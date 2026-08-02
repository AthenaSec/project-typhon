"""PyRIT PromptTarget that wraps target_agent's /chat endpoint."""

import uuid

import httpx
from pyrit.models import Message, construct_response_from_request
from pyrit.prompt_target import PromptTarget, TargetCapabilities, TargetConfiguration

DEFAULT_TIMEOUT = 60.0


class FastAPITarget(PromptTarget):
    """Wraps target_agent's append-only /chat endpoint.

    Keyed by PyRIT's own per-conversation id (Message.conversation_id) rather
    than a single id fixed at construction time, so one instance can safely be
    shared across many logical conversations — e.g. the many atomic attacks a
    PyRIT Scenario drives against a single objective_target — without their
    histories colliding on target_agent's server-side conversation store."""

    _DEFAULT_CONFIGURATION = TargetConfiguration(capabilities=TargetCapabilities(supports_multi_turn=True))

    def __init__(self, *, endpoint: str, timeout: float = DEFAULT_TIMEOUT) -> None:
        super().__init__(endpoint=endpoint)
        self._timeout = timeout
        self._conversation_ids: dict[str, str] = {}

    def _target_conversation_id(self, pyrit_conversation_id: str) -> str:
        return self._conversation_ids.setdefault(pyrit_conversation_id, str(uuid.uuid4()))

    async def _send_prompt_to_target_async(self, *, normalized_conversation: list[Message]) -> list[Message]:
        last_message = normalized_conversation[-1]
        request_piece = last_message.message_pieces[0]
        target_conversation_id = self._target_conversation_id(last_message.conversation_id)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._endpoint.rstrip('/')}/chat",
                json={"message": request_piece.converted_value, "conversation_id": target_conversation_id},
            )
        response.raise_for_status()
        return [
            construct_response_from_request(
                request=request_piece, response_text_pieces=[response.json()["response"]]
            )
        ]


class FastAPIEditableTarget(PromptTarget):
    """Stateless variant of FastAPITarget for strategies that need editable
    history (e.g. crescendo, which backtracks by rewriting prior turns).

    Sends the entire normalized_conversation on every call against
    target_agent's stateless /chat history mode, instead of relying on
    conversation_id continuity — so "editing" is just PyRIT sending a
    different history next call, the same pattern LLMClientChatTarget already
    uses for the adversarial/judge chat."""

    _DEFAULT_CONFIGURATION = TargetConfiguration(
        capabilities=TargetCapabilities(
            supports_multi_turn=True,
            supports_editable_history=True,
            supports_system_prompt=True,
        )
    )

    def __init__(self, *, endpoint: str, timeout: float = DEFAULT_TIMEOUT) -> None:
        super().__init__(endpoint=endpoint)
        self._timeout = timeout

    async def _send_prompt_to_target_async(self, *, normalized_conversation: list[Message]) -> list[Message]:
        request_piece = normalized_conversation[-1].message_pieces[0]
        history = [
            {"role": piece.role, "content": piece.converted_value}
            for piece in (message.message_pieces[0] for message in normalized_conversation[:-1])
            if piece.role != "system"
        ]
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._endpoint.rstrip('/')}/chat",
                json={"message": request_piece.converted_value, "history": history},
            )
        response.raise_for_status()
        return [
            construct_response_from_request(
                request=request_piece, response_text_pieces=[response.json()["response"]]
            )
        ]

"""PyRIT PromptTarget that wraps target_agent's /chat endpoint."""

import uuid

import httpx
from pyrit.models import Message, construct_response_from_request
from pyrit.prompt_target import PromptTarget, TargetCapabilities, TargetConfiguration

DEFAULT_TIMEOUT = 60.0


class FastAPITarget(PromptTarget):
    """One instance per attack: owns a fixed conversation_id so target_agent's
    server-side history accumulates across the multi-turn loop."""

    _DEFAULT_CONFIGURATION = TargetConfiguration(capabilities=TargetCapabilities(supports_multi_turn=True))

    def __init__(self, *, endpoint: str, timeout: float = DEFAULT_TIMEOUT) -> None:
        super().__init__(endpoint=endpoint)
        self._timeout = timeout
        self._conversation_id = str(uuid.uuid4())

    async def _send_prompt_to_target_async(self, *, normalized_conversation: list[Message]) -> list[Message]:
        request_piece = normalized_conversation[-1].message_pieces[0]
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._endpoint.rstrip('/')}/chat",
                json={"message": request_piece.converted_value, "conversation_id": self._conversation_id},
            )
        response.raise_for_status()
        return [
            construct_response_from_request(
                request=request_piece, response_text_pieces=[response.json()["response"]]
            )
        ]

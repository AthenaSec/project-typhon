"""PyRIT PromptTarget backed by the shared llm_client — used as both PyRIT's
adversarial (attacker) chat and the scorer's judge chat, so model/provider
config stays identical to judge.py and target_agent (same LLM_PROVIDER env)."""

from llm_client import complete, default_model, get_client
from pyrit.models import Message, construct_response_from_request
from pyrit.prompt_target import PromptTarget, TargetCapabilities, TargetConfiguration

# Shared by every PyRIT-side call: adversarial chat, objective scorer, and
# severity scorer. 512 was too tight — scorers on this project's default
# provider often write long chain-of-thought into "rationale" before closing
# the JSON object, so the response got cut off mid-string, failed JSON
# parsing, and burned retries (see pyrit.exceptions.exceptions_helpers
# "Retry attempt N for objective scorer" in the logs). Raised to give that
# rationale room to finish.
MAX_TOKENS = 2048


class LLMClientChatTarget(PromptTarget):
    _DEFAULT_CONFIGURATION = TargetConfiguration(
        capabilities=TargetCapabilities(
            supports_multi_turn=True,
            supports_editable_history=True,
            supports_system_prompt=True,
        )
    )

    def __init__(self, *, model: str | None = None) -> None:
        super().__init__()
        self._client = get_client()
        self._model = model or default_model()

    async def _send_prompt_to_target_async(self, *, normalized_conversation: list[Message]) -> list[Message]:
        system_prompt = ""
        history = []
        for message in normalized_conversation:
            piece = message.message_pieces[0]
            if piece.role == "system":
                system_prompt = piece.converted_value
            else:
                history.append({"role": piece.role, "content": piece.converted_value})

        request_piece = normalized_conversation[-1].message_pieces[0]
        text = complete(self._client, self._model, system_prompt, history, max_tokens=MAX_TOKENS)
        return [construct_response_from_request(request=request_piece, response_text_pieces=[text])]

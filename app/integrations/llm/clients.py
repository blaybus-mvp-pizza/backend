from typing import Protocol, Any, Dict


class LLMClient(Protocol):
    async def complete(self, prompt: str, **kwargs: Any) -> Dict[str, Any]: ...


# Later: implement OpenAI client and LangGraph runner here.

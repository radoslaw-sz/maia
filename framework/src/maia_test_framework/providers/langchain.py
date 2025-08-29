# maia_test_framework/providers/langchain.py
import time
import asyncio
from typing import Any, Dict, List, Callable, Optional
from maia_test_framework.core.message import AgentResponse, Message
from maia_test_framework.providers.base import BaseProvider

# Lazy import for langchain
try:
    from langchain.chains.base import Chain
except ImportError:
    Chain = None


class LangChainProvider(BaseProvider):
    """Provider for LangChain chains and agents."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if Chain is None:
            raise ImportError(
                "langchain is not installed. Please install it with `pip install langchain`"
            )

        self.chain = self.config.get("chain")
        if not isinstance(self.chain, Chain):
            raise ValueError("The 'chain' parameter must be an instance of a LangChain Chain.")

        # Hooks for customizing IO behavior
        self.input_mapper: Optional[Callable[[List[Message], str], Dict[str, Any]]] = self.config.get("input_mapper")
        self.output_parser: Optional[Callable[[Dict[str, Any]], str]] = self.config.get("output_parser")

    def get_provider_name(self) -> str:
        return f"LangChain-{self.chain.__class__.__name__}"

    async def generate(self, history: List[Message], system_message: str = "") -> AgentResponse:
        user_prompt = history[-1].content if history else ""

        if self.input_mapper:
            input_dict = self.input_mapper(history, system_message)
        else:
            input_dict = {"input": user_prompt, "system": system_message}

        start_time = time.perf_counter()

        try:
            # Run chain (async if available, else sync fallback)
            if hasattr(self.chain, "acall"):
                raw_response = await self.chain.acall(input_dict)
            elif hasattr(self.chain, "run"):
                # Run in thread to avoid blocking
                raw_response = await asyncio.to_thread(self.chain.run, input_dict)
            else:
                raise ValueError("Unsupported LangChain chain type: missing acall/run.")

            # Parse output
            if self.output_parser:
                content = self.output_parser(raw_response)
            else:
                if isinstance(raw_response, dict):
                    if "output" in raw_response:
                        content = raw_response["output"]
                    elif "text" in raw_response:
                        content = raw_response["text"]
                    else:
                        # Take the first str-like value
                        str_values = [str(v) for v in raw_response.values() if isinstance(v, (str, int, float))]
                        content = str_values[0] if str_values else str(raw_response)
                else:
                    content = str(raw_response)

            elapsed = time.perf_counter() - start_time

            return AgentResponse(
                content=content,
                metadata={
                    "agent_type": "langchain",
                    "chain_class": self.chain.__class__.__name__,
                    "elapsed_time": round(elapsed, 3),
                },
                raw_response=raw_response,
            )

        except Exception as e:
            return AgentResponse(
                content="",
                metadata={
                    "error": True,
                    "error_message": str(e),
                    "chain_class": self.chain.__class__.__name__,
                },
            )

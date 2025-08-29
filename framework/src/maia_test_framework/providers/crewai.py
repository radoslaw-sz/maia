# maia_test_framework/providers/crewai.py
import time
import asyncio
from typing import Any, Dict, List, Optional, Callable
from maia_test_framework.core.message import AgentResponse, Message
from maia_test_framework.providers.base import BaseProvider

# Lazy import for CrewAI
try:
    from crewai import Crew
except ImportError:
    Crew = None


class CrewAIProvider(BaseProvider):
    """Provider for CrewAI crews and agents."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if Crew is None:
            raise ImportError(
                "CrewAI is not installed. Please install it with `pip install crewai`"
            )

        self.crew = self.config.get("crew")
        if not isinstance(self.crew, Crew):
            raise ValueError("The 'crew' parameter must be an instance of a CrewAI Crew.")

        # Hooks for customization
        self.input_mapper: Optional[Callable[[List[Message], str], Dict[str, Any]]] = self.config.get("input_mapper")
        self.output_parser: Optional[Callable[[Any], str]] = self.config.get("output_parser")

    def get_provider_name(self) -> str:
        return f"CrewAI-{self.crew.__class__.__name__}"

    async def generate(self, history: List[Message], system_message: str = "") -> AgentResponse:
        user_prompt = history[-1].content if history else ""

        if self.input_mapper:
            input_dict = self.input_mapper(history, system_message)
        else:
            input_dict = {"input": user_prompt, "system": system_message}

        start_time = time.perf_counter()

        try:
            # CrewAI currently does not have async run, so wrap in thread
            raw_response = await asyncio.to_thread(self.crew.kickoff, input_dict)

            if self.output_parser:
                content = self.output_parser(raw_response)
            else:
                # Default: try stringifying
                content = str(raw_response)

            elapsed = time.perf_counter() - start_time

            return AgentResponse(
                content=content,
                metadata={
                    "agent_type": "crewai",
                    "crew_class": self.crew.__class__.__name__,
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
                    "crew_class": self.crew.__class__.__name__,
                },
            )

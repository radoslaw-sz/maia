from typing import List
from maia_test_framework.core.agent import Agent
from maia_test_framework.core.message import Message, AgentResponse
from maia_test_framework.providers.base import BaseProvider


class OrchestrationAgent(Agent):
    def __init__(self, provider: BaseProvider, name: str = "Orchestrator"):
        super().__init__(name, provider)

    def _build_system_message(self, agents: List[Agent]) -> str:
        agent_descriptions = []
        for agent in agents:
            if agent.name != self.name:
                agent_descriptions.append(f"- {agent.name}: {agent.system_message}")

        return f"""You are an orchestration agent. Your role is to decide which agent should handle the user's request.
You have the following agents available:
{chr(10).join(agent_descriptions)}

Based on the last user's message, you must respond with ONLY the name of the agent that should handle the request.
If no agent is suitable, you should respond with "None".
"""

    async def generate_response(self, history: List[Message], agents: List[Agent] = None) -> AgentResponse:
        if not agents:
            agents = []
            
        self.system_message = self._build_system_message(agents)
        last_message = history[-1] if history else ""
        return await self.provider.base_generate(
            history=[last_message],
            system_message=self.system_message,
        )
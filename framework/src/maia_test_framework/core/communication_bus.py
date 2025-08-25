from typing import Dict, List
from maia_test_framework.core.message import Message
from maia_test_framework.core.agent import Agent

class CommunicationBus:
    """Handles low-level message exchange and history"""
    
    def __init__(self):
        self.message_history: List[Message] = []
        self.agents: Dict[str, Agent] = {}
    
    def register_agent(self, agent: Agent):
        """Register an agent with the bus"""
        if agent.name in self.agents:
            raise ValueError(f"Agent with name '{agent.name}' is already registered.")
        self.agents[agent.name] = agent
    
    def get_agent(self, agent_name: str) -> Agent:
        """Get a registered agent by name"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found")
        return self.agents[agent_name]

    def add_message(self, message: Message):
        """Add a message to the history"""
        self.message_history.append(message)
    
    def get_history(self) -> List[Message]:
        """Get the full message history"""
        return self.message_history

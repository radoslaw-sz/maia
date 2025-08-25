import uuid
from typing import Callable, List, Optional, Tuple
from maia_test_framework.core.communication_bus import CommunicationBus
from maia_test_framework.core.message import Message, AgentResponse, IGNORE_MESSAGE
from maia_test_framework.core.agent import Agent
from maia_test_framework.core.exceptions import MaiaAssertionError

class Session:
    """High-level abstraction for a conversation session."""
    
    def __init__(self, bus: CommunicationBus, assertions: List[Callable[[Message], None]] = None, session_id: str = None):
        self.id = session_id or str(uuid.uuid4())
        self.bus = bus
        self.assertions = assertions or []
    
    def add_participant(self, agent: Agent):
        """Add a participant (agent) to the session."""
        self.bus.register_agent(agent)
        
    async def user_says(self, message: str) -> "Session":
        """Add user message to the conversation."""
        msg = Message(content=message, sender="user", sender_type="user")
        self.bus.add_message(msg)
        return self
    
    async def agent_responds(self, agent_name: str) -> Optional[AgentResponse]:
        """Have a specified agent respond to the conversation."""

        agent = self.bus.get_agent(agent_name)

        history = self.bus.get_history()

        response = await agent.generate_response(history)

        if response.content.strip() == IGNORE_MESSAGE:
            return None

        response_msg = Message(
            content=response.content,
            sender=agent_name,
            sender_type="agent",
            metadata=response.metadata
        )
        self.bus.add_message(response_msg)

        try:
            for assertion in self.assertions:
                assertion(response_msg)
        except MaiaAssertionError:
            # Assertion failed, was recorded, and raised. Stop processing and re-raise.
            raise
        
        return response

    async def user_says_and_broadcast(self, message: str) -> Tuple[Optional[AgentResponse], Optional[str]]:
        """Broadcast a user message to all agents and get the first response."""
        msg = Message(content=message, sender="user", sender_type="user")
        self.bus.add_message(msg)
        history = self.bus.get_history()

        for agent_name, agent in self.bus.agents.items():
            response = await agent.generate_response(history)
            if response.content.strip() != IGNORE_MESSAGE:
                response_msg = Message(
                    content=response.content,
                    sender=agent_name,
                    sender_type="agent",
                    metadata=response.metadata
                )
                self.bus.add_message(response_msg)
                return response, agent_name
        
        return None, None

    async def agent_says(self, from_agent: str, to_agent: str, message: str) -> "Session":
        """Send a message from one agent to another."""
        msg = Message(content=message, sender=from_agent, sender_type="agent", receiver=to_agent, receiver_type="agent")
        self.bus.add_message(msg)
        return self

    @property
    def message_history(self) -> List[Message]:
        return self.bus.get_history()

    def get_conversation_text(self) -> str:
        """Get full conversation as text"""
        lines = []
        for msg in self.message_history:
            lines.append(f"{msg.sender}: {msg.content}")
        return "\n".join(lines)

    async def run_agent_conversation(self, initiator: str, responder: str, initial_message: str, max_turns: int) -> List[Message]:
        """Run a multi-turn conversation between two agents."""
        conversation_log = []
        
        # Initial message
        msg = Message(content=initial_message, sender=initiator, sender_type="agent", metadata={"to_agent": responder})
        self.bus.add_message(msg)
        conversation_log.append(msg)

        for _ in range(max_turns):
            # Responder responds to initiator
            response_to_initiator = await self.agent_responds(responder)
            if response_to_initiator:
                msg = Message(content=response_to_initiator.content, sender=responder, sender_type="agent", metadata={"to_agent": initiator})
                conversation_log.append(msg)
            else:
                break

            # Initiator responds to responder
            response_to_responder = await self.agent_responds(initiator)
            if response_to_responder:
                msg = Message(content=response_to_responder.content, sender=initiator, sender_type="agent", metadata={"to_agent": responder})
                conversation_log.append(msg)
            else:
                break
        
        return conversation_log
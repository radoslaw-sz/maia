import uuid
from typing import Callable, List, Optional, Tuple
from maia_test_framework.core.communication_bus import CommunicationBus
from maia_test_framework.core.message import Message, AgentResponse, IGNORE_MESSAGE
from maia_test_framework.core.agent import Agent
from maia_test_framework.core.orchestration_agent import OrchestrationAgent
from maia_test_framework.core.exceptions import MaiaAssertionError
from maia_test_framework.core.judge_agent import JudgeAgent
from maia_test_framework.core.types.judge_result import JudgeResult
from maia_test_framework.core.types.orchestration_policy import OrchestrationPolicy

class Session:
    """High-level abstraction for a conversation session."""
    
    def __init__(self, bus: CommunicationBus, assertions: List[Callable[[Message], None]] = None, session_id: str = None, orchestration_agent: OrchestrationAgent = None, orchestration_policy: OrchestrationPolicy = None, validators: List[Callable[['Session'], None]] = None, judge_agent: JudgeAgent = None):
        self.id = session_id or str(uuid.uuid4())
        self.bus = bus
        self.assertions = assertions or []
        self.orchestration_agent = orchestration_agent
        self.orchestration_policy = orchestration_policy
        self.validators = validators or []
        self.assertion_results = []
        self.validator_results = []
        self.judge_agent = judge_agent
        self.judge_result = None
    
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

        if IGNORE_MESSAGE in response.content.strip():
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

        if self.orchestration_policy == OrchestrationPolicy.ORCHESTRATION_AGENT and self.orchestration_agent:
            agents = list(self.bus.agents.values())
            response = await self.orchestration_agent.generate_response(history, agents)

            agent_name = response.content.strip()
            
            if agent_name in self.bus.agents:
                agent_response = await self.agent_responds(agent_name)
                return agent_response, agent_name
            else:
                return None, None
        
        for agent_name, agent in self.bus.agents.items():
            if self.orchestration_agent and agent_name == self.orchestration_agent.name:
                continue

            response = await agent.generate_response(history)
            if self.orchestration_policy == OrchestrationPolicy.IGNORE_MESSAGE and IGNORE_MESSAGE in response.content.strip() :
                continue
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

    async def judge(self) -> JudgeResult:
        """
        Evaluates the session using the attached JudgeAgent and returns the result.
        """
        if not self.judge_agent:
            raise ValueError("No JudgeAgent has been attached to this session.")
        
        result = await self.judge_agent.judge_session(self)
        self.judge_result = result
        return result

    async def judge_and_assert(self):
        """
        Evaluates the session using the attached JudgeAgent and asserts the outcome.
        """
        if not self.judge_agent:
            raise ValueError("No JudgeAgent has been attached to this session.")
        
        await self.judge_agent.judge_and_assert(self)
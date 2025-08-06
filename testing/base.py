from abc import ABC
from typing import Callable, Dict, List

from maia_test_framework.core.agent import Agent
from maia_test_framework.core.message import Message
from maia_test_framework.core.session import Session
from maia_test_framework.core.communication_bus import CommunicationBus
from maia_test_framework.core.tools.base import BaseTool
from maia_test_framework.testing.mixin.provider_mixin import ProviderMixin
from maia_test_framework.testing.validators.base import BaseValidator

class MaiaTest(ABC, ProviderMixin):
    """Base class for multi-agent tests"""

    def setup_method(self):
        """Setup run before each test method"""
        self.agents: Dict[str, Agent] = {}
        self.sessions: List[Session] = []
        self.validators: List[BaseValidator] = []
        self.tools: Dict[str, BaseTool] = {}
        self.setup_tools()
        self.setup_agents()
        self.setup_session()

    def teardown_method(self):
        """Cleanup after each test method"""
        for session in self.sessions:
            for validator_class in self.validators:
                validator = validator_class(session)
                validator.validate()
        self.sessions.clear()

    def setup_agents(self):
        """Override this method to define agents for test suite"""
        pass

    def setup_tools(self):
        """Override this method to define tools for test suite"""
        pass

    def setup_session(self):
        """Override this method to define a common session for test suite"""
        pass

    def create_agent(self, name, provider, system_message="", ignore_trigger_prompt="", tools: List[str] = None):
        agent_tools = [self.tools[tool_name] for tool_name in tools] if tools else []
        agent = Agent(name, provider, system_message, ignore_trigger_prompt, tools=agent_tools)
        self.agents[name] = agent
        return agent

    def create_tool(self, name: str, tool_class: BaseTool, *args, **kwargs) -> BaseTool:
        tool = tool_class(name=name, *args, **kwargs)
        self.tools[name] = tool
        return tool

    def get_tool(self, name: str) -> BaseTool:
        """Get a tool by its name."""
        if name not in self.tools:
            raise ValueError(f"Tool with name '{name}' not found.")
        return self.tools[name]

    def create_session(self, agent_names: List[str] = None, assertions: List[Callable[[Message], None]] = None, session_id: str = None) -> Session:
        """Create a new session with specified agents"""
        bus = CommunicationBus()
        session = Session(bus, assertions, session_id)

        agents_to_add = []
        if agent_names:
            for name in agent_names:
                if name not in self.agents:
                    raise ValueError(f"Agent '{name}' not configured")
                agents_to_add.append(self.agents[name])
        else:
            agents_to_add = list(self.agents.values())

        for agent in agents_to_add:
            session.add_participant(agent)

        self.sessions.append(session)
        return session

    def get_session(self, session_id: str) -> Session:
        """Get a session by its ID."""
        for session in self.sessions:
            if session.id == session_id:
                return session
        raise ValueError(f"Session with ID '{session_id}' not found.")

    def extend_session(self, session_id: str, agent_names: List[str] = None, assertions: List[Callable[[Message], None]] = None) -> Session:
        """Extends an existing session with more agents and assertions."""
        session = self.get_session(session_id)
        if assertions:
            session.assertions.extend(assertions)

        if agent_names:
            for name in agent_names:
                if name not in self.agents:
                    raise ValueError(f"Agent '{name}' not configured")
                if name not in session.bus.agents:
                    session.add_participant(self.agents[name])
        
        return session

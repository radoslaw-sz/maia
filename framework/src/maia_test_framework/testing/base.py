from abc import ABC
from datetime import datetime
import json
import os
from typing import Callable, Dict, List, Literal, Any
from dataclasses import dataclass, asdict, field

import traceback

from maia_test_framework.core.agent import Agent
from maia_test_framework.core.message import Message
from maia_test_framework.core.session import Session
from maia_test_framework.core.communication_bus import CommunicationBus
from maia_test_framework.core.tools.base import BaseTool
from maia_test_framework.core.types.judge_result import JudgeResult
from maia_test_framework.testing.mixin.provider_mixin import ProviderMixin
from maia_test_framework.testing.assertions.base import MaiaAssertion
from maia_test_framework.core.exceptions import MaiaAssertionError
from maia_test_framework.core.judge_agent import JudgeAgent
from maia_test_framework.core.types.orchestration_policy import OrchestrationPolicy

@dataclass
class Participant:
    id: str
    name: str
    type: Literal["user", "agent", "tool"]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AssertionResult:
    id: str
    assertion_name: str
    description: str | None
    status: Literal["passed", "failed"]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidatorResult:
    name: str
    status: Literal["passed", "failed", "skipped"]
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TestResult:
    test_name: str
    start_time: str
    end_time: str
    status: Literal["passed", "failed"]
    participants: List[Participant]
    sessions: List[dict]

    def save(self, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        file_path = os.path.join(output_dir, f"{self.test_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)

class MaiaTest(ABC, ProviderMixin):

    def setup_method(self, method):
        """Setup run before each test method"""
        self.test_name = method.__name__
        self.start_time = datetime.now().isoformat()
        self.agents: Dict[str, Agent] = {}
        self.sessions: List[Session] = []
        self.tools: Dict[str, BaseTool] = {}
        self.setup_tools()
        self.setup_agents()
        self.setup_session()

    def teardown_method(self, method):
        """Cleanup after each test method - validators are now handled by pytest plugin"""
        self.sessions.clear()

    def _execute_and_record_assertion(self, assertion: MaiaAssertion, assertion_name: str, metadata: Dict[str, Any], session: Session):
        assertion_id = f"assert_{len(session.assertion_results) + 1}"
        try:
            final_description = None
            result_message = assertion.call()
            if result_message and isinstance(result_message, str):
                final_description = f"{result_message}"

            session.assertion_results.append(AssertionResult(
                id=assertion_id,
                assertion_name=assertion_name,
                description=final_description,
                status="passed",
                metadata=metadata
            ))
        except AssertionError as e:
            result = AssertionResult(
                id=assertion_id,
                assertion_name=assertion_name,
                description=str(e),
                status="failed",
                metadata=metadata
            )
            session.assertion_results.append(result)
            raise MaiaAssertionError(str(e), result=result) from e

    def run_assertion(self, assertion: MaiaAssertion, session: Session):
        """Runs a test-level assertion that is not bound to a specific message."""
        assertion_name = assertion.get_name() or "Unnamed Assertion"
        self._execute_and_record_assertion(assertion, assertion_name, metadata={}, session=session)

    def _run_message_assertion(self, assertion: MaiaAssertion, message: Message):
        """Runs a session-level assertion against a specific message."""
        assertion_name = assertion.get_name() or "Unnamed Assertion"
        metadata = {"message": message.to_dict()}
        if not hasattr(message, 'session_id') or not message.session_id:
            raise ValueError("Message is not associated with a session, cannot record assertion.")
        session = self.get_session(message.session_id)
        self._execute_and_record_assertion(assertion, assertion_name, metadata, session=session)

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

    def _create_assertion_wrapper(self, original_assertion_factory):
        def wrapper(response_msg):
            assertion_object = original_assertion_factory(response_msg)
            self._run_message_assertion(assertion_object, message=response_msg)
        return wrapper

    def create_session(self, agent_names: List[str] = None, assertions: List[Callable[[Message], None]] = None, session_id: str = None, orchestration_agent: Agent = None, orchestration_policy: OrchestrationPolicy = None, validators: List[Callable[[Session], None]] = None, judge_agent: JudgeAgent = None) -> Session:
        """Create a new session with specified agents"""
        bus = CommunicationBus()

        wrapped_assertions = []
        if assertions:
            for original_assertion in assertions:
                wrapped_assertions.append(self._create_assertion_wrapper(original_assertion))

        session = Session(bus, wrapped_assertions, session_id, orchestration_agent, orchestration_policy, validators, judge_agent=judge_agent)

        session.assertion_results = []
        session.validator_results = []

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

        if orchestration_agent:
            session.add_participant(orchestration_agent)

        self.sessions.append(session)
        return session

    def run_validator(self, validator: Callable[[Session], None], session: Session):
        """Manually runs a validator and records its result."""
        validator_name = validator.__name__
        try:
            validator(session)
            session.validator_results.append(ValidatorResult(
                name=validator_name,
                status="passed"
            ))
        except AssertionError as e:
            failure_details = {"error": str(e), "traceback": traceback.format_exc()}
            session.validator_results.append(ValidatorResult(
                name=validator_name,
                status="failed",
                details=failure_details
            ))
            raise  # Re-raise to allow pytest.raises to catch it

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
            for original_assertion in assertions:
                session.assertions.append(self._create_assertion_wrapper(original_assertion))

        if agent_names:
            for name in agent_names:
                if name not in self.agents:
                    raise ValueError(f"Agent '{name}' not configured")
                if name not in session.bus.agents:
                    session.add_participant(self.agents[name])
        return session
from abc import ABC
from datetime import datetime
import json
import os
import functools
from typing import Callable, Dict, List, Literal, Any
from dataclasses import dataclass, asdict, field
import traceback

from maia_test_framework.core.agent import Agent
from maia_test_framework.core.message import Message
from maia_test_framework.core.session import Session
from maia_test_framework.core.communication_bus import CommunicationBus
from maia_test_framework.core.tools.base import BaseTool
from maia_test_framework.testing.mixin.provider_mixin import ProviderMixin
from maia_test_framework.testing.validators.base import BaseValidator
from maia_test_framework.core.exceptions import MaiaAssertionError

@dataclass
class Participant:
    id: str
    name: str
    type: Literal["user", "agent", "tool"]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AssertionResult:
    id: str
    description: str
    status: Literal["passed", "failed"]
    details: str = ""

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
    assertions: List[AssertionResult]
    validators: List[ValidatorResult]

    def save(self, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        file_path = os.path.join(output_dir, f"{self.test_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)

class MaiaTest(ABC, ProviderMixin):
    """Base class for multi-agent tests"""
    _run_output_dir = None

    def setup_method(self, method):
        """Setup run before each test method"""
        if MaiaTest._run_output_dir is None:
            base_output_dir = os.getenv("MAIA_TEST_OUTPUT_DIR", "test_reports")
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            MaiaTest._run_output_dir = os.path.join(base_output_dir, timestamp)

        self.test_name = method.__name__
        self.start_time = datetime.now().isoformat()
        self.agents: Dict[str, Agent] = {}
        self.sessions: List[Session] = []
        self.validators: List[BaseValidator] = []
        self.tools: Dict[str, BaseTool] = {}
        self.assertion_results: List[AssertionResult] = []
        self.validator_results: List[ValidatorResult] = []
        self.setup_tools()
        self.setup_agents()
        self.setup_session()


    def teardown_method(self, method):
        """Cleanup after each test method"""
        
        # Determine final test status from pytest reports
        final_pytest_status = "passed"
        if (hasattr(self, 'rep_setup') and self.rep_setup.failed) or \
           (hasattr(self, 'rep_call') and self.rep_call.failed) or \
           (hasattr(self, 'rep_teardown') and self.rep_teardown.failed):
            final_pytest_status = "failed"

        # Run Validators only if the test call didn't already fail unexpectedly
        if not (hasattr(self, 'rep_call') and self.rep_call.failed):
            for validator_class in self.validators:
                validator = validator_class(self.sessions[0]) # Assuming one session for now
                try:
                    validator.validate()
                    self.validator_results.append(ValidatorResult(
                        name=validator.__class__.__name__,
                        status="passed"
                    ))
                except Exception as e:
                    self.validator_results.append(ValidatorResult(
                        name=validator.__class__.__name__,
                        status="failed",
                        details={"error": str(e), "traceback": traceback.format_exc()}
                    ))

        # Collect Participants
        participants = []
        participants.append(Participant(id="user", name="User", type="user"))
        for name, agent in self.agents.items():
            participants.append(Participant(id=name, name=name, type="agent", metadata={"model": agent.provider.__class__.__name__}))
        for name, tool in self.tools.items():
            participants.append(Participant(id=name, name=name, type="tool"))
        
        # Collect Session Data
        session_data = []
        for s in self.sessions:
            history = [msg._to_dict() for msg in s.message_history]
            session_data.append({
                "id": s.id,
                "participants": [p.id for p in participants],
                "messages": history,
            })
        
        result = TestResult(
            test_name=self.test_name,
            start_time=self.start_time,
            end_time=datetime.now().isoformat(),
            status=final_pytest_status, # Use the status from pytest
            participants=participants,
            sessions=session_data,
            assertions=self.assertion_results,
            validators=self.validator_results
        )
        result.save(output_dir=MaiaTest._run_output_dir)

        self.sessions.clear()

    def run_assertion(self, assertion_callable: Callable, description: str):
        assertion_id = f"assert_{len(self.assertion_results) + 1}"
        try:
            assertion_callable()
            self.assertion_results.append(AssertionResult(
                id=assertion_id,
                description=description,
                status="passed"
            ))
        except AssertionError as e:
            result = AssertionResult(
                id=assertion_id,
                description=description,
                status="failed",
                details=str(e)
            )
            self.assertion_results.append(result)
            raise MaiaAssertionError(str(e), result=result)

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

    def _create_assertion_wrapper(self, original_assertion):
        def wrapper(response_msg):
            func = original_assertion
            description = ""
            if isinstance(func, functools.partial):
                description = func.func.__name__
            else:
                description = func.__name__
            self.run_assertion(lambda: original_assertion(response_msg), description=description)
        return wrapper

    def create_session(self, agent_names: List[str] = None, assertions: List[Callable[[Message], None]] = None, session_id: str = None) -> Session:
        """Create a new session with specified agents"""
        bus = CommunicationBus()

        wrapped_assertions = []
        if assertions:
            for original_assertion in assertions:
                wrapped_assertions.append(self._create_assertion_wrapper(original_assertion))

        session = Session(bus, wrapped_assertions, session_id)

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

    def run_validator(self, validator_instance: BaseValidator):
        """Manually runs a validator and records its result."""
        validator_name = validator_instance.__class__.__name__
        try:
            validator_instance.validate()
            self.validator_results.append(ValidatorResult(
                name=validator_name,
                status="passed"
            ))
        except AssertionError as e:
            self.validator_results.append(ValidatorResult(
                name=validator_name,
                status="failed",
                details={"error": str(e)}
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
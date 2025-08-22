import pytest
import asyncio
from framework.testing.base import MaiaTest
from framework.providers.existing import ExistingAgentProvider

# Mock agent implementations for testing

class SimpleEchoAgent:
    """A simple agent with a synchronous 'run' method."""
    def run(self, prompt: str) -> str:
        return f"Echo: {prompt}"

class AsyncEchoAgent:
    """An agent with an asynchronous 'run' method."""
    async def run(self, prompt: str) -> str:
        await asyncio.sleep(0.01)  # Simulate async work
        return f"Async Echo: {prompt}"

class CallableAgent:
    """An agent that is directly callable."""
    def __call__(self, prompt: str) -> str:
        return f"Callable: {prompt}"

class ComplexResponseAgent:
    """An agent with a custom query method and a complex response format."""
    def query(self, prompt: str) -> dict:
        return {"response": f"Complex: {prompt}", "data": [1, 2, 3]}

class TestExistingAgentProvider(MaiaTest):
    """Test suite for the ExistingAgentProvider."""

    def setup_agents(self):
        """Set up various agents to test different provider configurations."""
        
        # Agent with a standard synchronous 'run' method
        self.create_agent(
            name="EchoAgent",
            provider=ExistingAgentProvider(config={
                "agent_instance": SimpleEchoAgent()
            })
        )

        # Agent with an asynchronous 'run' method
        self.create_agent(
            name="AsyncAgent",
            provider=ExistingAgentProvider(config={
                "agent_instance": AsyncEchoAgent()
            })
        )

        # Agent that is a callable instance
        self.create_agent(
            name="CallableAgent",
            provider=ExistingAgentProvider(config={
                "agent_instance": CallableAgent()
            })
        )

        # Agent with a custom method name and a response extractor
        self.create_agent(
            name="ComplexAgent",
            provider=ExistingAgentProvider(config={
                "agent_instance": ComplexResponseAgent(),
                "call_method": "query",
                "response_extractor": lambda r: r["response"]
            })
        )

    @pytest.mark.asyncio
    async def test_simple_agent_conversation(self):
        """Test conversation with a simple synchronous agent."""
        session = self.create_session(["EchoAgent"])
        await session.user_says("Hello")
        response = await session.agent_responds("EchoAgent")
        assert response.content == "Echo: Hello"
        assert response.metadata.get("agent_type") == "existing"

    @pytest.mark.asyncio
    async def test_async_agent_conversation(self):
        """Test conversation with an agent using an async method."""
        session = self.create_session(["AsyncAgent"])
        await session.user_says("World")
        response = await session.agent_responds("AsyncAgent")
        assert response.content == "Async Echo: World"

    @pytest.mark.asyncio
    async def test_callable_agent_conversation(self):
        """Test conversation with a callable agent instance."""
        session = self.create_session(["CallableAgent"])
        await session.user_says("Test")
        response = await session.agent_responds("CallableAgent")
        assert response.content == "Callable: Test"

    @pytest.mark.asyncio
    async def test_complex_agent_conversation(self):
        """Test agent with custom call method and response extractor."""
        session = self.create_session(["ComplexAgent"])
        await session.user_says("Data")
        response = await session.agent_responds("ComplexAgent")
        assert response.content == "Complex: Data"
        assert response.raw_response == {"response": "Complex: Data", "data": [1, 2, 3]}

    @pytest.mark.asyncio
    async def test_agent_error_handling(self):
        """Test error handling when the agent's method raises an exception."""
        class ErrorAgent:
            def run(self, prompt: str):
                raise ValueError("Something went wrong")

        self.create_agent(
            name="ErrorAgent",
            provider=ExistingAgentProvider(config={"agent_instance": ErrorAgent()})
        )
        
        session = self.create_session(["ErrorAgent"])
        await session.user_says("Trigger error")
        response = await session.agent_responds("ErrorAgent")
        
        assert response.content == ""
        assert response.metadata.get("error") is True
        assert "Something went wrong" in response.metadata.get("error_message", "")
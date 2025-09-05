import pytest
from maia_test_framework.core.orchestration_agent import OrchestrationAgent
from maia_test_framework.providers.generic_lite_llm import GenericLiteLLMProvider
from maia_test_framework.providers.ollama import OllamaProvider
from maia_test_framework.testing.assertions.content_patterns import assert_professional_tone
from maia_test_framework.testing.assertions.agents_participation import assert_agent_participated
from maia_test_framework.testing.base import MaiaTest
from maia_test_framework.testing.validators.conversation import conversation_validator
from maia_test_framework.testing.validators.agent import agent_message_count_validator, agent_not_participating_validator
from maia_test_framework.testing.validators.performance import performance_validator

class TestConversationSessions(MaiaTest):
    def setup_agents(self):
        self.create_agent(
            name="Alice",
            provider=self.get_provider("ollama"),
            system_message="You are a weather assistant. Only describe the weather.",
        )

        self.create_agent(
            name="Bob",
            provider=GenericLiteLLMProvider(config={
                "model": "ollama/mistral",
                "api_base": "http://localhost:11434"
            }),
            system_message="You are a pirate assistant who only suggests clothing.",
        )

    @pytest.mark.asyncio
    async def test_agent_conversation_fails_on_etiquette(self):
        session = self.create_session(["Alice", "Bob"])
        
        await session.agent_says("Alice", "Bob", "What's the weather?")
        await session.agent_responds("Alice")

        with pytest.raises(AssertionError, match=r"Agent Alice sent two messages in a row."):
            # We can call it manually for testing
            self.run_validator(conversation_validator(), session)

    @pytest.mark.asyncio
    async def test_assert_agent_not_participating(self):
        session = self.create_session(["Alice", "Bob"])

        await session.agent_says("Alice", "Bob", "What shall I wear if it is sunny?")
        await session.agent_responds("Bob")
        
        with pytest.raises(AssertionError, match=r"Agent Bob participated in the conversation when they should not have."):
            # We can call it manually for testing
            self.run_validator(agent_not_participating_validator(agent_name="Bob"), session)

    @pytest.mark.asyncio
    async def test_assert_latency_below(self):
        session = self.create_session(
            ["Alice"],
            validators=[performance_validator(threshold=60, unit="seconds")]
        )
        
        await session.user_says("What is the weather like today?")
        await session.agent_responds("Alice")

    @pytest.mark.asyncio
    async def test_assert_agent_message_count_below(self):
        session = self.create_session(["Alice", "Bob"])
        
        await session.user_says_and_broadcast("What is the weather like today?")
        await session.user_says_and_broadcast("What should I wear?")
        
        with pytest.raises(AssertionError, match=r"Agent Alice sent 2 messages, which is not below the threshold of 2."):
            # We can call it manually for testing
            self.run_validator(agent_message_count_validator(agent_name="Alice", max_messages=2), session)

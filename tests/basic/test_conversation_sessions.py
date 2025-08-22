import pytest
from framework.providers.generic_lite_llm import GenericLiteLLMProvider
from framework.providers.ollama import OllamaProvider
from framework.testing.assertions.content_patterns import assert_professional_tone
from framework.testing.assertions.agents_participation import assert_agent_participated
from framework.testing.base import MaiaTest
from framework.testing.validators.conversation import ConversationValidator

class TestConversationSessions(MaiaTest):
    def setup_agents(self):
        self.create_agent(
            name="Alice",
            provider=self.get_provider("ollama"),
            system_message="You are a weather assistant. Only describe the weather.",
            ignore_trigger_prompt="You MUST NOT answer questions about any other topic, including what to wear. If the user asks about anything other than the weather, you MUST respond with only the exact text: IGNORE_MESSAGE",
        )

        self.create_agent(
            name="Bob",
            provider=GenericLiteLLMProvider(config={
                "model": "ollama/mistral",
                "api_base": "http://localhost:11434"
            }),
            system_message="You are a pirate assistant who only suggests clothing.",
            ignore_trigger_prompt="If the question is not about what to wear, you MUST respond with only the exact text: IGNORE_MESSAGE"
        )

    @pytest.mark.asyncio
    async def test_conversation_broadcast(self):
        session = self.create_session(["Alice", "Bob"])

        # Test that only Alice responds to a weather question
        response_a, responder_a = await session.user_says_and_broadcast("Please describe the usual weather in London in July, including temperature and conditions.")
        
        print(f"{responder_a}: {response_a.content}")
        assert responder_a == 'Alice'
        assert_agent_participated(session, 'Alice')

        # Test that only Bob responds to a clothing question
        response_b, responder_b = await session.user_says_and_broadcast(f"Given the weather: {response_a.content}, what clothes should I wear?")
        
        print(f"{responder_b}: {response_b.content}")
        assert responder_b == 'Bob'
        assert_agent_participated(session, 'Bob')

        # Test that no one responds to an irrelevant question
        response_c, responder_c = await session.user_says_and_broadcast("What is the capital of France?")
        assert response_c is None
        assert responder_c is None

    @pytest.mark.asyncio
    async def test_conversation_direct_message(self):
        self.create_agent(
            name="Alice",
            provider=GenericLiteLLMProvider(config={
                "model": "ollama/mistral",
                "api_base": "http://localhost:11434"
            }),
            system_message="You are a weather assistant."
        )
        self.create_agent(
            name="Bob",
            provider=OllamaProvider(config={
                "model": "mistral"
            }),
            system_message="You are a assistant who only suggests clothing."
        )

        session = self.create_session(
            ["Alice", "Bob"],
            assertions=[assert_professional_tone],
        )

        await session.user_says("Please describe the usual weather in London in July, including temperature and conditions.")
        await session.agent_responds('Alice')
        assert_agent_participated(session, 'Alice')
        await session.agent_responds('Bob')
        assert_agent_participated(session, 'Bob')

    @pytest.mark.asyncio
    async def test_agent_to_agent_conversation(self):
        session = self.create_session(["Alice", "Bob"])
        
        # Alice initiates conversation with Bob
        await session.agent_says("Alice", "Bob", "Given the weather: rainy and 20 degress celsius, what clothes should I wear?")
        response = await session.agent_responds("Bob")
        assert_agent_participated(session, "Bob")
        
        # Bob responds back to Alice
        await session.agent_says("Bob", "Alice", f"Based on my info: {response.content}")
        response = await session.agent_responds("Alice")
        assert_agent_participated(session, "Alice")

    @pytest.mark.asyncio
    async def test_multi_turn_agent_conversation(self):
        self.create_agent(
            name="Alice",
            provider=self.get_provider("ollama"),
            system_message="You are a weather assistant."
        )
        self.create_agent(
            name="Bob",
            provider=self.get_provider("ollama"),
            system_message="You are a pirate who want to know the different details of the weather."
        )
    
        session = self.create_session(["Alice", "Bob"])
        
        conversation_log = await session.run_agent_conversation(
            initiator="Bob",
            responder="Alice", 
            initial_message="What's the weather?",
            max_turns=3
        )
        
        assert len(conversation_log) == 7  # 3 turns each + initial message

    @pytest.mark.asyncio
    async def test_agent_conversation_fails_on_etiquette(self):
        session = self.create_session(["Alice", "Bob"])
        
        await session.agent_says("Alice", "Bob", "What's the weather?")
        await session.agent_responds("Alice")

        with pytest.raises(AssertionError, match=r"Agent Alice sent two messages in a row."):
            # This will be called in teardown, but we can call it manually for testing
            self.run_validator(ConversationValidator(session))
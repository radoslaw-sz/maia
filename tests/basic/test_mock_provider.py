import pytest
from framework.testing.base import MaiaTest
from framework.providers.mock import MockProvider

class TestMockProvider(MaiaTest):
    def setup_agents(self):
        self.create_agent(
            name="Alice",
            provider=MockProvider(config={
                "responses": [
                    "Hello, I am a mock agent.",
                    "I am doing well, thank you for asking."
                ]
            })
        )

        def echo_bot(user_prompt):
            return f"You said: {user_prompt}"

        self.create_agent(
            name="Bob",
            provider=MockProvider(config={
                "response_function": echo_bot
            })
        )

    @pytest.mark.asyncio
    async def test_mock_conversation(self):
        session = self.create_session(["Alice"])
        
        await session.user_says("Hello, how are you?")
        response1 = await session.agent_responds("Alice")
        assert response1.content == "Hello, I am a mock agent."

        await session.user_says("That's good to hear.")
        response2 = await session.agent_responds("Alice")
        assert response2.content == "I am doing well, thank you for asking."

        # Test that the provider returns an empty string when it runs out of responses
        await session.user_says("Anything else?")
        response3 = await session.agent_responds("Alice")
        assert response3.content == ""

    @pytest.mark.asyncio
    async def test_mock_function_conversation(self):
        session = self.create_session(["Bob"])

        await session.user_says("Hello, Bob!")
        response1 = await session.agent_responds("Bob")
        assert response1.content == "You said: Hello, Bob!"

        await session.user_says("How are you today?")
        response2 = await session.agent_responds("Bob")
        assert response2.content == "You said: How are you today?"

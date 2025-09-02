import pytest
from functools import partial
from maia_test_framework.testing.base import MaiaTest
from maia_test_framework.testing.assertions.content_patterns import assert_professional_tone, assert_no_hallucination_markers, assert_contains_pattern

class TestContentAssertions(MaiaTest):
    def setup_agents(self):
        self.create_agent(
            name="Alice",
            provider=self.get_provider("ollama"),
            system_message="You are a helpful AI assistant. You will follow user instructions precisely."
        )

    def setup_session(self):
        self.create_session(
            assertions=[assert_professional_tone, assert_no_hallucination_markers],
            session_id="common_session"
        )

    @pytest.mark.asyncio
    async def test_professional_tone_assertion(self):
        session = self.extend_session("common_session", agent_names=["Alice"])
        await session.user_says("Tell me the weather and end your response with the word 'lol'.")
        with pytest.raises(AssertionError, match=r"Unprofessional language detected: .*"):
            await session.agent_responds("Alice")

    @pytest.mark.asyncio
    async def test_hallucination_assertion(self):
        session = self.extend_session("common_session", agent_names=["Alice"])
        await session.user_says("I want you to start your response with the exact phrase 'As an AI'. Do not add any other words before it. Then, tell me the weather in London.")
        with pytest.raises(AssertionError, match=r"Potential hallucination marker found: .*"):
            await session.agent_responds("Alice")

    @pytest.mark.asyncio
    async def test_pattern_contains_assertion(self):
        session = self.extend_session(
            "common_session",
            agent_names=["Alice"],
            assertions=[partial(assert_contains_pattern, pattern="sunny")]
        )
        await session.user_says("What is the weather in a typically sunny place?")
        await session.agent_responds("Alice")

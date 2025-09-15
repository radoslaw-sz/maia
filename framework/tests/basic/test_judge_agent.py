import pytest
from maia_test_framework.core.judge_agent import JudgeAgent
from maia_test_framework.testing.base import MaiaTest


class TestJudgeAgent(MaiaTest):

    def setup_agents(self):
        self.create_agent(
            name="RecipeBot",
            provider=self.get_provider("ollama"),
            system_message="You are a helpful assistant that provides recipes.",
        )

    @pytest.mark.asyncio
    async def test_judge_successful_conversation(self):
        """Tests that the JudgeAgent correctly identifies a successful conversation."""
        judge_agent = JudgeAgent(self.get_provider("ollama"))
        session = self.create_session(["RecipeBot"], judge_agent=judge_agent)

        await session.user_says("Can you give me a simple recipe for pancakes?")
        await session.agent_responds("RecipeBot")

    @pytest.mark.xfail(reason="Conversation should be judged as failure.")
    @pytest.mark.asyncio
    async def test_judge_failed_conversation(self):
        """Tests that the JudgeAgent correctly identifies a failed conversation."""
        judge_agent = JudgeAgent(self.get_provider("ollama"))
        session = self.create_session(["RecipeBot"], judge_agent=judge_agent)

        await session.user_says("What is the capital of France?")
        await session.agent_responds("RecipeBot")

    @pytest.mark.xfail(reason="Conversation should be judged as failure.")
    @pytest.mark.asyncio
    async def test_judge_with_requirements(self):
        """Tests that the JudgeAgent can evaluate requirements manually."""
        requirements = [
            "The recipe is for cookies.",
            "The recipe is for a birthday cake." # This should fail.
        ]
        judge_with_reqs = JudgeAgent(self.get_provider("ollama"), requirements=requirements)
        
        session = self.create_session(["RecipeBot"], judge_agent=judge_with_reqs)

        await session.user_says("Give me a recipe for chocolate chip cookies.")
        await session.agent_responds("RecipeBot")
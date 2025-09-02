from typing import List
from crewai import Agent, Task, Crew, LLM
import pytest
from maia_test_framework.providers.crewai import CrewAIProvider
from maia_test_framework.core.message import Message
from maia_test_framework.testing.base import MaiaTest

# Input mapper (maps history to Crew input)
def crew_input_mapper(history: List[Message], system_message: str):
    user_prompt = history[-1].content if history else ""
    return {"query": user_prompt, "system": system_message}

class TestCrewAIIntegration(MaiaTest):
    def setup_agents(self):

        llm=LLM(model="ollama/mistral", base_url="http://localhost:11434")

        # Define simple agents
        researcher = Agent(
            role="Researcher",
            goal="Find information about countries",
            backstory="Expert in geography",
            llm=llm
        )
        responder = Agent(
            role="Responder",
            goal="Answer user queries concisely",
            backstory="Skilled in communication",
            llm=llm
        )

        # Define a task
        task = Task(description="Answer the query: {query}", expected_output="Short factual answer", agent=responder)

        # Create crew
        crew = Crew(agents=[researcher, responder], tasks=[task])

        # Provider
        crewai_provider = CrewAIProvider(config={
            "crew": crew,
            "input_mapper": crew_input_mapper
        })

        # Register agent
        self.create_agent(
            name="CrewAgent",
            provider=crewai_provider,
            system_message="You are a helpful multi-agent assistant."
        )

    @pytest.mark.asyncio
    async def test_crewai_agent(self):
        session = self.create_session(["CrewAgent"])
        await session.user_says("What is the capital of France?")
        response = await session.agent_responds("CrewAgent")

        assert "Paris" in response.content

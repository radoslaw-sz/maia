import pytest
from maia_test_framework.providers.generic_lite_llm import GenericLiteLLMProvider
from maia_test_framework.testing.assertions.agents_participation import assert_agent_participated
from maia_test_framework.testing.base import MaiaTest
from tests.tools.weather_api import WeatherAPITool

class TestToolUsage(MaiaTest):
    def setup_tools(self):
        self.create_tool(
            name="weather_api",
            tool_class=WeatherAPITool,
            mock_responses={
                "london": {
                    "location": "London",
                    "temperature": 25,
                    "condition": "sunny",
                }
            }
        )

    def setup_agents(self):
        self.create_agent(
            name="Alice",
            provider=self.get_provider("ollama"),
            system_message="You are a weather assistant. Only describe the weather.",
            tools=["weather_api"]
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
    async def test_conversation_direct_message(self):
        session = self.create_session(["Alice", "Bob"])

        await session.user_says("Please describe the usual weather in London in July, including temperature and conditions.")
        response_a = await session.agent_responds('Alice')
        print(f"Alice: {response_a.content}")
        assert_agent_participated(session, 'Alice')

        # Assert that the tool was called with the correct parameters
        weather_tool = self.get_tool("weather_api")
        assert weather_tool.get_call_count() == 1
        last_call = weather_tool.get_last_call()
        assert last_call["parameters"]["location"].lower() == "london"
        assert last_call["result"]["location"] == "London"

        await session.user_says(f"Given the weather: {response_a.content}, what clothes should I wear?")
        response_b = await session.agent_responds('Bob')
        print(f"Bob: {response_b.content}")
        assert_agent_participated(session, 'Bob')
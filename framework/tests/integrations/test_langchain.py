import pytest
from langchain_ollama import OllamaLLM
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from src.maia_test_framework.providers.langchain import LangChainProvider
from src.maia_test_framework.testing.base import MaiaTest
from typing import List, Dict, Any
from src.maia_test_framework.core.message import Message

def simple_input_mapper(history: List[Message], system_message: str) -> Dict[str, Any]:
    user_prompt = history[-1].content if history else ""
    place = user_prompt.split("of ")[-1].replace("?", "").strip()
    return {"place": place, "system": system_message}

def simple_output_parser(raw: Dict[str, Any]) -> str:
    return raw.get("output") or raw.get("answer") or str(raw)

class TestLangChainIntegration(MaiaTest):
    def setup_agents(self):
        llm = OllamaLLM(model="mistral")
        prompt = PromptTemplate.from_template("What is the capital of {place}?")
        chain = LLMChain(llm=llm, prompt=prompt)

        langchain_provider = LangChainProvider(config={
            "chain": chain,
            "input_mapper": simple_input_mapper,
            "output_parser": simple_output_parser
        })

        self.create_agent(
            name="LangChainAgent",
            provider=langchain_provider,
            system_message="You are a helpful assistant.",
        )

    @pytest.mark.asyncio
    async def test_langchain_agent(self):
        session = self.create_session(["LangChainAgent"])
        await session.user_says("What is the capital of Poland?")
        response = await session.agent_responds("LangChainAgent")
        
        assert "Warsaw" in response.content

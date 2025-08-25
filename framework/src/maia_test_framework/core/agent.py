# maia_test_framework/core/agent.py
import json
from typing import List
from maia_test_framework.core.message import Message, AgentResponse
from maia_test_framework.providers.base import BaseProvider
from maia_test_framework.core.tools.base import BaseTool

class Agent:
    def __init__(self, name: str, provider: BaseProvider, system_message: str = "", ignore_trigger_prompt: str = "", tools: List[BaseTool] = None):
        self.name = name
        self.provider = provider
        self.system_message = system_message
        self.ignore_trigger_prompt = ignore_trigger_prompt
        self.tools = tools or []

    def _format_tools_prompt(self):
        if not self.tools:
            return ""
        
        tool_schemas = [tool.get_schema() for tool in self.tools]
        
        prompt = """
You have access to the following tools. To use a tool, you must respond with a JSON object with the following structure:
{
    "tool_call": {
        "name": "<tool_name>",
        "parameters": {
            "<parameter_name>": "<parameter_value>"
        }
    }
}

Here are the available tools:
"""
        prompt += json.dumps(tool_schemas, indent=2)
        return prompt

    async def generate_response(self, history: List[Message]) -> AgentResponse:
        system_message = self.system_message + self._format_tools_prompt()
        
        response = await self.provider.generate(
            history=history,
            system_message=system_message,
            ignore_trigger_prompt=self.ignore_trigger_prompt
        )

        try:
            response_data = json.loads(response.content)
            if "tool_call" in response_data:
                tool_call = response_data["tool_call"]
                tool_name = tool_call["name"]
                tool_params = tool_call["parameters"]

                tool_to_use = next((tool for tool in self.tools if tool.name == tool_name), None)

                if tool_to_use:
                    tool_result = await tool_to_use.execute(**tool_params)
                    
                    history.append(Message(sender=self.name, sender_type="agent", receiver=tool_call["name"], receiver_type="tool", content=response.content))
                    history.append(Message(sender=tool_call["name"], sender_type="tool", content=json.dumps({"tool_output": tool_result})))

                    # Second call to LLM with tool result
                    return await self.provider.generate(
                        history=history,
                        system_message=system_message,
                        ignore_trigger_prompt=self.ignore_trigger_prompt
                    )
        except (json.JSONDecodeError, KeyError):
            # Not a tool call, return original response
            pass

        return response

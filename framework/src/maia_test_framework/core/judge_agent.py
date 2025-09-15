import asyncio
import json
from typing import Protocol, List, Optional

from maia_test_framework.core.agent import Agent
from maia_test_framework.core.message import Message
from maia_test_framework.core.types.judge_result import JudgeResult, RequirementResult

class SessionInterface(Protocol):
    def get_conversation_text(): str


class JudgeAgent(Agent):
    """
    An agent responsible for evaluating a conversation session and determining
    if the user's initial request was successfully fulfilled.
    """

    def __init__(self, provider, name="Judge", requirements: Optional[List[str]] = None, **kwargs):
        self.requirements = requirements
        if requirements:
            system_message = """You are a Judge AI. Your role is to determine if a conversation between a user and one or more AI agents 
resulted in the successful fulfillment of the user's original request and meets a list of requirements.

Analyze the entire conversation history provided. The user's request is the first message from the user.
The subsequent messages are the responses from the agents.

Your response MUST be in a JSON format. The JSON object should have the following properties:
- \"overall_assessment\": An object containing the overall assessment of the conversation, with the following properties:
  - \"verdict\": A string, either \"SUCCESS\" or \"FAILURE\".
  - \"score\": A float from 0.0 to 10.0.
  - \"reasoning\": A brief, single-sentence justification for your decision.
- \"requirements\": An array of objects, where each object evaluates a single requirement. Each object should have:
  - \"requirement\": The text of the requirement being evaluated.
  - \"verdict\": A string, either \"SUCCESS\" or \"FAILURE\".
  - \"score\": A float from 0.0 to 10.0.
  - \"reasoning\": A brief, single-sentence justification for your decision.

- Overall SUCCESS means the agent(s) provided a direct and complete answer to the user's initial query.
- Overall FAILURE means the agent(s) failed to answer, evaded the question, or provided an irrelevant or incomplete response.
- Requirement SUCCESS means the conversation explicitly and correctly fulfills the requirement.
- Requirement FAILURE means the conversation does not fulfill the requirement.

The requirements to be evaluated will be listed in the user prompt.

Example response:
{
  \"overall_assessment\": {
    \"verdict\": \"SUCCESS\",
    \"score\": 9.0,
    \"reasoning\": \"The agent provided a comprehensive and accurate answer to the user's request.\"
  },
  \"requirements\": [
    {
      \"requirement\": \"The response must be in French.\",
      \"verdict\": \"SUCCESS\",
      \"score\": 10.0,
      \"reasoning\": \"The entire response was correctly written in French.\"
    },
    {
      \"requirement\": \"The response must mention the Eiffel Tower.\",
      \"verdict\": \"FAILURE\",
      \"score\": 0.0,
      \"reasoning\": \"The response did not mention the Eiffel Tower.\"
    }
  ]
}
"""
        else:
            system_message = """You are a Judge AI. Your role is to determine if a conversation between a user and one or more AI agents 
resulted in the successful fulfillment of the user's original request.

Analyze the entire conversation history provided. The user's request is the first message from the user.
The subsequent messages are the responses from the agents.

Your response MUST be in a JSON format. The JSON object should have the following properties:
- \"verdict\": A string, either \"SUCCESS\" or \"FAILURE\".
- \"score\": A float from 0.0 to 10.0, where 10.0 is a perfect, direct, and concise answer, and 0.0 is a complete failure.
- \"reasoning\": A brief, single-sentence justification for your decision.

- SUCCESS means the agent(s) provided a direct and complete answer to the user's initial query.
- FAILURE means the agent(s) failed to answer, evaded the question, or provided an irrelevant or incomplete response.

Example response:
{
  \"verdict\": \"SUCCESS\",
  \"score\": 8.5,
  \"reasoning\": \"The agent correctly answered the user's question about the capital of France.\"
}
"""
        super().__init__(name=name, provider=provider, system_message=system_message, **kwargs)

    async def judge_session(self, session: SessionInterface) -> JudgeResult:
        """
        Evaluates the session and returns a verdict on whether the user's request was met.
        If requirements are provided in the constructor, it also evaluates the conversation against each requirement.

        Args:
            session: The conversation session to evaluate.

        Returns:
            A JudgeResult object containing the verdict, score, reasoning, and requirement results.
        """
        conversation_log = session.get_conversation_text()
        if not conversation_log:
            return JudgeResult(verdict="FAILURE", score=0.0, reasoning="The conversation was empty.")

        user_prompt_content = f"Here is the conversation log:\n\n{conversation_log}"

        if self.requirements:
            user_prompt_content += "\n\nHere are the requirements to check:\n\n- " + "\n- ".join(self.requirements)

        # The history for the judge is just the single user prompt containing the log.
        judge_history = [Message(sender="user", content=user_prompt_content, sender_type="user")]

        # Get the judge's verdict by calling the provider directly
        response_message = await self.provider.base_generate(
            history=judge_history,
            system_message=self.system_message
        )
        response_text = response_message.content.strip()

        # Parse the response
        try:
            # The model may wrap the JSON in ```json ... ```, so we need to extract it.
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON object found in the response.")
            json_string = response_text[json_start:json_end]
            
            response_data = json.loads(json_string)

            if self.requirements:
                return self._parse_response_with_requirements(response_data, self.requirements)
            else:
                return self._parse_standard_response(response_data)
        except (json.JSONDecodeError, ValueError) as e:
            return JudgeResult(verdict="FAILURE", score=0.0, reasoning=f"Error parsing judge's JSON response: {e}. Response: {response_text}")
        except Exception as e:
            return JudgeResult(verdict="FAILURE", score=0.0, reasoning=f"Error processing judge's response: {e}")

    def _parse_standard_response(self, response_data: dict) -> JudgeResult:
        verdict = response_data.get("verdict", "").upper()
        score = response_data.get("score")
        reasoning = response_data.get("reasoning", "No reasoning provided.")

        if verdict not in ["SUCCESS", "FAILURE"]:
            return JudgeResult(verdict="FAILURE", score=0.0, reasoning=f"Invalid verdict in JSON response: {verdict}")

        if not isinstance(score, (int, float)):
            return JudgeResult(verdict=verdict, score=0.0, reasoning=f"Invalid or missing score in JSON response: {score}")

        return JudgeResult(verdict=verdict, score=float(score), reasoning=reasoning)

    def _parse_response_with_requirements(self, response_data: dict, requirements: List[str]) -> JudgeResult:
        overall_assessment_data = response_data.get("overall_assessment")
        if not isinstance(overall_assessment_data, dict):
            return JudgeResult(verdict="FAILURE", score=0.0, reasoning="Missing or invalid 'overall_assessment' in JSON response.")

        # Parse overall assessment
        base_result = self._parse_standard_response(overall_assessment_data)
        if base_result.verdict == "FAILURE" and base_result.score == 0.0:
            # Propagate parsing errors
            return base_result

        requirement_results = []
        requirements_data = response_data.get("requirements", [])
        if not isinstance(requirements_data, list):
             return JudgeResult(verdict="FAILURE", score=0.0, reasoning="Invalid 'requirements' field in JSON response, expected a list.")

        for i, req_data in enumerate(requirements_data):
            try:
                if not isinstance(req_data, dict):
                    raise ValueError("Requirement entry is not a dictionary.")

                req_text = req_data.get("requirement")
                req_verdict = req_data.get("verdict", "").upper()
                req_score = req_data.get("score")
                req_reasoning = req_data.get("reasoning", "No reasoning provided.")

                if not req_text:
                    raise ValueError("Missing 'requirement' text.")

                if req_verdict not in ["SUCCESS", "FAILURE"]:
                     raise ValueError(f"Invalid verdict: {req_verdict}")
                
                if not isinstance(req_score, (int, float)):
                    raise ValueError(f"Invalid or missing score: {req_score}")

                requirement_results.append(RequirementResult(
                    requirement=req_text,
                    verdict=req_verdict,
                    score=float(req_score),
                    reasoning=req_reasoning
                ))
            except (ValueError, KeyError) as e:
                requirement_results.append(RequirementResult(
                    requirement=requirements[i] if i < len(requirements) else "Unknown requirement",
                    verdict="FAILURE",
                    score=0.0,
                    reasoning=f"Failed to parse requirement from judge. Error: {e}. Data: {req_data}"
                ))

        base_result.requirements = requirement_results
        return base_result

    async def judge_and_assert(self, session: SessionInterface):
        """
        Evaluates the session and asserts that the user's request was met.
        If requirements are provided in the constructor, it also asserts that all requirements were met.

        Args:
            session: The conversation session to evaluate.

        Raises:
            AssertionError: If the JudgeAgent determines the conversation was a "FAILURE"
                            or if any requirement was not met.
        """
        result = await self.judge_session(session)
        session.judge_result = result
        if result.verdict == "FAILURE":
            raise AssertionError(f"Judge marked session as FAILURE with score {result.score}. Reason: {result.reasoning}")
        
        if result.requirements:
            failed_requirements = [req for req in result.requirements if req.verdict == "FAILURE"]
            if failed_requirements:
                error_messages = [f"Requirement '{req.requirement}' was not met. Reason: {req.reasoning}" for req in failed_requirements]
                raise AssertionError("Judge marked one or more requirements as FAILURE:\n" + "\n".join(error_messages))

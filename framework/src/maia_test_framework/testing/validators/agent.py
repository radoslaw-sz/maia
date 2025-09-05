from typing import Callable
from maia_test_framework.core.session import Session

def agent_not_participating_validator(agent_name: str) -> Callable[[Session], None]:
    """
    Returns a validator that asserts that a specific agent has not participated in the conversation.
    """
    def agent_not_participating(session: Session):
        """Asserts that a specific agent has not participated in the conversation."""
        for message in session.message_history:
            if message.sender == agent_name:
                raise AssertionError(f"Agent {agent_name} participated in the conversation when they should not have.")

    return agent_not_participating

def agent_message_count_validator(agent_name: str, max_messages: int) -> Callable[[Session], None]:
    """
    Returns a validator that asserts that an agent has sent a number of messages below a certain threshold.
    """
    def agent_message_count(session: Session):
        """Asserts that an agent has sent a number of messages below a certain threshold."""
        count = sum(1 for message in session.message_history if message.sender == agent_name)
        if count >= max_messages:
            raise AssertionError(f"Agent {agent_name} sent {count} messages, which is not below the threshold of {max_messages}.")

    return agent_message_count

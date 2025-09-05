from typing import Callable
from maia_test_framework.core.session import Session

def conversation_validator() -> Callable[[Session], None]:
    """
    Returns a validator that asserts that agents take turns in the conversation.
    """
    def turn_taking_validator(session: Session):
        """Asserts that agents take turns in the conversation."""
        messages = session.message_history
        for i in range(1, len(messages)):
            if messages[i].sender == messages[i-1].sender:
                raise AssertionError(f"Agent {messages[i].sender} sent two messages in a row.")
    
    return turn_taking_validator
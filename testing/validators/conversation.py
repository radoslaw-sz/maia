from maia_test_framework.testing.validators.base import BaseValidator
from maia_test_framework.core.session import Session

class ConversationValidator(BaseValidator):
    def __init__(self, session: Session):
        super().__init__(session)
        
    def assert_turn_taking_etiquette(self):
        """Asserts that agents take turns in the conversation."""
        messages = self.session.message_history
        for i in range(1, len(messages)):
            if messages[i].sender == messages[i-1].sender:
                raise AssertionError(f"Agent {messages[i].sender} sent two messages in a row.")

    def validate(self):
        self.assert_turn_taking_etiquette()
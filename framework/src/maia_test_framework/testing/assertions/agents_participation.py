from maia_test_framework.core.session import Session
from maia_test_framework.testing.assertions.base import as_assertion_factory

@as_assertion_factory
def assert_agent_participated(session: Session, agent_name: str):
    """Assert that specific agent participated in conversation"""
    agent_messages = [msg for msg in session.message_history if msg.sender == agent_name]
    assert len(agent_messages) > 0, f"Agent '{agent_name}' did not participate in conversation"
    return f"Agent '{agent_name}' participated in conversation"

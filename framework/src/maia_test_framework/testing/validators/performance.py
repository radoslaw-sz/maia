from typing import Callable
from maia_test_framework.core.session import Session
from datetime import timedelta

def performance_validator(threshold: int, unit: str = "seconds") -> Callable[[Session], None]:
    """
    Returns a validator that asserts that the latency between user and agent messages is below a threshold.
    """
    def latency_validator(session: Session):
        """Asserts that the latency between user and agent messages is below a threshold."""
        if unit == "milliseconds":
            delta = timedelta(milliseconds=threshold)
        elif unit == "seconds":
            delta = timedelta(seconds=threshold)
        elif unit == "minutes":
            delta = timedelta(minutes=threshold)
        else:
            raise ValueError("unit must be one of 'milliseconds', 'seconds', or 'minutes'")

        messages = session.message_history
        for i in range(1, len(messages)):
            if messages[i-1].sender == "user":
                latency = messages[i].timestamp - messages[i-1].timestamp
                if latency > delta:
                    raise AssertionError(f"Latency of {latency} between user and agent {messages[i].sender} exceeded the threshold of {delta}.")

    return latency_validator

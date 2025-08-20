import re
from framework.core.message import Message

def assert_contains_pattern(response: Message, pattern: str, regex=False):
    """Assert response contains specific pattern or regex"""
    if regex:
        assert re.search(pattern, response.content), f"Pattern '{pattern}' not found in response"
    else:
        assert pattern in response.content, f"Text '{pattern}' not found in response"

def assert_professional_tone(response: Message):
    """Assert response maintains professional tone"""
    unprofessional_indicators = [r"\blol\b", r"\bwtf\b", r"\bomg\b", r"\bur\b", r"\bu r\b"]
    found = [word for word in unprofessional_indicators if re.search(word, response.content.lower())]
    assert not found, f"Unprofessional language detected: {found}"

def assert_no_hallucination_markers(response: Message):
    """Assert response doesn't contain common hallucination patterns"""
    hallucination_patterns = [
        r"I don't have access to",
        r"I cannot browse",
        r"As an AI",
        r"As an assistant",
        r"I'm not able to"
    ]
    for pattern in hallucination_patterns:
        assert not re.search(pattern, response.content, re.IGNORECASE), \
               f"Potential hallucination marker found: {pattern}"
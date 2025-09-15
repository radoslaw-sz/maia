from dataclasses import asdict, dataclass, field
from typing import List


@dataclass
class RequirementResult:
    """
    Represents the result of a single requirement evaluation.
    """
    requirement: str
    verdict: str  # "SUCCESS" or "FAILURE"
    score: float  # 0.0 to 10.0
    reasoning: str

    def to_dict(self):
        return asdict(self)


@dataclass
class JudgeResult:
    """
    Represents the result of a JudgeAgent's evaluation.
    """
    verdict: str  # "SUCCESS" or "FAILURE"
    score: float  # 0.0 to 10.0
    reasoning: str
    requirements: List[RequirementResult] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
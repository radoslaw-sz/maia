from abc import ABC, abstractmethod
import functools
from typing import Any, Callable, Optional

class MaiaAssertion(ABC):
    """Abstract base class for all test assertions."""

    @abstractmethod
    def call(self):
        """Executes the assertion logic."""
        pass

    def get_name(self) -> Optional[str]:
        """Returns the name of the assertion function."""
        return None

class _FunctionalAssertion(MaiaAssertion):
    """A generic assertion object that wraps a function call."""
    def __init__(self, func: Callable, args: tuple, kwargs: dict):
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def call(self):
        return self._func(*self._args, **self._kwargs)

    def get_name(self) -> str:
        target_func = self._func
        if isinstance(target_func, functools.partial):
            target_func = target_func.func
        return target_func.__name__

def as_assertion_factory(func: Callable[..., Any]) -> Callable[..., MaiaAssertion]:
    """
    A decorator that turns an assertion function into a factory
    that produces a MaiaAssertion object.
    
    Usage:
    @as_assertion_factory
    def my_assertion(arg1, arg2):
        assert arg1 == arg2
        
    # This now returns a MaiaAssertion object instead of executing directly:
    assertion_object = my_assertion(1, 1) 
    """
    @functools.wraps(func)
    def factory(*args: Any, **kwargs: Any) -> MaiaAssertion:
        return _FunctionalAssertion(func, args, kwargs)
    return factory

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Pytest hook to access test report information.
    This hook attaches the report for each phase (setup, call, teardown)
    to the test class instance, allowing it to know its own outcome.
    """
    # Execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # Store the report object on the item for each phase
    setattr(item, "rep_" + rep.when, rep)

    # Also attach the report to the class instance if it exists
    if hasattr(item, "instance"):
        setattr(item.instance, "rep_" + rep.when, rep)
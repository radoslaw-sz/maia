import pytest
import json
import os
from pathlib import Path
from glob import glob
from datetime import datetime
import traceback

_run_output_dir = None

def pytest_addoption(parser):
    parser.addoption(
        "--maia-report", action="store", default=None,
        help="Path to unified Maia JSON test report"
    )
    parser.addoption(
        "--maia-output-dir", action="store", default=None,
        help="Directory to save Maia test reports"
    )

def pytest_configure(config):
    """Setup run directory before tests start"""
    global _run_output_dir
    
    output_dir_option = config.getoption("--maia-output-dir")
    if output_dir_option:
        base_output_dir = output_dir_option
    else:
        base_output_dir = os.getenv("MAIA_TEST_OUTPUT_DIR", "test_reports")

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    _run_output_dir = os.path.join(base_output_dir, timestamp)

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)

def pytest_runtest_teardown(item):
    """Called after test teardown. Save test results here."""
    from maia_test_framework.testing.base import MaiaTest, TestResult, Participant

    if not hasattr(item, 'instance') or not isinstance(item.instance, MaiaTest):
        return

    test_instance = item.instance

    final_pytest_status = "passed"
    if (hasattr(test_instance, 'rep_setup') and test_instance.rep_setup.failed) or \
       (hasattr(test_instance, 'rep_call') and test_instance.rep_call.failed) or \
       (hasattr(test_instance, 'rep_teardown') and test_instance.rep_teardown.failed):
        final_pytest_status = "failed"

    all_participants = {}
    session_data = []
    for s in test_instance.sessions:
        history = [msg.to_dict() for msg in s.message_history]
        session_participant_ids = set()

        for msg in s.message_history:
            session_participant_ids.add(msg.sender)
            if msg.receiver:
                session_participant_ids.add(msg.receiver)

        for participant_id in session_participant_ids:
            if participant_id not in all_participants:
                if participant_id == "user":
                    all_participants[participant_id] = Participant(id="user", name="User", type="user")
                elif participant_id in test_instance.agents:
                    agent = test_instance.agents[participant_id]
                    all_participants[participant_id] = Participant(id=participant_id, name=participant_id, type="agent", metadata={"model": agent.provider.__class__.__name__})
                elif participant_id in test_instance.tools:
                    all_participants[participant_id] = Participant(id=participant_id, name=participant_id, type="tool")

        session_data.append({
            "id": s.id,
            "participants": list(session_participant_ids),
            "messages": history,
        })
    
    participants = list(all_participants.values())
    
    result = TestResult(
        test_name=test_instance.test_name,
        start_time=test_instance.start_time,
        end_time=datetime.now().isoformat(),
        status=final_pytest_status,
        participants=participants,
        sessions=session_data,
        assertions=test_instance.assertion_results,
        validators=test_instance.validator_results
    )
    
    if _run_output_dir:
        result.save(output_dir=_run_output_dir)

def pytest_sessionfinish(session, exitstatus):
    report_path = session.config.getoption("--maia-report")
    if not report_path:
        return

    if not _run_output_dir or not os.path.exists(_run_output_dir):
        session.config.pluginmanager.get_plugin("terminalreporter").write_line(
            f"Maia report directory not found: {_run_output_dir}"
        )
        return

    latest_run_dir = Path(_run_output_dir)

    # Collect all JSON test result files from this run
    test_files = glob(str(latest_run_dir / "*.json"))

    merged_results = []
    for file_path in test_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                merged_results.append(json.load(f))
        except Exception as e:
            merged_results.append({
                "test_file": str(file_path),
                "error": f"Failed to load: {e}"
            })

    # Write unified report
    out_path = Path(report_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(merged_results, f, indent=2)

    session.config.pluginmanager.get_plugin("terminalreporter").write_line(
        f"Maia unified report written to {out_path}"
    )

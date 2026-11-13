"""pytest 插件：把失败的用例收集到 reports/failures.json，供 python main.py analyze 用。"""
import json
from pathlib import Path

import pytest

_REPORT_DIR = Path(__file__).resolve().parent.parent / "reports"
_FAILURES = []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        case = getattr(item, "callspec", None)
        params = getattr(case, "params", {}) if case else {}
        case_info = params.get("case", {})
        _FAILURES.append({
            "id": case_info.get("id", item.name),
            "name": case_info.get("name", ""),
            "method": case_info.get("method", ""),
            "path": case_info.get("path", ""),
            "expected_status": case_info.get("expected_status", ""),
            "error": str(report.longrepr)[:2000],
        })


def pytest_sessionfinish(session, exitstatus):
    _REPORT_DIR.mkdir(exist_ok=True)
    path = _REPORT_DIR / "failures.json"
    path.write_text(
        json.dumps(_FAILURES, ensure_ascii=False, indent=2), encoding="utf-8"
    )

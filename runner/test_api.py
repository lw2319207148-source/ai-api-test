"""执行生成的接口测试用例（pytest 文件）。

用法：先 python main.py run <用例json>，它会生成 runner/generated_cases.py，
然后这里用 pytest 参数化把每条用例跑一遍。
"""
import os
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

try:
    from runner.generated_cases import CASES
except ImportError:
    CASES = []  # 还没生成时先空着

BASE = os.getenv("TARGET_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def _get_json(resp):
    try:
        return resp.json()
    except ValueError:
        return {}


if CASES:

    @pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c['id']}-{c['name']}")
    def test_api_case(case):
        _run_case(case)

else:

    def test_api_case():
        pytest.skip("没有用例：先运行 python main.py run <用例json> 生成")


def _run_case(case):
    url = BASE + case["path"]
    method = case["method"].upper()
    body = case.get("body")

    # 防御性检查：POST/PUT 必须有 body（专门测"缺少请求体"且期望 422 的除外）。
    # 这样 AI 忘写 body 时，错误信息一眼就能看懂，而不是到服务端才报 422。
    if method in ("POST", "PUT") and body is None and case["expected_status"] != 422:
        raise AssertionError(
            f"{case['id']}（{case.get('name', '')}）是 {method} 请求但没有 body："
            "POST/PUT 必须带合法请求体（只有测「缺少请求体」且期望 422 才允许省略）"
        )

    resp = requests.request(
        method=method,
        url=url,
        headers=case.get("headers") or {},
        params=case.get("params") or {},
        json=body if body is not None else None,
        timeout=10,
    )

    # 1) 断言 HTTP 状态码
    assert resp.status_code == case["expected_status"], (
        f"状态码不符：期望 {case['expected_status']}，实际 {resp.status_code}；"
        f"响应体：{resp.text[:200]}"
    )

    # 2) 断言期望出现的字段
    if case.get("expect_fields"):
        body = _get_json(resp)
        if isinstance(body, list):  # 列表响应取第一条来检查
            body = body[0] if body else {}
        for field in case["expect_fields"]:
            assert field in body, (
                f"响应缺少字段 {field}；实际响应：{resp.text[:200]}"
            )

    # 3) 断言不应出现的字段
    if case.get("expect_absent_fields"):
        body = _get_json(resp)
        for field in case["expect_absent_fields"]:
            assert field not in body, (
                f"响应不应包含字段 {field}；实际响应：{resp.text[:200]}"
            )

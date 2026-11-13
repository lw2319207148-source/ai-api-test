"""项目入口。

用法（在 ai-api-test 目录下执行）：
    python main.py gen [接口描述json] [输出用例json]
        例：python main.py gen examples/users_api.json cases.json
        作用：调 LLM 根据接口描述生成测试用例，存到 cases.json

    python main.py run [用例json]
        例：python main.py run cases.json
        例：python main.py run examples/sample_cases.json   # 不用 LLM 也能先跑通
        作用：把用例转成 pytest 测试并执行，生成 reports/report.html

    python main.py check
        作用：检查 LLM 网关和靶子接口是否都连得上（先自检再跑）

    python main.py analyze [失败json]
        例：python main.py analyze reports/failures.json
        作用：把失败用例发给 AI，让它用中文分析原因并给修复建议
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent  # 项目根目录，保证在任意位置运行都正确


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "gen":
        spec_file = sys.argv[2] if len(sys.argv) > 2 else "examples/users_api.json"
        out_file = sys.argv[3] if len(sys.argv) > 3 else "cases.json"

        spec_path = ROOT / spec_file
        if not spec_path.exists():
            print(f"[gen] 找不到接口描述文件：{spec_file}")
            print("[gen] 确认文件在 ai-api-test 目录下，例如：python main.py gen examples/users_api.json cases.json")
            return

        from generator.llm_client import generate_cases

        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        try:
            cases = generate_cases(spec)
        except ValueError as e:
            print(f"[gen] AI 输出的用例格式不合格：{e}")
            print("[gen] 模型输出有随机性，直接重跑一次本命令通常就能过；")
            print("[gen] 若反复失败，把 .env 的 LLM_MODEL 换成 check 列出的其他 DeepSeek V4 模型再试")
            return
        except RuntimeError as e:
            print(f"[gen] 调用失败：{e}")
            return
        (ROOT / out_file).write_text(
            json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[OK] 已生成 {len(cases)} 条用例 -> {out_file}")

    elif cmd == "run":
        cases_file = sys.argv[2] if len(sys.argv) > 2 else "cases.json"

        import pytest
        from runner.make_tests import make_tests

        cases_path = ROOT / cases_file
        if not cases_path.exists():
            print(f"[run] 找不到用例文件：{cases_file}")
            print("[run] 想接 AI 生成，先跑：python main.py gen examples/users_api.json cases.json")
            print("[run] 想直接看效果，跑现成样例：python main.py run examples/sample_cases.json")
            return

        try:
            make_tests(str(cases_path), str(ROOT / "runner" / "generated_cases.py"))
        except ValueError as e:
            print(f"[run] 用例文件有问题：{e}")
            print("[run] 用例 json 必须是一个非空数组（每条含 id/name/method/path/expected_status 等字段）")
            return
        reports_dir = ROOT / "reports"
        reports_dir.mkdir(exist_ok=True)  # pytest-html 不会自动建目录
        print(f"[RUN] 开始执行 {cases_file} ...")
        pytest.main([
            "-v",
            str(ROOT / "runner" / "test_api.py"),
            f"--html={reports_dir / 'report.html'}",
            "--self-contained-html",
        ])
        print("[RUN] 执行结束。报告：reports/report.html")
        print("[RUN] 若有失败，跑：python main.py analyze reports/failures.json 让 AI 帮你分析")

    elif cmd == "check":
        import requests
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
        base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
        target = os.getenv("TARGET_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
        api_key = os.getenv("LLM_API_KEY", "")
        model = (os.getenv("LLM_MODEL") or "").strip()

        if not base_url:
            print("[check] 未配置 LLM_BASE_URL（先复制 .env.example 为 .env）")
        else:
            try:
                r = requests.get(f"{base_url}/models", timeout=5)
                print(f"[check] LLM 网关 {base_url} -> 有响应 (HTTP {r.status_code})")
            except Exception as e:
                print(f"[check] LLM 网关 {base_url} 连不上：{e.__class__.__name__}（先确认 WorkBuddy/网关程序已启动）")

            # 带密钥再问一次 /models，顺便列出可用模型名（方便用户填 LLM_MODEL）
            try:
                r2 = requests.get(
                    f"{base_url}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10,
                )
                if r2.status_code == 200:
                    ids = [m.get("id") for m in r2.json().get("data", []) if m.get("id")]
                    print(f"[check] 可用模型：{ids}")
                else:
                    print(f"[check] 带密钥访问 /models 返回 {r2.status_code}（密钥可能不对）")
            except Exception:
                pass

            print(f"[check] 当前 .env 里的 LLM_MODEL = {model or '(空，会自动选用第一个可用模型)'}")

        try:
            r = requests.get(f"{target}/health", timeout=5)
            print(f"[check] 靶子接口 {target} -> 有响应 (HTTP {r.status_code})")
        except Exception as e:
            print(f"[check] 靶子接口 {target} 连不上：{e.__class__.__name__}（先启动 uvicorn）")

    elif cmd == "analyze":
        from generator.analyze import analyze_failures

        failures_file = sys.argv[2] if len(sys.argv) > 2 else "reports/failures.json"
        failures_path = ROOT / failures_file
        if not failures_path.exists():
            print(f"[analyze] 找不到失败记录：{failures_file}")
            print("[analyze] 说明还没有失败用例，或还没跑过 python main.py run（跑完会生成 reports/failures.json）")
            return
        print("[ANALYZE] 让 AI 分析失败用例 ...")
        text = analyze_failures(str(failures_path))
        print("\n" + text + "\n")

    else:
        print("未知命令。用法：python main.py gen|run|check|analyze")


if __name__ == "__main__":
    main()

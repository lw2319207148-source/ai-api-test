"""把用例 JSON 转成 pytest 可导入的 runner/generated_cases.py。"""
import json
from pathlib import Path


def make_tests(cases_file: str, out_file: str = "runner/generated_cases.py") -> str:
    cases = json.loads(Path(cases_file).read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"{cases_file} 里不是非空数组")
    # 关键：JSON 的 null/true/false 不是合法的 Python 字面量，
    # 所以不能直接把 JSON 文本赋给 CASES，要用 repr 后的字符串 + json.loads 还原
    payload = json.dumps(cases, ensure_ascii=False)
    content = (
        "# 本文件由 runner/make_tests.py 自动生成，勿手改\n"
        "import json\n\n"
        f"CASES = json.loads({payload!r})\n"
    )
    Path(out_file).write_text(content, encoding="utf-8")
    return out_file

"""把失败的用例喂给 LLM，让它用中文分析原因并给修复建议。"""
import json
from pathlib import Path

from generator.llm_client import chat


def analyze_failures(failures_file: str) -> str:
    fails = json.loads(Path(failures_file).read_text(encoding="utf-8"))
    if not fails:
        return "没有失败用例，无需分析。"

    user = (
        "下面是一批接口自动化测试里失败的用例，请用中文逐个分析可能的失败原因，"
        "并给出具体、可操作的修复建议（是接口代码的 bug、用例写错、还是环境问题）：\n"
        + json.dumps(fails, ensure_ascii=False, indent=2)
    )
    messages = [
        {
            "role": "system",
            "content": "你是一名资深测试工程师，擅长定位接口测试失败原因。回答要分条、具体、可操作。",
        },
        {"role": "user", "content": user},
    ]
    return chat(messages, temperature=0.3)

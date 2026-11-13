"""校验并解析 LLM 返回的 JSON 用例列表。

LLM 有时会输出 markdown 代码块、或数组前后带废话，
这里做"宽容解析"：只要文本里有 JSON 数组，就把它抠出来解析。
"""
import json
import re

REQUIRED = ["category", "method", "path", "expected_status"]


def parse_cases(text: str) -> list[dict]:
    text = text.strip()
    # 去掉可能的 ```json ... ``` 围栏
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    # 截取第一个 '[' 到最后一个 ']'
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("LLM 输出里找不到 JSON 数组")
    data = json.loads(text[start:end + 1])
    if not isinstance(data, list) or not data:
        raise ValueError("LLM 输出不是非空数组")

    cases = []
    for index, item in enumerate(data, 1):
        if not isinstance(item, dict):
            raise ValueError("每个用例必须是 JSON 对象")
        for key in REQUIRED:
            if key not in item:
                raise ValueError(f"用例缺少字段：{key}")
        # id / name 缺失时自动补（有的模型会忘写）
        item.setdefault("id", f"case-{index}")
        item.setdefault("name", f"{item['method']} {item['path']}")
        # 补齐可选字段，保证后续执行代码不用做一堆判断
        item.setdefault("headers", {})
        item.setdefault("params", {})
        item.setdefault("body", None)
        item.setdefault("expect_fields", [])
        item.setdefault("expect_absent_fields", [])

        # 语义检查：POST/PUT 这类"带请求体"的请求，AI 经常忘写 body，
        # 导致接口直接 422。这里强制要求补上。
        # 唯一例外：专门测「缺少请求体」且 expected_status=422 的负向用例允许省略 body。
        method = str(item.get("method", "")).upper()
        if method in ("POST", "PUT") and item.get("body") is None:
            if item.get("expected_status") != 422:
                raise ValueError(
                    f"用例 {item.get('id', '?')}（{item.get('name', '')}）是 {method} 请求但 body 为 null；"
                    "POST/PUT 必须给出合法请求体 body。只有专门测「缺少请求体」且 expected_status=422 的负向用例才允许省略。"
                )

        cases.append(item)
    return cases

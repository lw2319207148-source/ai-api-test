"""调用 DeepSeek V4（OpenAI 兼容接口）生成测试用例 / 分析失败原因。

连接信息从项目根目录的 .env 读取：LLM_BASE_URL / LLM_API_KEY / LLM_MODEL
（参考 .env.example）
"""
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from generator.prompt import build_messages
from generator.schemas import parse_cases

# 始终读项目根目录的 .env，避免「在别的目录执行命令就读不到」的问题
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_FILE)


def _list_model_ids(base_url: str, api_key: str) -> list:
    """尝试调 /models 列出可用模型 id，失败返回空列表。"""
    try:
        r = requests.get(
            f"{base_url}/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        if r.status_code == 200:
            return [m.get("id") for m in r.json().get("data", []) if m.get("id")]
    except Exception:
        pass
    return []


def _resolve() -> tuple:
    """读取 .env 里的连接信息；模型名为空时自动取第一个可用模型。"""
    base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
    api_key = os.getenv("LLM_API_KEY", "")
    model = (os.getenv("LLM_MODEL") or "").strip()

    if not base_url:
        raise RuntimeError("请先在 .env 里填入 LLM_BASE_URL（wb2api 反代地址）")
    if not api_key:
        # 本地网关（如 wb2api）通常不校验密钥，给个占位值即可
        api_key = "local-gateway"
    if not model:
        ids = _list_model_ids(base_url, api_key)
        # 只挑 DeepSeek V4 系列的模型（用户约束），优先 flash（快）
        deepseek = [i for i in ids if "deepseek-v4" in i.lower()]
        flash = [i for i in deepseek if "flash" in i.lower()]
        if flash:
            model = flash[0]
        elif deepseek:
            model = deepseek[0]
        else:
            raise RuntimeError(
                "LLM_MODEL 没填，且网关的可用模型里没找到 DeepSeek V4 系列。"
                "请先运行 python main.py check 看可用模型，再把模型名填进 .env 的 LLM_MODEL"
            )
        print(f"[LLM] 自动选用模型：{model}")
    return base_url, api_key, model


def chat(messages: list, temperature: float = 0.3, max_retries: int = 2) -> str:
    """通用对话调用：发 messages，返回模型回复文本。"""
    base_url, api_key, model = _resolve()
    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": temperature}

    last_error = None
    for _ in range(max_retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:  # 网络错误 / 服务端错误都走重试
            last_error = e

    raise RuntimeError(f"调用 LLM 失败（已重试 {max_retries} 次）：{last_error}")


def generate_cases(api_spec: dict, max_retries: int = 2) -> list:
    """根据接口描述生成测试用例，返回解析后的用例列表。

    AI 有时会漏字段，所以解析失败时会把错误反馈给模型、让它重新输出，
    最多再试 max_retries 次，最后还不行才抛异常。
    """
    messages = build_messages(api_spec)
    last_error = None
    for attempt in range(max_retries + 1):
        content = chat(messages, temperature=0.2, max_retries=2)
        try:
            return parse_cases(content)
        except ValueError as e:
            last_error = e
            # 把上次的坏输出和错误原因贴回去，让模型照着改
            messages = messages + [
                {"role": "assistant", "content": content[:2000]},
                {
                    "role": "user",
                    "content": (
                        f"你刚才的输出解析失败：{e}。"
                        "请严格按字段要求，重新输出完整的 JSON 数组，"
                        "每个用例都必须包含 id、name、category、method、path、"
                        "expected_status、expect_fields、expect_absent_fields，"
                        "不要省略任何字段、不要输出 JSON 以外的内容。"
                    ),
                },
            ]
    raise ValueError(f"AI 输出连续 {max_retries + 1} 次解析失败：{last_error}")

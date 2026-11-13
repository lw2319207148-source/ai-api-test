"""构造给 LLM 的提示词：让它基于接口描述，生成严格的 JSON 用例列表。"""
import json

SYSTEM = (
    "你是一名资深接口测试工程师。根据给定的接口描述，设计覆盖三类场景的测试用例："
    "normal（正常）、boundary（边界）、exception（异常/负向）。"
    "只输出一个 JSON 数组，不要任何解释、不要 markdown 代码块。"
    "数组里每个元素必须是对象，且包含这些字段："
    "id(字符串，格式如 TC-LOGIN-001)、name(字符串)、category(取 normal/boundary/exception)、"
    "method(HTTP方法)、path(接口路径)、headers(对象，可为空对象)、"
    "params(查询参数对象，可为空对象)、body(请求体对象或 null)、"
    "expected_status(期望的 HTTP 状态码整数)、"
    "expect_fields(期望响应中出现的字段名数组)、"
    "expect_absent_fields(期望响应中不应出现的字段名数组)。"
    "重要规则：POST/PUT 请求的 body 必须给出合法的请求体 JSON 对象，"
    "绝不能写 null（除非这条用例就是专门测「缺少请求体」，此时 expected_status 应为 422）。"
    "expected_status 必须与场景自洽：登录成功=200、密码错误=401、缺 token/错 token=401、"
    "缺必填字段=422、重复用户名=409、资源不存在=404、非法 id=422。"
)


def build_messages(api_spec: dict) -> list[dict]:
    """api_spec：examples/users_api.json 读出来的接口描述。"""
    spec_text = json.dumps(api_spec, ensure_ascii=False, indent=2)
    user = (
        f"下面是目标接口的描述：\n```json\n{spec_text}\n```\n"
        "请为每个接口生成 3~6 条测试用例，normal/boundary/exception 都要覆盖。"
        "重点关注：登录鉴权（缺 token、错 token）、必填字段缺失、非法 id、"
        "金额 <= 0、重复用户名等场景。直接输出 JSON 数组。"
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]

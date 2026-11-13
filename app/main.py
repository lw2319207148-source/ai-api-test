"""靶子接口：一个简单的「用户 + 订单」系统，专门用来让 AI 生成的测试用例跑。

启动方式（在 ai-api-test 目录下执行）：
    uvicorn app.main:app --reload --port 8000

这是"被测对象"，不是项目主体。项目主体是：AI 根据 examples/users_api.json
里的接口描述，生成测试用例，再由 pytest 打这些接口。
"""
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="AI-Test 靶子接口", version="1.0.0")

# 内存数据库（进程重启就重置，只用于演示，不用真数据库）
USERS = {
    1: {"id": 1, "username": "alice", "role": "admin"},
    2: {"id": 2, "username": "bob", "role": "user"},
}
ORDERS = {}
_next_user_id = 3
_next_order_id = 1
TOKEN = "demo-token-123"


class LoginIn(BaseModel):
    username: str
    password: str


class UserIn(BaseModel):
    username: str = Field(..., min_length=1)
    role: str = "user"


class OrderIn(BaseModel):
    user_id: int
    item: str
    amount: float = Field(..., gt=0)  # 金额必须 > 0


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login")
def login(data: LoginIn):
    # 只演示逻辑：密码固定 123456
    if data.password == "123456":
        return {"token": TOKEN, "username": data.username}
    raise HTTPException(status_code=401, detail="用户名或密码错误")


@app.get("/users")
def list_users():
    return {"users": list(USERS.values())}


@app.get("/users/{user_id}")
def get_user(user_id: int):
    if user_id not in USERS:
        raise HTTPException(status_code=404, detail="用户不存在")
    return USERS[user_id]


@app.post("/users")
def create_user(data: UserIn):
    global _next_user_id
    if any(u["username"] == data.username for u in USERS.values()):
        raise HTTPException(status_code=409, detail="用户名已存在")
    user = {"id": _next_user_id, "username": data.username, "role": data.role}
    USERS[_next_user_id] = user
    _next_user_id += 1
    return user


@app.put("/users/{user_id}")
def update_user(user_id: int, data: UserIn):
    if user_id not in USERS:
        raise HTTPException(status_code=404, detail="用户不存在")
    USERS[user_id].update({"username": data.username, "role": data.role})
    return USERS[user_id]


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    if user_id not in USERS:
        raise HTTPException(status_code=404, detail="用户不存在")
    del USERS[user_id]
    return {"deleted": user_id}


@app.post("/orders")
def create_order(data: OrderIn, authorization: str = Header(None)):
    # 需要登录后拿到的 token 才能下单
    if authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="缺少或无效的 token")
    if data.user_id not in USERS:
        raise HTTPException(status_code=404, detail="用户不存在")
    global _next_order_id
    order = {"id": _next_order_id, **data.model_dump()}
    ORDERS[_next_order_id] = order
    _next_order_id += 1
    return order

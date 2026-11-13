# AI 生成测试用例 + 接口自动化执行

一个 Python 项目：给它一段**接口描述**，AI 自动生成测试用例（正常/边界/异常），
程序再把这些用例转成 pytest 接口测试，自动执行并输出 HTML 测试报告。

## 技术栈
- Python 3.11
- FastAPI（自己写的靶子接口：登录 / 用户 CRUD / 订单）
- DeepSeek V4（wb2api 反代，OpenAI 兼容接口）负责生成用例
- pytest + requests 执行测试
- pytest-html 生成报告

## 目录结构
```
ai-api-test/
├── app/                 # 靶子接口（被测对象）
├── generator/           # 用例生成（提示词 / 调 LLM / 校验输出）
├── runner/              # 用例转 pytest + 执行
├── examples/            # 接口描述示例 + 手写样例用例
├── main.py              # 入口：gen / run / check / analyze
├── requirements.txt
├── .env.example         # 密钥模板
└── README.md
```

## 快速开始（不用 LLM 也能先跑通）
1. 安装依赖：
   ```
   pip install -r requirements.txt
   ```
2. 终端 A 启动靶子接口：
   ```
   uvicorn app.main:app --reload --port 8000
   ```
3. 终端 B 用我手写的 10 条样例用例跑一遍：
   ```
   python main.py run examples/sample_cases.json
   ```
4. 打开 `reports/report.html` 看测试报告。
5. 如果有失败的用例，让 AI 帮你分析：
   ```
   python main.py analyze reports/failures.json
   ```

## 自检命令（推荐先跑）
```
python main.py check
```
会分别检查「LLM 网关」和「靶子接口」通不通，哪边不通提示哪边。

## 接入 LLM 生成用例
1. 复制 `.env.example` 为 `.env`，填入：
   - `LLM_BASE_URL`：wb2api 反代地址
   - `LLM_API_KEY`：密钥
   - `LLM_MODEL`：模型名（如 deepseek-v4-flash；留空则自动选第一个可用模型）
2. 生成用例：
   ```
   python main.py gen examples/users_api.json cases.json
   ```
3. 执行：
   ```
   python main.py run cases.json
   ```

## 常见问题
- **`[check] LLM 网关连不上`**：wb2api 网关一般跟着 WorkBuddy 之类的主程序启动，先把那个程序打开。
- **`[check] 靶子接口连不上`**：说明终端 A 的 `uvicorn` 没启动或端口被占。
- **`ModuleNotFoundError`**：先 `pip install -r requirements.txt`。
- **报告打不开/不存在**：程序会自动创建 `reports/` 目录，执行完再看。

## 路线图
- [x] M1 骨架 + 靶子接口 + 用例生成模块
- [ ] M2 用例转 pytest 并跑通（已可用样例用例验证）
- [x] M3 pytest-html 报告 + AI 分析失败原因（`main.py analyze`，待真实运行验证）
- [ ] M4 README 完善、演示、推 GitHub

## 项目亮点（面试可以这么说）
- **AI 不是摆设**：不是"调用个 API 就完事"，而是「接口描述 → 提示词约束 → AI 生成 JSON 用例 → 程序校验解析 → pytest 参数化执行 → HTML 报告 → AI 分析失败原因」的完整闭环。
- **能演示**：一条 `python main.py run examples/sample_cases.json` 就能出报告，不联网也能跑（样例用例兜底）。
- **工程细节**：`.env` 管密钥不进 Git、宽容解析 LLM 输出（防它吐 markdown/废话）、失败自动重试、Windows 路径兼容。
- **有被测对象**：自己写了 FastAPI 靶子接口（登录鉴权 / 用户 CRUD / 订单金额校验），知道测的是什么。

## 演示脚本（面试 3 分钟版）
1. 终端 A：`uvicorn app.main:app --reload --port 8000`
2. 终端 B：`python main.py run examples/sample_cases.json`，打开 `reports/report.html`，说明"这是手写样例，先证明执行链路通"。
3. `python main.py gen examples/users_api.json cases.json`，展示"AI 真生成了 N 条用例"。
4. `python main.py run cases.json`，展示 AI 用例跑出来的报告。
5. `python main.py analyze reports/failures.json`（若有失败），展示"AI 连失败原因都能帮分析"。

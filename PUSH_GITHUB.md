# 推送到 GitHub（M4 步骤，小白版）

> 在 `ai-api-test` 目录打开终端（PowerShell / CMD 都行），一条一条执行。

## 1. 初始化并提交
```
git init
git add .
git commit -m "AI 生成测试用例 + 接口自动化执行"
```

## 2. 在 github.com 上建仓库
- 登录你的 GitHub → 右上角 `+` → `New repository`
- 仓库名填 `ai-api-test`
- 选 Public 或 Private 都行（面试用建议 Public，README 和代码都能被看到）
- **不要勾选** "Add a README"（因为本地已有）
- 点 Create repository

## 3. 关联远程并推送
把下面这行的 `你的用户名` 换成你的 GitHub 用户名：
```
git branch -M main
git remote add origin https://github.com/你的用户名/ai-api-test.git
git push -u origin main
```

## 4. 检查密钥没泄露
- 打开 GitHub 网页上的仓库，确认**看不到** `.env` 文件（`.gitignore` 已把它排除）。
- 如果之前不小心提交过 `.env`，告诉我，我教你怎么从历史里删干净。

## 5. 给仓库补个一句话介绍
GitHub 仓库页面 → About → Description 填：
```
AI 生成接口测试用例 + pytest 自动执行 + HTML 报告 + AI 分析失败原因（FastAPI + DeepSeek）
```

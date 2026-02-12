# AI每日速递

每日自动推送AI领域最新资讯、论文精选和知识点解读到微信。

## 功能特点

- **📰 AI要闻**: 从多个国内源聚合，AI筛选5-7条有技术价值的新闻
- **📚 论文精选**: arXiv大模型相关论文，易懂版+专业版解读
- **💡 每日知识点**: 70+知识点按分类管理，60天内不重复，附带原理图
- **🤖 多模型支持**: 通义千问/DeepSeek等多模型自动切换

## 快速开始

### 1. 安装依赖

```bash
cd ai_daily_digest
pip install -r requirements.txt
```

### 2. 配置环境变量

**Windows:**
```cmd
set DASHSCOPE_API_KEY=你的通义千问API_KEY
set SERVERCHAN_SENDKEY=你的Server酱SENDKEY
python main.py
```

**Linux/Mac:**
```bash
export DASHSCOPE_API_KEY=你的通义千问API_KEY
export SERVERCHAN_SENDKEY=你的Server酱SENDKEY
python main.py
```

或者直接编辑 `config.yaml` 填入密钥。

### 3. 获取密钥

- **通义千问**: https://dashscope.console.aliyun.com/
- **Server酱**: https://sct.ftqq.com/ (微信扫码登录)

## GitHub Actions 自动运行（推荐）

让你的脚本在GitHub服务器上每天自动运行，不需要自己电脑开机。

### 步骤

1. **创建GitHub仓库**
   - 登录 GitHub，创建一个新的私有仓库（如 `ai-daily-digest`）

2. **推送代码**
   ```bash
   cd ai_daily_digest
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/你的用户名/ai-daily-digest.git
   git push -u origin main
   ```

3. **配置Secrets**
   - 进入仓库 → Settings → Secrets and variables → Actions
   - 点击 "New repository secret"，添加：
     - Name: `DASHSCOPE_API_KEY`，Value: 你的通义千问API Key
     - Name: `SERVERCHAN_SENDKEY`，Value: 你的Server酱SendKey

4. **修改推送时间（可选）**
   - 编辑 `.github/workflows/daily.yml`
   - `cron: '0 4 * * *'` 表示UTC 4:00（北京时间12:00）
   - 如需改为北京时间8:00，改为 `cron: '0 0 * * *'`

5. **手动测试**
   - 进入仓库 → Actions → AI Daily Digest
   - 点击 "Run workflow" 手动触发一次测试

### 定时说明

| cron表达式 | UTC时间 | 北京时间 |
|------------|---------|----------|
| `0 4 * * *` | 04:00 | 12:00 |
| `0 0 * * *` | 00:00 | 08:00 |
| `0 16 * * *` | 16:00 | 00:00（次日） |

## 本地运行

### 方式1：直接运行
```bash
python main.py
```

### 方式2：Windows任务计划
1. `Win + R` → 输入 `taskschd.msc`
2. 创建基本任务，每天12:00运行
3. 程序: `python`，参数: `D:\路径\ai_daily_digest\main.py`

## 配置说明

### 模型配置

```yaml
llm:
  models:
    - name: "deepseek-v3.1"  # 优先使用
      priority: 1
    - name: "qwen-plus"      # 备用
      priority: 2
```

模型会按priority排序，失败自动切换下一个。

### 新闻源

| 来源 | 类型 |
|------|------|
| 机器之心 | 国内RSS |
| 量子位 | 国内RSS |
| 新智元 | 国内RSS |
| 36氪AI | 国内RSS |
| AI科技评论 | 国内RSS |
| InfoQ AI | 国内RSS |

### 知识点分类

- 基础概念、模型架构、大语言模型
- 高效训练、RAG与检索、多模态
- 强化学习、Agent与推理、前沿技术

## 项目结构

```
ai_daily_digest/
├── .github/workflows/
│   └── daily.yml          # GitHub Actions配置
├── config.yaml            # 主配置文件
├── main.py                # 主程序
├── llm_generator.py       # LLM内容生成
├── knowledge_manager.py   # 知识点管理
├── sources/
│   ├── arxiv_fetcher.py   # arXiv论文
│   ├── news_fetcher.py    # 新闻聚合
│   └── image_searcher.py  # 图片搜索
├── prompts/               # Prompt模板
└── notifier/
    └── serverchan.py      # Server酱推送
```

## 常见问题

**推送失败？**
- 检查环境变量或config.yaml中的密钥

**GitHub Actions没运行？**
- 检查Actions是否启用（仓库Settings → Actions → General）
- 确认Secrets配置正确

**知识点重复？**
- 删除 `data/knowledge_history.json`

# Auto Content Bot — AI 写稿机器人

每天早上 8:00 自动抓数据 → AI 写文章 → 存到 GitHub。手机 1 分钟复制发布。

## 工作流程

```
每天早 8:00（GitHub Actions 自动）

  抓数据           →   AI 写文章        →   保存
  金价/天气          "老七"人设            GitHub 仓库
  微博热搜           反 AI 腔            自动提交
  历史上的今天       3种随机角度          output/ 目录
```

你每天只需：打开 GitHub → 复制文章 → 头条号 APP 粘贴发布（1 分钟）

## 项目结构

```
src/
  main.py              # 主流程编排
  writer.py            # DeepSeek AI 写作（"老七"人设）
  publisher.py         # 文章保存 + 自动提交
  config.py / utils.py # 配置和工具
  fetchers/
    gold_price.py      # 国际金价
    weather.py         # 天气 (wttr.in, 免费)
    history.py         # 历史上的今天 (Wikipedia)
    trending.py        # 微博/百度热搜
output/                # 文章输出（自动提交到 GitHub）

.github/workflows/
  daily-publish.yml    # 定时触发（早 8:00）
```

## 部署步骤

### 1. 注册头条号
- https://mp.toutiao.com → 注册 → 实名认证
- 开通「创作收益」（0 粉丝可用）
- 绑定支付宝提现

### 2. 注册 DeepSeek + 充值
- https://platform.deepseek.com → 注册
- 创建 API Key → 充值 30 元
- 定价 1 元/百万 tokens，每天消耗约 0.02 元

### 3. 配置环境
复制 `.env.example` 为 `.env`，填入 DeepSeek API Key：
```
DEEPSEEK_API_KEY=sk-your-key
```

### 4. 部署到 GitHub
```bash
git init && git add . && git commit -m "init"
git remote add origin https://github.com/你的用户名/auto-content-bot.git
git push -u origin main
```

### 5. 配置 GitHub Secret
Settings → Secrets → Actions → New secret:
- Name: `DEEPSEEK_API_KEY`
- Value: 你的 DeepSeek API Key

### 6. 触发测试
Actions → Daily Article Generator → Run workflow

## 日常使用

**每天早上起床后（1 分钟）：**
1. 打开 `https://github.com/你的用户名/auto-content-bot/tree/main/output`
2. 打开最新的 `_每日发布.txt`
3. 复制一篇文章 → 头条号 APP 点「写文章」→ 粘贴 → 发布
4. 重复 2-3 次

## 改进点（相比初始版本）

- **反 AI 腔**：设定了"老七"人设 + 禁用套话 + 随机写作角度
- **追热点**：接入微博/百度热搜，文章更有话题性
- **免下载**：文章自动提交回 GitHub，手机直接打开就能看
- **轻量**：移除了不可靠的浏览器自动化代码，保持简洁

## 成本预估

| 项目 | 金额 |
|------|------|
| DeepSeek 充值 | 30 元（够用 4 年+） |
| GitHub | 免费 |
| 头条号 | 免费 |
| 每天 API 消耗 | ~0.02 元 |

## 预估收入

| 阶段 | 月收入 |
|------|--------|
| 起步（1-3 月） | 2-6 元 |
| 积累（3-6 月） | 6-30 元 |
| 稳定（6 月+） | 30-150 元 |

# Auto Content Bot — AI 写稿机器人

每天自动：爬数据 → AI 写文章 → 保存。你只需 1 分钟复制粘贴发布。

---

## 工作流程

```
每天早上 8:00（GitHub Actions 自动运行）
    │
    ├── 抓取金价数据（免费 API）
    ├── 抓取天气预报（免费 API）
    ├── 抓取历史上的今天（Wikipedia 免费 API）
    │
    ├── 调用 DeepSeek 改写为文章
    │
    ├── 保存到 output/ 文件夹
    └── 打包为 daily-articles.zip
    
你起床后花 1 分钟：

    打开 GitHub → Actions → 下载今天文章
    → 复制内容 → 打开头条号APP → 粘贴发布
```

---

## 第①步：注册头条号 + 开通创作收益

**注册：**
1. 手机浏览器打开 https://mp.toutiao.com
2. 点击「注册」→ 用手机号注册
3. 选择账号类型：**个人**
4. 内容领域选「财经」或「生活」

**实名认证（必须）：**
1. 后台 →「设置」→「账号信息」→「实名认证」
2. 上传身份证正反面 + 人脸识别
3. 审核通常 1-24 小时

**开通创作收益（0 粉丝即可）：**
1. 后台 → 找「创作收益」或「收益中心」
2. 点击「开通」→ 同意协议
3. 绑定支付宝（满 1 元可提现）

---

## 第②步：注册 DeepSeek + 充值 30 元

1. 手机浏览器打开 https://platform.deepseek.com
2. 手机号注册 / 登录
3. 进「API Keys」→「创建 API Key」→ 复制保存
4. 进「充值」→ 支付宝 → 充 **30 元**
5. 记下 API Key

> 每篇文章约 2000 tokens，1 元 = 100 万 tokens，30 元够跑 4 年以上。

---

## 第③步：部署代码到 GitHub（需要一次电脑）

> 这步需要一台电脑（去网吧、借朋友的、或用公司电脑），只需要 15 分钟。

**3.1 安装依赖 + 测试**

在项目目录打开终端：

```bash
cd auto-content-bot

# 安装依赖
pip install -r requirements.txt

# 本地测试（看看能不能生成文章）
set DEEPSEEK_API_KEY=sk-你的key
python -m src.main
```

如果成功，`output/` 文件夹里会出现今天的文章。

**3.2 上传到 GitHub**

```bash
git init
git add .
git commit -m "init"
git branch -M main
git remote add origin https://github.com/你的用户名/auto-content-bot.git
git push -u origin main
```

**3.3 配置密钥**

1. 打开你的 GitHub 仓库 → Settings → Secrets and variables → Actions
2. 点「New repository secret」
3. Name 填：`DEEPSEEK_API_KEY`
4. Value 填：你的 DeepSeek API Key
5. 点 Add secret

**3.4 手动测试**

1. 仓库里点 Actions 标签
2. 左侧点「Daily Content Generation」
3. 右侧点「Run workflow」→「Run workflow」
4. 等黄色圆点变绿色 ✓
5. 点进去 → 拉到最下面 → Artifacts → 下载 `daily-articles.zip`
6. 解压，确认里面有文章

---

## 第④步：每天发布（手机操作，1 分钟）

**以后每天早上拿起手机：**

1. 打开 GitHub（手机浏览器或 GitHub APP）
2. 进入你的仓库 → Actions
3. 点最新一次运行 → 拉到底部 Artifacts → 下载 `daily-articles`
4. 解压文件 → 打开 `2026-05-27_每日发布.txt`
5. 复制第 1 篇文章的标题和正文
6. 打开**今日头条 APP** → 点「+」→「写文章」
7. 粘贴标题和正文 → 点「发布」
8. 回到第 5 步，发第 2 篇、第 3 篇

这一步是唯一需要手动的地方，熟练后不到 1 分钟搞定。

---

## 成本与收益

| | 金额 |
|---|---|
| DeepSeek 充值（一次性） | 30 元 |
| GitHub | 免费 |
| 头条号 | 免费 |
| 每天消耗 | 约 0.02 元 |
| **预估日收入（冷启动）** | **0.05 - 0.5 元** |
| **预估月收入（积累后）** | **30 - 150 元** |

---

## 为什么头条号不用 API 了？

头条号开放平台需要**企业营业执照**才能申请 API 密钥，个人创作者无法获取。所以采用「自动生成 + 手动发布」的模式。

好处是：
- 每天发布前你可以扫一眼内容质量，避免生硬的 AI 文被平台限流
- 可以根据热点随时调整 prompt
- 省去找 API 的折腾时间

---

## 每周维护（2 分钟）

1. 打开 GitHub 仓库 → Actions 标签
2. 看看最近 7 天的运行有没有红色 ✗
3. 有红色 → 点进去看日志，通常原因：
   - DeepSeek 余额不足 → 充值
   - 数据源暂时不可用（隔天会自动恢复）

---

## 提示

- 每天发布时，**不要标题和正文完全照搬**——偶尔微调几个字，让文章看起来更像真人写的
- 如果某天数据抓取失败（比如金价 API 挂了），系统会自动跳过该类型，不影响其他文章
- `output/` 文件夹里的文章会保留在 GitHub Actions 里 90 天，随时可以下载

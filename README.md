# qiuyiwu-skills

邱懿武的 Claude Code 自定义 skill 库。任何新机器 `git clone + ./install.sh` 就能用。

## 包含 3 个 skill

| Skill | 干什么 |
|-------|--------|
| `web-analytics` | 给网站接百度统计 + GA4 + GTM，含 7 个核心事件埋点 |
| `seo-geo-optimizer` | SEO + GEO（让大模型能读到）+ 速度优化全套（8 个 Python 脚本 + 模板 + 实战经验补丁）|
| `xiaomi-tts` | 中文文本转语音（小米 MIMO API），茉莉知性讲师默认音色 |

## 一键安装

```bash
git clone https://github.com/<你的用户名>/qiuyiwu-skills.git ~/qiuyiwu-skills
cd ~/qiuyiwu-skills
./install.sh
```

`install.sh` 用 **symlink** 把仓库里的 skill 链到 `~/.claude/skills/`，以后 `git pull` 自动更新。

## 卸载

```bash
cd ~/qiuyiwu-skills
for d in skills/*/; do
  rm -f ~/.claude/skills/"$(basename "$d")"
done
```

## 用法

不需要记关键词。任何 Claude Code 会话里直接说出意图即可，skill 描述里写了大量触发词，Claude 会自动识别：

| 你说 | 触发 |
|------|------|
| 「给这个站接百度跟 GA4」 | `web-analytics` |
| 「做下 SEO，让百度收录我」 | `seo-geo-optimizer` |
| 「帮我把这段话变成音频」 | `xiaomi-tts` |
| 「让 ChatGPT 能引用我」 | `seo-geo-optimizer`（GEO 章节）|

## 需要的环境变量

按需设置（不用都设）：

```bash
# xiaomi-tts
export MIMO_API_KEY="sk-xxxxxxxx"

# seo-geo-optimizer 的 baidu_push.py
export BAIDU_SITE="https://你的域名.com"
export BAIDU_PUSH_TOKEN="百度站长平台拿"
```

放 `~/.zshrc` 或 `~/.bashrc` 永久生效。

## 跨机器同步流程

```bash
# 在源机器（你常用的 Mac）
cd ~/qiuyiwu-skills
git add -A
git commit -m "update"
git push

# 在目标机器（新笔记本 / 工作站）
git pull       # 自动拉新版（symlink 不需要重装）
```

如果只是修改了 skill 内容（编辑 SKILL.md / 脚本），git pull 后立刻生效。
如果新增了 skill 目录，pull 完再跑一次 `./install.sh`。

## 安全

- 仓库里**没有任何 API key、密码、服务器地址**
- 所有 secrets 走环境变量
- 推荐放**私库**（GitHub Private / Gitee 私库 / 自建 Gitea）
- 不建议公开 — skill 里有一些跟邱懿武项目相关的偏好（音色选择、写作风格示例等）

## 不包含的 skill

`qiuyiwu-deploy` 没打包进来 —— 里面有服务器 IP 和密码，敏感信息，仅本机使用。

## 后续可加的 skill 槽位

```
skills/
  ├── web-analytics/        ✓ 已有
  ├── seo-geo-optimizer/    ✓ 已有
  ├── xiaomi-tts/           ✓ 已有
  ├── <new-skill>/          ← 直接放新目录进来，下次 install.sh 自动接管
```

新建 skill 模板见 `~/.claude/skills/anthropic-skills:skill-creator/`（如果装了 skill-creator）。

## SkillOps 技能归档

[打开整库索引与版本说明](skillops-library/README.md)。

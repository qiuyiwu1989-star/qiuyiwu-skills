# 邱懿武的 AI 技能库

收录邱懿武在产品研究、教学设计、内容创作和项目协作中使用的 Agent 技能。你可以浏览技能的 `SKILL.md`、配套模板和参考资料，也可以按版本查看历史内容。

[浏览 SkillOps 技能归档](skillops-library/) · [查看完整索引](skillops-library/index.json) · [安装 Claude Code 技能](#安装-claude-code-技能)

## 从哪里看起

| 技能 | 适合什么任务 |
| --- | --- |
| [用户价值叙事 1.0.1](skillops-library/skills/user-value-storytelling--b20a02ec-34b0-4258-ac6e-d2899e77b78a/versions/1.0.1/SKILL.md) | 用具体场景和可验证的证据讲清产品价值 |
| [JTBD × KANO 需求挖掘与排序 1.0.0](skillops-library/skills/jtbd-kano-discovery--2128b958-2c96-4244-a7e1-9dd4eb1281cc/versions/1.0.0/SKILL.md) | 从访谈提炼需求、设计问卷、根据答卷确定优先级 |
| [有谱 v2](skillops-library/skills/youpu--74f0bfd356f13126/versions/2/SKILL.md) | 记录项目现状、决定和下一步，方便换人或换 Agent 接手 |

[`skillops-library/`](skillops-library/)是 SkillOps 的一份版本快照，包含 **368 个技能、404 个可读版本和 1,970 个文件**。8 个插件的名称、ID 和版本也可在索引里查到，完整插件包由 SkillOps 管理。

## 安装 Claude Code 技能

根目录的 [`skills/`](skills/) 提供三个可用安装脚本接入的技能。

| 技能 | 用途 |
| --- | --- |
| [`web-analytics`](skills/web-analytics/) | 为网站接入百度统计、GA4 和 GTM |
| [`seo-geo-optimizer`](skills/seo-geo-optimizer/) | 检查搜索收录、AI 可读性和页面性能 |
| [`xiaomi-tts`](skills/xiaomi-tts/) | 使用小米 MiMo 将中文文本转成音频 |

```bash
git clone https://github.com/qiuyiwu1989-star/qiuyiwu-skills.git ~/qiuyiwu-skills
cd ~/qiuyiwu-skills
bash install.sh
```

安装脚本会把这三个目录链接到 `~/.claude/skills/`。同名的实体目录会先备份，同名符号链接会重新指向本仓库。安装后新开一个 Claude Code 会话即可使用。更新现有技能可在仓库目录运行 `git pull`。使用 MiMo 语音或百度链接提交功能时，请按各技能说明在本机配置所需的环境变量。

如需使用归档中的技能，可先在索引中选择版本，再查看该版本的 `SKILL.md` 和附件，按目标客户端的方式安装对应版本目录。

## 来源与授权

归档中的版本号、文件列表和源端摘要见各技能的 `index.json`。复用或再分发时，请查看相应技能和附件声明的来源与授权。

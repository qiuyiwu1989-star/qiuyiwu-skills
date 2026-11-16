# video-to-prompt

Openclaw skill — 将本地桌面录屏转换为结构化 CUA 提示词。

外部用户只需 `SKILL.md`；本文件面向维护者。

## 源码结构

此 skill 目录（`skills/video-to-prompt/`）只包含 **bootstrap shim**：
`SKILL.md` / `README.md` / `scripts/video-to-prompt.sh`。

实际运行时（bin / lib / tools / prompts / config）位于 `runtime/agents/video-to-prompt/`，
由独立的 Node 包维护。生产部署 SoT 是本仓 `scripts/package/package.sh`（详见 CLAUDE.md
`scripts/package/` 段），统一打包 cua / vtp / vtp-runtime / skills / plugin/skill-switch
为 `arkclaw-xua-plugin-<YYYY.M.D>.tgz` 上传 TOS。

## 触发方式

```bash
# 对话化
bash scripts/video-to-prompt.sh <video-path>

# 信号化（插件使用）
bash scripts/video-to-prompt.sh --from-signal <<'EOF'
{"skill":"video-to-prompt","payload":{"videoPath":"<path>","outputDir":"<dir>"}}
EOF
```

## 运行时契约

- 输入：本地绝对路径视频（拒绝 URL）
- 模型配置：`/root/.openclaw/openclaw.json`
- 三路径分派：`supportsVideo` → 短视频 inline base64 或长视频切片预摘要 / 仅 `supportsImage` → 关键帧 `extract_frames_range` / 二者均无 → 乐观放行（Ark API 报错时发 `preflight_failed` + `<computer-handoff />`）
- 输出：`<outputDir>/prompt.json` + `meta.json` + `steps.jsonl`
- 事件：stdout 单行 JSON

环境变量见 `SKILL.md`。

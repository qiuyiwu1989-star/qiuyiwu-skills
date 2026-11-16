---
name: video-to-prompt
description: "Convert a local desktop recording (MP4 / MKV) into a structured executable operation prompt. Use this skill when the user asks to generate a prompt from a recorded video / screen recording. Trigger keywords: 视频、录屏、录制、生成提示词、video、record、extract-prompt."
argument-hint: "[video-absolute-path]"
arguments: videoPath
allowed-tools: Bash(ffmpeg *) Bash(ffprobe *) Bash(node *) Bash(bash *)
metadata:
  openclaw:
    os: [linux]
    requires:
      bins: [ffmpeg, ffprobe, node]
      config: [agents.defaults.model.primary]
---

# Video to Prompt

将本地桌面录屏转换为结构化可执行操作提示词。

## 命令

```bash
bash skills/video-to-prompt/scripts/video-to-prompt.sh <absolute-video-path>
```

## 输入

- 本地绝对路径，MP4 或 MKV
- 不接受 URL
- 默认允许 `${OPENCLAW_WORKSPACE}` 与 `/tmp`

## 输出

产物目录：

- Plugin spawn 路径（常规）：`$VTP_HOME/runs/<id>/prompt`（plugin 显式注入 `CUA_VTP_OUTPUT_DIR`）
- 裸 shell 调用：`$VTP_HOME/runs/<id>`（无 `/prompt` 后缀，由 `video-to-prompt.sh` 的默认 fallback 决定）

| 文件           | 内容                                                            |
| -------------- | --------------------------------------------------------------- |
| `prompt.json`  | 结构化 executable operation prompt                              |
| `meta.json`    | 状态、模型、时间、错误                                          |
| `steps.jsonl`  | 每步记录                                                        |
| `events.jsonl` | per-run 事件协议流(进度 / phase / 错误事件,`events` RPC 数据源) |

`prompt.json` 字段：`taskName / description / preconditions / steps / expectedResult / confidence / source / usage / createdAt`。

## 失败标签

| 场景                           | 处理                                               |
| ------------------------------ | -------------------------------------------------- |
| 模型不支持图像/视频输入        | preflight 失败，emit `preflight_failed` 事件后退出 |
| 二进制缺失 / 路径非法 / 锁冲突 | 直接说明原因，skill 退出                           |

## 环境变量

| 变量                               | 默认                                                                                     | 说明                                                                                             |
| ---------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `CUA_VTP_RECORDING_ID`             | 自动生成                                                                                 | 录制 ID                                                                                          |
| `CUA_VTP_OUTPUT_DIR`               | `$VTP_HOME/runs/<id>/prompt`（plugin 注入） / `$VTP_HOME/runs/<id>`（裸 shell fallback） | 产物目录                                                                                         |
| `CUA_VTP_OUTPUT_ROOT`              | `/root/.vtp`（plugin spawn 时注入为 `$VTP_HOME/runs`）                                  | runtime 写 `prompt.json` / `meta.json` 前的物理根目录限制；`CUA_VTP_OUTPUT_DIR` 必须 realpath 落在此根内 |
| `CUA_VTP_LANGUAGE`                 | `zh-CN`                                                                                  | 输出语言                                                                                         |
| `CUA_VTP_MAX_STEPS`                | `20`                                                                                     | ReAct 最大轮数（脚本恒传 `--max-steps`，默认 20；裸 `vtp run` 不带 flag 时 runtime fallback 50） |
| `CUA_VTP_FRAMES_QUOTA`             | `200`                                                                                    | extract_frames_range 的项目级帧上限（runtime fallback；脚本不传 `--frames-quota`）               |
| `CUA_VTP_DELETE_VIDEO_ON_SUCCESS`  | `false`                                                                                  | 成功后删视频（plugin spawn skill 时显式注入 `false`，二期保留本地 mp4 7 天）                     |
| `CUA_VTP_SESSION_KEY`              | （空）                                                                                   | 透传到 prompt.json 元数据，便于关联会话                                                          |
| `CUA_VTP_ALLOWED_ROOTS`            | `/tmp:${OPENCLAW_WORKSPACE}:${VTP_HOME}`                                                 | 接受的视频路径前缀（冒号分隔），preflight 校验                                                   |
| `CUA_VTP_VIDEO_MAX_SINGLE_SEC`     | `60`                                                                                     | 超此时长走 chunked summarize 路径                                                                |
| `CUA_VTP_VIDEO_CHUNK_SEC`          | `40`                                                                                     | 长视频切片粒度                                                                                   |
| `CUA_VTP_VIDEO_CHUNK_MAX_BYTES`    | `67108864`                                                                               | 单 chunk inline base64 大小上限（64MB），含短视频 inline 守卫                                    |
| `CUA_VTP_RUN_DEADLINE_MS`          | `1800000`                                                                                | 整次 analyze 运行时上限（30 min）；`0` 关闭（生产不建议）                                        |
| `CUA_VTP_FFMPEG_BIN`               | `ffmpeg`                                                                                 | zoom_region 等抽帧子流程的 ffmpeg 路径                                                           |
| `CUA_VTP_FFPROBE_BIN`              | `ffprobe`                                                                                | 同上，ffprobe 路径                                                                               |
| `CUA_VTP_BASELINE_ENABLED`         | `true`                                                                                   | PERCEPTION baseline 预读（均匀抽帧 + 批量 OCR）总开关；`false` 短路整段                          |
| `CUA_VTP_BASELINE_MAX_FRAMES`      | `20`                                                                                     | baseline 抽帧上限                                                                                |
| `CUA_VTP_BASELINE_UNIFORM_COUNT`   | `8`                                                                                      | baseline 均匀采样帧数                                                                            |
| `CUA_VTP_BASELINE_SCENE_THRESHOLD` | `0.1`                                                                                    | baseline 场景切换检测阈值                                                                        |
| `CUA_VTP_BASELINE_OCR_CONCURRENCY` | `6`                                                                                      | baseline 批量 OCR 并发数                                                                         |
| `CUA_VTP_BASELINE_TIMEOUT_MS`      | `1200000`                                                                                | baseline 阶段总超时（20 min）                                                                    |
| `CUA_VTP_CONFIG_PATH`              | `$VTP_HOME/config/local.json`                                                            | local 配置覆盖路径                                                                               |
| `VTP_HOME`                         | `$HOME/.vtp`                                                                             | Runtime 部署根（可被 `api.config.videoToPrompt.vtpHome` 覆盖）                                   |
| `VTP_RUNTIME_DIR`                  | （未设）                                                                                 | 强制覆盖 runtime 目录的最高优先级（debug 时用）                                                  |
| `OPENCLAW_WORKSPACE`               | `$HOME/.openclaw/workspace`                                                              | Workspace 根                                                                                     |

### OTel 可观测性 env（二期）

plugin / runtime 启动时初始化 OTel SDK（`observability/otel.ts`），trace/metric 走 OTLP collector。collector 不可达时 fail-open（导出失败静默吞，不影响 analyze 主流程）。

**端点配置驱动（对齐 CUA `config.otel.endpoint` 风格）**：collector 端点的单一来源是 plugin configSchema 的 `videoToPrompt.otelEndpoint`——**单端点同时服务 trace + metric**（OTLP proto exporter 自动追加 `/v1/traces`、`/v1/metrics`）。plugin 读它初始化自身 OTel，并写入 `OTEL_EXPORTER_OTLP_ENDPOINT` 进程环境变量；runtime SEA 全量继承 env 自动接收。下表 env 是显式覆盖 / 回落通道。

| 变量                                  | 默认                                                   | 说明                                                                                                                                                                                                  |
| ------------------------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CUA_VTP_OTEL_ENDPOINT` | （回落 `OTEL_EXPORTER_OTLP_ENDPOINT`）| OTLP collector 端点的显式覆盖（`CUA_VTP_*` 命名空间，trace + metric 共用）。两者都未设时 OTel SDK 默认连 `http://localhost:4318` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | （由 plugin 按 configSchema.otelEndpoint 写入）| OTel 标准端点 env，作为 `CUA_VTP_OTEL_ENDPOINT` 的回落；configSchema 驱动的传播通道 |
| `OTEL_CAPTURE_MESSAGE_CONTENT`        | `false`                                                | 仅控制 OpenAI auto-instrumentation 是否捕获**完整** LLM message（`true` 时写入 span，隐私敏感，生产默认关）。注：手动 `agent.llm` span 始终上报**截断后**（≤8KB）的 prompt/response，不受此 flag 控制 |
| `VTP_VERSION`                         | `0.0.0`                                                | 上报到 span 的 `service.version` 资源属性                                                                                                                                                             |
| `VTP_TRACE_DIR`                       | （未设）                                               | 仅本地 DEV 调试：turn-recorder dump 每 turn 的 `turn-NNN.json`（须绝对路径才生效）                                                                                                                    |

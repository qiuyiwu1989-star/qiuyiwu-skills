---
name: doubao-clone-tts
description: 克隆声音豆包语音配音。使用豆包双向流式 TTS，以邱懿武授权的本人克隆音色生成中文旁白、试听和原始字幕事件。用户要求豆包配音、qiuyiwu 音色或 S_r9pl2DBW1 时使用。
---

# 克隆声音豆包语音配音

默认音色 `S_r9pl2DBW1`，用户 `qiuyiwu`。2026-11-05 实测成功。不要自行创建或训练新音色。

## 已确认的默认配音预设

用户于 2026-11-05 要求保留《假如万物有 AI》使用的参数。后续未另行指定时沿用：

| 项目 | 默认值 |
| --- | --- |
| 服务 | 豆包双向流式 TTS |
| 本人克隆音色 | `S_r9pl2DBW1` |
| 用户标识 | `qiuyiwu` |
| 语速 | `speech_rate=15`（加快 15%） |
| 模型 | `seed-tts-2.0-standard` |
| 资源 ID | `seed-icl-2.0` |
| 输出格式 | MP3，24000 Hz |
| 字幕事件 | `enable_subtitle=true`，保留 `.events.json` |
| 音高、音量、情绪 | 未显式设置，沿用服务默认，不另行添加效果 |

语速在 TTS 请求中设置一次；不要再对已加速音轨叠加后期变速。用户最新明确将默认语速由 10% 改为 15%，以此为准。已确认音色与参数的续作可直接沿用，无需每次重复试听。仅增加插画、镜头或调整剪辑时，复用现有音轨和实际字幕时间，不重新生成 TTS；只有旁白或声音要求改变时才重新合成受影响的段落并重新对齐。

## 调用

Python 环境：`/Users/qiu/.local/share/doubao-tts/venv/bin/python`（依赖 websockets）。

```sh
/Users/qiu/.local/share/doubao-tts/venv/bin/python /Users/qiu/.codex/skills/doubao-clone-tts/scripts/synthesize.py --input /absolute/narration.txt --output /absolute/voice.mp3 --rate 15
```

输入为纯旁白，不含 Markdown、镜头编号和导演说明。默认语速参数 15（加快 15%）；用户已明确更新此默认值，替代之前的 10%。0 为原速。首次使用新音色或新参数时先生成短试听；已确认的默认预设直接按用户范围制作。长篇按幕拆分，保留原文与各幕实际音频时长。

凭据从 `DOUBAO_API_KEY` 或 `~/.config/doubao-tts/credentials.json` 的 `api_key` 读取。私有文件权限须为 0600；禁止打印凭据、放入命令行参数、技能、项目、提交或日志。不得覆盖用户已有凭据，除非明确更新。

## 协议与结果

- WebSocket：`wss://openspeech.bytedance.com/api/v3/tts/bidirection`
- 认证：`X-Api-Key`；资源：`seed-icl-2.0`。
- 模型：`seed-tts-2.0-standard`；MP3，24000 Hz。
- 开启 `enable_subtitle`，原始非音频事件保存为同名 `.events.json`。
- `protocols.py` 来自官方文档附带的 Python 协议示例；不启用其调试日志。
- 遇到鉴权、额度、音色权限错误，报告脱敏错误并停止，勿反复计费重试。

## 验收与视频接入

用 ffmpeg 完整解码检查音频；核对音色 ID、旁白和参数，不以文件存在替代验收。最终提供可播放的本地 MP3。

字幕事件未必返回完整时间；先检查实际事件，不得声称已有字幕。若无可用字幕时间，用 ASR/强制对齐与原稿生成 SRT。替换旁白后必须重新对齐字幕与镜头，不能沿用旧音轨时间戳。保留插画原始标题、完整构图，不以截图裁切代替重绘。

官方文档：https://docs.volcengine.com/docs/doubao-voice/bidirectional-streaming-text-to-speech-websocket?lang=zh

本次实测返回 event 364 的逐字全局秒级 `startTime/endTime`。可运行 `python3 scripts/subtitles.py /absolute/voice.events.json` 生成 SRT（每条约14字）；长段落还需语义断句与人工抽查。该工具只适用于单会话全局时间事件，多幕合并需加各幕音轨偏移。

## 讲述节奏与读音

- 速度快但要有停顿：故事动作紧凑，转折、追问与结论留出消化时间。先用自然标点和段落控制；需要精确停顿时在后期插入静音，并更新后续全部时间戳。不得把未验证的情绪、重音或停顿标签当作接口功能。
- 忠于用户确认的旁白与第一人称。获准润色时拆长句、减少书面连接词，保留原意；不要为了配音擅改观点或标题。
- 项目内维护读音约定，覆盖AI、AGI、FDE、人名及多音词。合成前先听关键读音；如需替换口语读法，保存“正式原文—合成文本”的映射，字幕保留正式文字，不能机械按字符位置套时间。
- 跨段落试听声线、音量和句尾，检查是否截字、重复或异常停顿。必要时在合并后统一响度，避免逐段归一化造成音量跳变；记录实际处理，不随意增加变调、混响或背景音乐。
- 保存脱敏的实际合成参数与处理记录（音色、模型、资源、speech_rate、采样率、格式、文本版本、音频时长、后期变速/静音/响度处理），不记录认证头。默认值不能冒充旧音频的实测参数。
- 若仅补图，直接用现有音轨的实际时长和字幕定位镜头；无需为每个镜头分别合成一句，以免声线与韵律割裂。

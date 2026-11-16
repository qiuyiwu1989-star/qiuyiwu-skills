---
name: media-transcript
description: 把一条视频/音频链接（抖音为主，可扩展 B站/视频号/小宇宙）变成「可用的内容资产」：无水印原视频 + 毫秒级逐字稿(SRT) + 读后总结。当用户发来抖音/视频链接并要求"转写/转录/提取内容/读一下这个视频/总结这个视频/保存这个视频"时使用。也适用于用户说"帮我读下这个视频讲什么"。输出三件套：source.mp4 / transcript.txt+srt / 总结.md。
id: fande/media-transcript
---

# 媒体转录（Media Transcript）

把一条视频链接，变成**可以沉淀的内容资产**。核心产出三件套：

| 资产 | 文件 | 用途 |
|------|------|------|
| **原视频** | `source.mp4`（无水印） | 留存 / 二次剪辑 |
| **逐字稿** | `transcript.txt`（毫秒时间轴）+ `transcript.srt` | 阅读 / 对轴 / 导入剪映 |
| **读后总结** | `<slug>.md` | 归档到 vault（reading-archive 契约） |

> 授权归属：范德 CEO 直接调用。属于 vault「内容资产」能力族，与 `reading-archive`（提炼归档）、`video-editor`（后期）协作。

## 触发场景

- "读一下这个视频 / 这个视频讲了啥 / 帮我总结这个视频"
- "转写 / 转录 / 提取字幕 / 把这条抖音内容弄出来"
- 用户直接甩一条抖音分享链接（`v.douyin.com/xxx`）
- "保存这个视频 / 把原视频存下来"

## 一条龙流程

### 首选：`ingest.sh`（到"待写总结"为止）

```bash
bash skills/media-transcript/scripts/ingest.sh "<链接>" <slug>
```

自动完成：下载无水印 mp4 → 抽音 → 转录（毫秒+SRT）→ 上传 COS → 生成 1 年签名直链 → 在 `vault-staging/video/` 搭好归档 md 骨架。**机械部分全自动，人/LLM 只需填总结 + 校专有名词，然后 publish。**

> ⚠️ **slug 必须 `YYYY-MM-DD-<slug>` 前缀**（否则 `validate-output.py` 报错、publish 会不一致）。ingest.sh 不自动加日期前缀，请手传如 `2026-10-11-apple-sociology-iphone-moment`。

### 分步（调试用）

```bash
bash skills/media-transcript/scripts/transcribe.sh "<链接>" [输出目录]
```
默认输出到 `/tmp/media-transcript/<aweme_id>/`：`meta.json` / `source.mp4` / `audio.wav`（转完自动删，`--keep-audio` 保留）/ `transcript.txt` / `transcript.txt.srt`。

**分工**：
- `scripts/douyin.py` — 解析**抖音/TikTok**链接 → 无水印 mp4 直链 + 元数据（走 api.douyin.wtf，标准库）
- `scripts/xhs.py` — 解析**小红书**链接 → 无水印 mp4 直链 + 元数据（读分享页 `__INITIAL_STATE__`）
- `scripts/transcribe.sh` — 按域名自动分流到对应解析器 → 下载 → 抽音 → 调 transcribe.py（带重试、转完清 wav）
- `scripts/transcribe.py` — faster-whisper 转录，输出 `hh:mm:ss.mmm` 时间轴 + 标准 SRT
- `scripts/ingest.sh` — 上面的一键封装

## Token 成本（重要）

**只有第 5 步（读逐字稿→写总结）烧 token，其余全本地免费。** STT（最重的一步）用本地 whisper，0 token。

`消耗 ≈ 逐字稿 token × 3`。实测 19:48 视频：逐字稿 ~8k token ⇒ 一进一出约 10k–16k token。

## 输出格式

`transcript.txt`（毫秒级）：
```
[00:00:00.000-00:00:03.780] 现代大学制度所带来的真正的阶级区分
[00:00:03.780-00:00:07.100] 并不只是只有少数人能够进入精英大学
```
`transcript.srt`：标准 SRT，可直接导剪映 / Arctime / Premiere。

## ⚡ 第一步铁律（2026-10-19 新增）：先找现成文字稿，再谈转写

**转写是最后手段，不是第一手段。** ASR 又慢又烧算力（2h14m 音频 CPU 上要 1-2 小时）。**任何音频/视频，先花 30 秒查有没有官方/现成文字稿**——播客（RSS）、YouTube、B站、腾讯新闻几乎都可能有。

**播客（最典型）**——官方 RSS 里常有 `podcast:transcript` 标签：
1. 用 iTunes Lookup 找 feed：`https://itunes.apple.com/search?term=<播客名>&entity=podcast` → 拿 `feedUrl`
2. 拉 RSS，在对应 `<item>` 里找 `<podcast:transcript url="...">`
3. 直接下那个 URL（常见 `.../transcript.txt`、`.vtt`、`.srt`、`.json`）——**纯文本，零 ASR**

> 实测（2026-10-19）：Cheeky Pint《Muse Wonder: Zuckerberg and Wang's $100B AI》2h14m → RSS `https://feeds.transistor.fm/cheeky-pint-with-john-collison` → `<podcast:transcript url="https://share.transistor.fm/s/bb7b9a51/transcript.txt">` → 151KB 官方全文，**秒取，省了一次 2 小时 ASR**。

**判断顺序**：① RSS/页面有 transcript → 直接用；② 有字幕文件（srt/vtt）→ 直接用；③ 都没有 → 才下音频跑 whisper。

---

## 平台支持

| 平台 | 取流方式 | 稳定性 |
|------|---------|--------|
| 抖音 / TikTok | `api.douyin.wtf` 解析服务（demo 账号） | ✅ 较稳（可备多 provider） |
| 小红书 | 分享页 HTML 内嵌 `__INITIAL_STATE__` → `video.media.stream[].masterUrl` | ⚠️ **脆弱**：`xsec_token` 有时效、页面结构变更会断、无反爬后备 |
| 视频号 | **本机无解**（见坑 #16）；变通：找**同名内容在腾讯新闻/腾讯视频的镜像**，用 yt-dlp 下载 | ⚠️ 依赖“有镜像” |
| **播客（RSS）** | **先查 `podcast:transcript` 标签拿官方文字稿**（见上「第一步铁律」）；确认没有才下 mp3 转写 | ✅ 有稿则零成本 |

### 视频号专用说明（2026-10-15 实测）

**视频号分享链（`https://weixin.qq.com/sph/xxxx`）在本机拿不到视频流**：
- 官方接口 `POST /finder-preview/api/feed/get_feed_info`（shortUri/exportId）**只回元数据**（作者/文案/封面/计数），**不含 h264/h265 视频地址**
- 视频流是 ISAAC 流密码加密的：真链 = `objectDesc.media[0].url + media[0].token`，前 **131072 字节**用 `media[0].decodeKey` 解密（算法见 `ltaoo/wx_channels_download` 的 `pkg/scraper/wxchannels/decrypt.go`）
- 网页版 `finder-preview` 设计上「只给浏览」→ DOM 里**从不出 `<video>`**，无头浏览器也抓不到流

**三条可行路径**（本机只能走 ②）：
1. 用户在微信里保存/转发源文件
2. **找同名镜像**：视频号内容常同步到**腾讯新闻**（`news.qq.com/rain/a/...`，页内 blob 播放）或**腾讯视频**。腾讯新闻页里的 `vid`（如 `f12940fpl3o`）可用 **yt-dlp 下 `https://v.qq.com/x/page/<vid>.html`** ✅ 实测成功
3. 本机跑 `wx_channels_download`（需微信客户端+代理，非无头服务器能独立完成）

> 实测案例：`AmVE7z9wuS`（超级创新者·猫不白）→ 腾讯新闻镜像 `20261014V0BPYO00` → vid `f12940fpl3o` → yt-dlp 下载 5:26 视频 → whisper 转写 291 段。

**小红书注意**：① 链接里的 `xsec_token` **会过期**，拿到链接要尽快抓，别囤；② 目前只有"读 HTML"这一条路，没有稳定解析服务做 Plan B；③ 抓取时会带 iPhone UA + `Referer: xiaohongshu.com`，视频流用 Range 请求直下（无水印）。

## 模型（持久化，勿重下）

- 位置：`~/.openclaw/models/faster-whisper-medium/`（含 `model.bin`，约 1.5G）
- 来源：ModelScope `pengzhendong/faster-whisper-medium`（**不是** huggingface）
- 环境变量可覆盖：`MODEL_DIR=/path/to/model`

## 归档（用户确认：目标是 qiuyiwu.com 的「视频档案」集合）

一条龙产出后，落三处：

1. **读后总结（提炼稿）→ vault/reading**：走 `reading-archive` 技能。
2. **原视频 + 三件套 → COS（大文件）**：`~/.cos.conf` → 桶 `qiuyiwu-1359505647`（ap-nanjing，私有），路径 `video-archive/<slug>/`。
3. **站上「视频档案」集合 → `bash scripts/publish-video.sh <slug>`**：
   - md 源放 `vault-staging/video/<slug>.md`（含字段：日期/来源/讲者/信源层级/标签/一句话/时长/视频/逐字稿）
   - 伴生 `<slug>.transcript.txt` + `.srt`（同目录）
   - 「视频」字段填 COS 签名直链（`coscmd signurl ... -t 31536000`，1 年）
   - 产物上站：https://qiuyiwu.com/vault/video/

> 站点服务 `/opt/agent-vault`（systemd `agent-vault.service`，127.0.0.1:5095）有集合白名单 `target()`；`video` 已加入（2026-10-11）。新集合需同步改白名单。
> 本地 mv 大文件到 `~/.openclaw/media/video-archive/<slug>/`（git 外）。

## 十一个坑（都踩过，记牢）

1. **yt-dlp 拿不到抖音**：报 `Fresh cookies (not necessarily logged in) are needed`。**别死磕 yt-dlp**，直接走解析 API。
2. **huggingface.co 在本机不通**（Errno 101 / 超时）。faster-whisper 默认去 HF 下模型 → 必挂。**必须走 ModelScope**，用 `--model-dir` 指向本地目录。
3. **浏览器工具在本机不可靠**（`browser action=start` 超时）。不要靠浏览器抓抖音。
4. **解析 API 用 demo 账号**：`GET /api/v1/auth/demo` 拿 demo 用户名密码 → `POST /api/v1/auth/login` 换 token。端点：`GET /api/v1/douyin/video?aweme_id=<id>`（首次常返回 `202 + task_id`，需轮询 `/api/v1/tasks/<id>`）。
5. **一定要选 `format=="mp4"` 且 `watermark==false` 的流**（streams 里混着 dash/带水印）。
6. **短链要先展开**：`v.douyin.com/xxx` → 用 HTTP 重定向拿真实 URL，再提 `aweme_id`。
7. **磁盘紧张（本机常 95%）**：`source.mp4` 和 `audio.wav` 别留双份；`audio.wav` 转完即可删。模型放 `~/.openclaw/models`（别塞进 git 跟踪的 workspace）。
8. **中文转写要 `language="zh"` + `vad_filter=True`**，否则长音频会飘。
9. **专有名词必错**：whisper 对中西人名/术语易错（实测"布迪厄"变成"不敌恶"、"授圣"变成"受胜"、"绩点"变成"记点"）。**总结/归档前必须人工校对专有名词**。
10. **外部时间轴勘误**：网上流传的"人工校准"稿可能整体被拉伸（实测一篇标 30:12 的视频真实只有 17:32，约 1.7×）。**以音频实测 duration 为准**；先把逐字稿段落对齐到音频时间轴，再输出 SRT。
11. **视频简介≠正文**：抖音的 title/description（文案）常常**视频里并未朗读**，别把它当逐字稿塞进时间轴。
12. **归档 md 文件名必须 `YYYY-MM-DD-` 前缀**（`validate-output.py` 会校验），但 COS slug / ingest 的 slug 与文件名前缀可能不一致 → 发布前核对。
13. **转写专有名词反复出错**：同一个人名每期都可能错法不同（如"王正 Carl"→"王胜考/王政考"）。有口播的系列建议维护人名白名单，自动替换。
15. **小红书是脆弱路径**：走 `__INITIAL_STATE__` 提取，`xsec_token` 会过期；若解析报「未找到 __INITIAL_STATE__」多为 token 失效/风控，需重新获取分享链接。抖音 API 挂了可换 provider，小红书暂无后备。
16. **视频号（weixin.qq.com/sph）本机无解**：① 官方 get_feed_info 只回元数据、不吐流；② 视频流 ISAAC 加密（前 128KB，用 decodeKey），需微信登录态 + 能注入 JS 的客户端（wx_channels_download，仅 macOS/Windows）；③ 第三方解析 API 几乎全挂。**变通：找同名内容的腾讯新闻/腾讯视频镜像**——腾讯新闻页 blob 播放，从 HTML/网络里提 `vid`，再 `yt-dlp https://v.qq.com/x/page/<vid>.html` 下载。别再对视频号短链死磕第三方 API（实测 15+ 家全 404/502）。
14. **whisper 偶发"整段重复"**（解码回环）：实测遇到过整段 100% 重复。`transcribe.py` 已内置检测（段尾比对往前 3~12 段），命中会打印 `⚠️ 检测到 N 处疑似整段重复`，按提示核对即可。

## 校验

- 转录完成后 `wc -l transcript.txt` 看段数、看末尾时间是否≈视频时长（`meta.json.duration_ms`）。
- 归档总结前过 `validate-output.py --collection reading`。

## 协作关系

| 对象 | 关系 |
|------|------|
| `reading-archive` | 本技能产出转写 → 由其提炼成归档 md |
| `video-editor` | 后期剪辑/字幕烧录 |
| `file-hub` | 大文件托管（COS） |

## 迭代记录

- **v1.5（2026-10-19）**：**新增「第一步铁律」——先找现成文字稿，再谈转写**。播客类先在 RSS 找 `podcast:transcript`（iTunes Lookup 拿 feedUrl → 拉 RSS → 下 transcript.txt/.vtt/.srt）。实测省掉一次 2h14m 的 ASR。
- **v1.4（2026-10-15）**：新增**视频号**支持说明。核心结论：本机拿不到视频号流（官方接口只回元数据、视频流 ISAAC 加密、需微信客户端）；**变通路径 = 找同名内容的腾讯新闻/腾讯视频镜像**（腾讯新闻页提取 `vid` → `yt-dlp https://v.qq.com/x/page/<vid>.html`）。实录案例：超级创新者·猫不白《高手标准能复制…》。新增坑 #16。
- **v1.3（2026-10-14）**：新增**小红书**支持（`scripts/xhs.py` + transcribe.sh 按域名分流）。小红书走分享页 `__INITIAL_STATE__` 提取无水印流，属脆弱路径（已记坑 #15）。


- **v1.2（2026-10-11）**：添加一键入口 `ingest.sh`（下载→转写→COS→签名→建骨架）；`transcribe.sh` 加解析重试 + 转完清 wav；补 Token 成本说明；补"slug 必须带日期前缀"坑。详见 `review.md`。
- **v1.1（2026-10-11）**：确定归档去处为 qiuyiwu.com「视频档案」集合（`/vault/video/`）；新增 `render-video-collection.py` + `publish-video.sh`；原视频改存 COS（`qiuyiwu-1359505647`，签名链接）。站点服务集合白名单加入 `video`。
- **v1.0（2026-10-11）**：建制。起因：用户发来抖音布迪厄视频要求提取内容，手工跑通全管线后固化。含 douyin.py / transcribe.sh / transcribe.py 三个脚本 + 11 条踩坑。

---
name: livepage-mcp
description: 从邱懿武的 LivePage PPT 库（qiuyiwu.com/mcp/livepage，MCP 服务）检索、读取、取材，用于提案、视频剪辑、内容复用。当用户说"从我的PPT库找/调/取"、"用我以前的PPT"、"找一下我讲XX的那页"、"做个提案/视频，从PPT库取材"时使用。也可用于定位某张幻灯片的原文、AI解读、版式、以及下载页面图片。
id: fande/livepage-mcp
---

# LivePage MCP — 个人 PPT 库检索与取材

把邱懿武的 **2000+ 页历史 PPT**（14 个 deck）变成可检索、可取材的内容资产，用于**提案 / 视频剪辑 / 内容复用**。

## 连接

- **Endpoint**：`https://qiuyiwu.com/mcp/livepage`（MCP streamable-http，`LivePage v1.30.0`）
- **鉴权**：`Authorization: Bearer <token>`
- **凭据**：`vault: qiuyiwu.com/livepage-mcp`；脚本读取 `~/.config/livepage/conn.txt`（600 权限）
- **客户端**：`scripts/lp.py`（纯标准库，无依赖）

## 快速用法

```bash
cd skills/livepage-mcp/scripts
python3 lp.py collections                          # 列 14 个 deck
python3 lp.py search "创造力" --limit 8             # 全文搜（返回 content_id/页码/标题/摘要）
python3 lp.py search "组织变革" --collection legacy-deck-e87cb45c05ad389d
python3 lp.py read <content_id>                    # 读一页：原文 + AI 解读
python3 lp.py context <content_id>                 # 前后页（顺出整段叙事）
python3 lp.py assets <content_id>                  # 列素材
python3 lp.py get <content_id> --kind image --out /tmp/p.jpg   # 下图片（base64→文件）
python3 lp.py --json search "xx"                   # 原始 JSON，便于管道
```

## 集合清单（14 个 deck）

| collection_id | 标题 | 页数 |
|---|---|---|
| legacy-deck-90783486b4b0693c | AI 思维与认知 / MBA | 484 |
| legacy-deck-58e08f69ba8386e2 | AI 教育 K12 | 466 |
| legacy-deck-772a5fb04f9bad38 | AI 时代的造"物"思维 | 187 |
| legacy-deck-c35b21d6ca39aa7c | 产品定义方法论与 AI 产品思维 | 215 |
| legacy-deck-1e7d5ea110099bb4 | 产品路演方法论 | 74 |
| legacy-deck-4691511b6bed23e5 | 人工智能带来产业变革 | 157 |
| legacy-deck-649e688a567a6e38 | 管理学院的 AI 课 | 153 |
| legacy-deck-d3cec99112255db9 | 艺术家发布论坛 | 41 |
| legacy-deck-fffe7db9df23e0e7 | 造物云 2025 介绍 | 53 |
| legacy-deck-c50157fef3e4d058 | 浙大全链路解决方案 | 251 |
| legacy-deck-9ed54f8bee3b57fb | AI 产品创新体系 | 101 |
| legacy-deck-e87cb45c05ad389d | AI 时代的组织变革 | 46 |
| pdf-35483b961593 | AI 时代的组织变革 (pdf) | 46 |
| keynote-7d0657542fbf07d9 | AI 时代的组织变革 (keynote) | 84 |

> 同一份内容可能有多种来源格式（legacy/pdf/keynote）——**取内容前先看哪个来源更全**。

## 读一页返回什么（取材的关键）

```json
{
  "title": "有一个想法",
  "slide_text": "页面原文（可做字幕/口播稿）",
  "ai_interpretation": {
    "audience_takeaway": "这页要传达的核心",
    "claims": "核心主张",
    "concept_layer": "现象/概念层",
    "layout_pattern": "版式",
    "has_chart|has_diagram|has_illustration|has_photo": "有没有图（决定要不要抠素材）",
    "narration": "讲稿式描述（可直接当口播）",
    "knowledge_atoms": ["知识原子，可做信息卡"]
  }
}
```

**这意味着它是一套"带标签的分镜素材库"，不是裸文字。**

## 三个标准流程

**1. 提案取材**：`search 关键词` → 挑相关页 → `read` 读主张/原文 → `get --kind image` 抠图 → 组进新 deck。

**2. 视频剪辑取材**：
- 搜主题 → 定位页 → 读 `narration`/`audience_takeaway` 当**口播脚本**
- `has_illustration/photo=true` → `get_asset image` 抠图当**画面**
- `read_context` 顺出**前后页**，得到一段完整叙事

**3. 内容复用**：找旧 deck 里已讲透的观点（避免重复造），拷原文进新提案。

## 配套：给取材配口播（TTS）

Mimo TTS（本地适配器 127.0.0.1:18800 → api.xiaomimimo.com）。
⚠️ **坑**：配置里的 `mimo-v2-tts` 已失效，现用 **`mimo-v2.5-tts`**；且 TTS 模型要求
**messages 里必须有 assistant role**（要朗读的文本放 assistant），否则报 `messages must contain an assistant role`。

    POST https://api.xiaomimimo.com/v1/chat/completions
    {"model":"mimo-v2.5-tts",
     "messages":[{"role":"user","content":"请朗读下面文字。"},{"role":"assistant","content":"<要读的文本>"}],
     "modalities":["audio"],"audio":{"voice":"mimo_default","format":"mp3"}}
    → choices[0].message.audio.data (base64) → 解出 mp3 → ffmpeg 转 opus/m4a

备选：`edge-tts`（zh-CN-YunxiNeural 等）本机连微软服务返回 403，暂不可用。

## 硬约束（务必遵守）

1. ⚠️ **读权 ≠ 发布权**：服务自己声明 `"Reading rights do not imply publishing rights"`，`publication_permission` 多为 `unknown`。**内部参考/剪辑可用；对外公开发布前必须确认授权。**
2. ⚠️ **AI 解读 ≠ 原话**：`ai_interpretation` 是 AI 生成的解读，**不能当作讲者原话引用**。引用要引 `slide_text`（原文）。
3. **`get_asset kind=html`** 常报错（多数页 `has_html=false`）——本库以"页图+文字+AI元数据"为主，非完整 HTML 源。
4. **偶发限流**：首次 `read_content` 用假 id 会报 `LivePage request failed`，用真实 id 即可。
5. **不要把 token 写进任何仓库/聊天**；脚本从 `~/.config/livepage/conn.txt` 读。

## 协作

| 对象 | 关系 |
|------|------|
| `构成`（A-09） | 取材 → 排版成新 deck / 视频 |
| `media-transcript` | 视频侧（转写/剪辑）；本技能供"素材源" |
| `reading-archive` | 若要把某页沉淀成档案 |

## 迭代记录

- **v1.1（2026-10-14）**：实测打通全链路（14 集合 / 搜索 / 读页 / 上下文 / 抠图 get_asset image ✅）。产出 lp.py 客户端。
- **v1.0（2026-10-14）**：建制。测试 MCP 连通性与能力。

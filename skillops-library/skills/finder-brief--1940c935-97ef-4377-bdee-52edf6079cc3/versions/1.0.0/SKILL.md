---
name: finder-brief
description: >-
  范德给邱懿武（懿武）出任何「简报/报告/分析页」时用。把结论做成一张移动端设计页 HTML，
  发布到 share.qiuyiwu.com，**只发链接、不发图片**（飞书长图会裁切，他已明确要求）。
  触发场景：决策晨报、调研汇总、选题矿、分析洞察、周报月报、任何"给懿武看的东西"。
  也用于把深脑（shennao / deepbrain MCP）的判断做成可回看的页面。
---

# finder-brief：把简报做成链接（不是图片）

## 为什么有这条

邱懿武（=用户，下称懿武）对报告的唯一硬要求：

> **只发链接，不发图片。** 飞书对长图/附件显示反复出问题（裁切、不可靠）。落点统一 `share.qiuyiwu.com`。

**所以：凡是要"给他看"的产出 → 一律渲染成 HTML → 发到 share 站 → 消息里只给 URL。**

## 落点与结构

- **站点**：`https://share.qiuyiwu.com/`（独立静态站）
- **服务器**：`146.56.239.22`，目录 `/var/www/html/share/`，nginx 配置 `/etc/nginx/sites-enabled/share.qiuyiwu.com`
- **证书**：复用 `qiuyiwu.com`（含该子域，2027-01 到期）
- **索引**：`https://share.qiuyiwu.com/`（= finder-briefs.html）

## 设计系统（**唯一真相源**）

**`scripts/brief-design.css`** —— 所有页共用这一份。**改这里 = 改所有页。**
**v2（2026-11-10）：已对齐 qiuyiwu.com 站内真源**（`/var/www/html/styles.css` + `assets/v3-tokens.css`）。色值/字体/圆角一律取自站内 token（暖白纸感 #FAF8F4、暖红强调 #8E4231、深脑紫 #7A5CC8、Source Han 字体族），**不再另造色**。站内改版时同步此文件。
样张：https://share.qiuyiwu.com/design-system-v2.html （由 `build-design-system.py` 从本文件生成，永远与真源一致）。
站内设计系统页：https://qiuyiwu.com/design-system.html （V3 规范，含 light/dark 双份 token）。
前缀 `bf-`：`bf-mast`（报头）· `bf-lead`（导语）· `bf-h2`（分区标题）· `bf-card`（卡片，`.c-blue/.c-yellow/.c-red/.c-purple/.c-green`）· `bf-row`（列表行）· `bf-side`/`bf-vs`/`bf-punch`（对照）· `bf-quote`（引文）· `bf-todo`（行动）· `bf-table`（表）· `bf-tag`（胶囊）· `bf-foot`（页脚）· `bf-cube`（深脑立方体）。

色值/字体/尺寸全在 `:root`，**不要在新页面里重写色值**——引用变量。

### 生成新页（两种方式）
1. **决策晨报**：改内容文件 → `python3 scripts/build-brief.py <content.md> <out.html>`（自动内联设计系统）。
2. **其他任意页**：写 HTML 时在 `<style>` 里直接 `@import` 或复制 `brief-design.css` 内容；用 `bf-*` 类名。

## 设计规范（简述）

- **风格**：纸感 + 红色强调的编辑风
- **画幅**：宽 430–470px（手机）；题目/引文用衬线（Noto Serif CJK SC），正文无衬线
- **字号**：正文 ≥16px，行距 1.75；引文 17px 衬线
- **结构**：报头（深脑立方体 SVG）→ 今日一句（荧光高亮）→ 分块卡片（左色条分类）→ 数据行
- **模板**：`scripts/brief-template.html` + `scripts/brief-design.css`

## 工具（都在 workspace/scripts/）

| 脚本 | 作用 |
|---|---|
| `publish-html.sh <html> [slug]` | **通用发布**：上传 → 回显 URL。（最常用） |
| `brief-design.css` | **设计系统**：色值/字体/组件类，所有页共用 |
| `brief-template.html` | 决策晨报页模板（引用设计系统） |
| `render-shot.sh <html> <out.png> <w> [scale]` | HTML→PNG，**按真实内容高裁切**（备用，不再推图） |
| `shot-slices.sh <html> <prefix> <w> [maxH]` | HTML→按空白行智能切片（备用） |
| `build-brief.py <content.md> <out.html>` | 用模板生成决策晨报页 |
| `publish-brief.sh <content.md>` | 决策晨报一键：构建→切片→发布 |

## 标准流程

```
1. 写内容（Markdown 或直接用模板）
2. 若复用现成 skill（如 answer-me-with-html）生成 HTML，也可以
3. bash scripts/publish-html.sh <文件.html> <slug>
4. 消息里只发：一行摘要 + 🔗 <URL>
```

## 铁律

- ❌ **绝不发图 / 绝不写 `MEDIA:`**（对懿武的所有简报）
- ✅ 只发 **文本摘要 + 一个链接**
- ✅ 每次发布后 **curl 校验 HTTP 200** 再回话
- ✅ 文件名用**语义化 slug**（如 `decision-brief-2026-11-10.html`）
- ✅ 若用了深脑的判断，只引 `quote_verified` 原话、署原说话人

## 已验证的坑

1. **飞书长图会裁** → 根因在飞书显示，不在渲染；**解法就是发链接**（本 skill 的由来）。
2. `scp` **必须带 sshpass**，否则 "Permission denied"；批量 scp 易被拒 → 打 tar 包一次传。
3. nginx 改动**先 `nginx -t` 再 reload**；warnings 多半是原有的，先看是不是 new。
4. `chrome --screenshot` 的 `--window-size` 高度**不能手填**（会截掉）→ 用 `render-shot.sh`。

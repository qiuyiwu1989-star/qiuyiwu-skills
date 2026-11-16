# 实录标准（结构与密度）

> 来源：qiuyiwu.com 线上 `pipeline/check_recap_standard.py`（原文摘录 + 说明）
> 用途：speech-recap 技能的验收标准

---

## 一、结构六件（缺了就是漏装，退出码非 0）

线上脚本原文说明：

> 【结构】每篇必须齐的六件(缺了就是新实录漏装,退出码非 0)
>   进度条容器 / 阅读脚本 / 统一顶栏 / 篇尾说明 / 章标题带 class="part" / 章标题带 id
>   章标题没 id 会同时废掉两个东西:左侧导览渲染不出来,检索深链只能落到页面顶部。

| # | 件 | 判准（HTML 里找什么） |
|---|---|---|
| 1 | 进度条容器 | `read-bar` |
| 2 | 阅读脚本 | `recap-reader.js` |
| 3 | 统一顶栏 | `v3-shell.css` **且** `v3-ui.js`（2026-08-10 起，从旧版 site-nav.js 换成 V3 shell） |
| 4 | 篇尾说明 | `class="foot"`（2026-08-10 起标签从 `<footer>` 改成 `<p>`，**避免一页两个 `<footer>` 地标**；判准只认 class） |
| 5 | 三栏网格壳 | `class="r-shell"` + `id="r-toc"` + `id="r-atoms"`（三栏：左目录/右要点面板，见 assets/recap.css v3） |
| 6 | 章标题 | 每个 `<h2>` 都要有 `class="part"` **且**有 `id` |

---

## 二、密度（视觉停顿间隔，只报告不阻断）

线上脚本原文说明：

> 【密度】视觉停顿间隔(只报告,不阻断)
>   停顿 = 图 + 小节标题 + 金句,读者能歇一口气、能定位的锚点。
>   标准是每 300-500 字一次。实测 design-future 曾经每 3529 字才有一次,
>   读者要滚过约 7 屏才遇到一个锚点。
>   这条是内容层的活(多半是补小节标题),不该阻断部署,但要一直看得见。

**公式**：
```
正文去空白字数 ÷ 视觉停顿数  →  落在 300-500 为达标
其中：停顿 = <img> 数 + <h3> 数 + <blockquote> 数
（正文范围：<article>...</article>，词数＝去空白、去标签后的字符数）
```

**常量**：`DENSITY_MAX = 500`（必须 ≤）/ `DENSITY_IDEAL = 300`（理想）

---

## 三、发布链路（qiuyiwu.com）

- 实录目录：`/var/www/html/speakings/{slug}/`（内含 `index.html` + `fig/`）
- 图：`fig/{slug}-{页码:03d}.webp`
- 索引：`/var/www/html/data/talks-index.json`（talks 数组）+ `data/speakings-cards.json`（cards）
- 发布脚本：`/var/www/html/pipeline/draft_recap.py`（支持 `--publish=<slug>`）
- 校验脚本：`/var/www/html/pipeline/check_recap_standard.py`
- 依赖的 CSS：`/styles.css` + `/assets/v3-tokens.css` + `/assets/v3-shell.css` + `/assets/recap.css`
- 依赖的 JS：`/assets/library-data.js` + `/assets/nav-config.js` + `/assets/v3-ui.js` + `/assets/recap-reader.js`

⚠️ **本地预览坑**：HTML 引的是站上**绝对路径**（`/styles.css`），用 `file://` 打开会**完全没有样式**。要本地看效果，需把 4 个 CSS 抓下来改相对路径引用（或起个指向 qiuyiwu.com 的本地服务）。

---

## 四、优先用线上产出，不要自造壳

qiuyiwu.com 已有成熟的**三栏网格壳**（左目录 + 正文 + 右要点面板）与阅读进度、深链。**做新实录时套现有壳，不要另发明一套**——否则六件容易漏，样式也会走样。

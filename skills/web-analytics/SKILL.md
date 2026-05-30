---
name: web-analytics
description: 给中文 + 海外双场景网站接数据统计 — 百度统计 / GA4 / GTM 一次配齐，含 7 个核心事件埋点（页面访问、卡片点击、外链转化、滚动深度、表单提交、视频播放、PWA 安装）。当用户要"接百度统计 / 接 GA4 / 接 Google Analytics / 加埋点 / 加事件追踪 / 做数据监测 / 上 GTM / 监控转化率 / 看流量来源 / 加百度推送"时使用。即使只说"给这个网站加个统计"也应触发。
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# /web-analytics — 双场景数据统计接入

给任何中文 / 海外网站一次性接齐三套统计：**百度统计**（国内必备）+ **GA4**（境外）+ **GTM**（可选 — 长期维护用）。包含 7 个高价值事件的埋点模板，全部双发到两套统计，让你在中外两个后台看同一份数据。

脚本路径：`~/.claude/skills/web-analytics/`

---

## 工作流（agent 视角）

1. **问用户拿 ID**
   - 百度统计 ID（hm.js?后面那串 32 位 hex）— https://tongji.baidu.com/ 注册站点拿
   - GA4 Measurement ID（`G-XXXXXXXXXX` 形式）— https://analytics.google.com/ 注册属性拿
   - 可选：GTM ID（`GTM-XXXXXX`）

2. **决定要装哪几套** — 默认全装，国内站可以只装百度

3. **找到所有要插入的 HTML 文件** — index.html / 详情页模板 / 子页 …

4. **在每个 `</head>` 之前注入对应 snippet**（见下方模板）

5. **如果用户要事件埋点 → 加 helper 函数到 app.js + 调用点**

6. **验证** — curl 抓 HTML 看 grep 命中 + 提示用户去后台「实时」看数据

---

## 模板 1：百度统计

放在 `</head>` 之前（异步加载，不阻塞）：

```html
<!-- 百度统计 Baidu Analytics -->
<script>
  var _hmt = _hmt || [];
  (function() {
    var hm = document.createElement("script");
    hm.src = "https://hm.baidu.com/hm.js?{{BAIDU_ID}}";
    var s = document.getElementsByTagName("script")[0];
    s.parentNode.insertBefore(hm, s);
  })();
</script>
```

替换 `{{BAIDU_ID}}` 为用户给的 32 位 hex。

---

## 模板 2：GA4

放在 `</head>` 之前：

```html
<!-- Google Analytics 4 (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={{GA4_ID}}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', '{{GA4_ID}}');
</script>
```

替换 `{{GA4_ID}}` 为 `G-XXXXXXXXXX`。

> ⚠️ 国内访客可能因网络问题加载慢/被拦。**两套并存最稳**：境内看百度，境外看 GA4。

---

## 模板 3：GTM（可选）

如果用户要长期可维护 → 推荐用 GTM，以后所有 tag 在后台改：

```html
<!-- Google Tag Manager（放 head 第一项）-->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','{{GTM_ID}}');</script>
```

`<body>` 紧跟其后：

```html
<!-- GTM noscript -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={{GTM_ID}}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
```

装好 GTM 后，**GA4 / 百度 / 其他 tag 都通过 GTM 后台配**，HTML 里只留 GTM 这一段。

---

## 双发事件埋点 helper

在 `app.js` 最顶部（content.js 之后、其他逻辑之前）注入：

```javascript
/* ========== 双发事件追踪 helper ==========
   一次调用，自动上报到 GA4 + 百度统计。
   用法：track('card_view', { card_id: 'L4-022', card_level: 'L4' });
*/
window.track = function(eventName, params = {}) {
  // GA4
  if (typeof gtag === 'function') {
    try { gtag('event', eventName, params); } catch (_) {}
  }
  // 百度：拆成 类别/动作/标签/值
  if (typeof _hmt !== 'undefined') {
    try {
      const category = params.category || eventName.split('_')[0] || 'event';
      const action = params.action || eventName;
      const label = params.label || params.id || params.card_id || params.name || '';
      const value = params.value || params.amount || 0;
      _hmt.push(['_trackEvent', category, action, String(label), Number(value) || 0]);
    } catch (_) {}
  }
};
```

---

## 7 个核心事件 — 任何项目都该埋

| 事件名 | 触发时机 | 参数 | 业务价值 |
|--------|---------|------|---------|
| `card_view` | 详情页加载 / 卡片查看 | `card_id`, `card_level` | 内容热度排序 |
| `card_flip` | 翻面 / 切换标签 / 展开折叠 | `card_id`, `side` | 互动深度 |
| `media_play` | 音频 / 视频开始播放 | `media_id`, `duration` | 多媒体价值 |
| `tag_click` | 点 #标签 / 分类 | `tag_name` | 用户兴趣聚类 |
| `outbound_click` | 跳外链（淘宝/微信/合作站）| `target_url`, `target_name` | **转化漏斗** |
| `scroll_depth` | 滚动达 25/50/75/100% | `depth` | 阅读完成率 |
| `pwa_install` | 安装到主屏 | — | 留存信号 |

### 注入到 app.js 的标准埋点代码

```javascript
// 1) card_view — 详情页加载时
function trackCardView(cardId, level) {
  window.track('card_view', { card_id: cardId, card_level: level, category: 'card' });
}

// 2) outbound_click — 所有外链点击（统一拦截）
document.addEventListener('click', (e) => {
  const a = e.target.closest('a[href^="http"]');
  if (!a) return;
  if (a.host && a.host !== location.host) {
    window.track('outbound_click', {
      target_url: a.href,
      target_name: a.textContent.trim().slice(0, 40),
      category: 'outbound'
    });
  }
});

// 3) scroll_depth — 25/50/75/100 阈值各上报一次
(function() {
  const reported = new Set();
  function check() {
    const h = document.documentElement;
    const pct = Math.round((h.scrollTop + window.innerHeight) / h.scrollHeight * 100);
    for (const t of [25, 50, 75, 100]) {
      if (pct >= t && !reported.has(t)) {
        reported.add(t);
        window.track('scroll_depth', { depth: t, category: 'engagement' });
      }
    }
  }
  let scheduled = false;
  window.addEventListener('scroll', () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => { check(); scheduled = false; });
  }, { passive: true });
})();

// 4) media_play — TTS / video 播放（按需挂载）
document.addEventListener('play', (e) => {
  const el = e.target;
  if (el.tagName === 'AUDIO' || el.tagName === 'VIDEO') {
    window.track('media_play', {
      media_id: el.id || el.src.split('/').pop(),
      duration: el.duration || 0,
      category: 'media'
    });
  }
}, true);

// 5) pwa_install — Service Worker installed
window.addEventListener('appinstalled', () => {
  window.track('pwa_install', { category: 'pwa' });
});
```

剩下的 `card_flip` / `tag_click` 业务场景不同，要根据项目 DOM 结构挂 — 用户问的时候再加。

---

## 关键点 + 常见坑

| 坑 | 原因 | 修法 |
|----|------|------|
| GA4 后台「实时」 0 访客 | 国内被 GFW 拦 / 装了广告拦截 | 用无痕窗口 / 海外节点测；境内访客本就难拿到 GA 数据 |
| 百度后台一直显「0」 | sitemap 还没主动提交 / 站点未验证 | 去 https://ziyuan.baidu.com/ 验证站点 + 提交 sitemap |
| GA4 事件不显示 | 用户参数命名不规范（含中文 / 空格）| `event_name` 只用 `[a-z_]`，参数 key 一样 |
| 数据双计 | GA4 默认 `send_page_view: true` + 又手动 trigger 一次 | 二选一，别同时 |
| GTM + GA4 直装 = 数据翻倍 | 两套都上报 | **二选一**：要么 HTML 直插 GA4，要么 GTM 里配 GA4 tag |
| 用户隐私 | GDPR / 个保法 | 需要的话加 cookie consent banner（用户单独问的时候再做）|

---

## 国内站长平台「主动推送」（额外加分）

百度爬取速度慢 → 主动推送让百度立刻知道有新内容。一次性给 `scripts/baidu_push.py`：

```python
#!/usr/bin/env python3
"""百度站长平台主动推送 — 把 sitemap 里的 URL 全推一遍"""
import os, sys, re, urllib.request

SITE = os.environ.get("BAIDU_SITE", "https://qiuyiwu.com")        # 改你的站点
TOKEN = os.environ.get("BAIDU_PUSH_TOKEN", "")                    # 站长平台拿
if not TOKEN:
    print("ERROR: export BAIDU_PUSH_TOKEN=xxx"); sys.exit(1)

# 从本地 sitemap.xml 拿全部 URL
sitemap = open(sys.argv[1] if len(sys.argv) > 1 else "sitemap.xml").read()
urls = re.findall(r"<loc>([^<]+)</loc>", sitemap)
payload = "\n".join(urls).encode("utf-8")

url = f"http://data.zz.baidu.com/urls?site={SITE}&token={TOKEN}"
req = urllib.request.Request(url, data=payload,
    headers={"Content-Type": "text/plain"}, method="POST")
print(urllib.request.urlopen(req).read().decode())
```

跑：`BAIDU_PUSH_TOKEN=xxx python3 scripts/baidu_push.py sitemap.xml`

---

## 调用流程速查

收到「接百度 + GA4」类请求：

1. **问 ID**：要不要装哪几套？拿 ID
2. **找 HTML**：grep 项目里 `</head>` 在哪些文件出现
3. **批量插**：每个 `</head>` 之前注入对应 snippet
4. **可选埋点**：如果用户要事件追踪 → 注入 `window.track()` helper + 7 个核心事件代码
5. **部署 + 验证**：curl 抓 HTML 看 grep 是否命中；告诉用户去「实时」看
6. **如果走 PWA / SW**：提醒 **Service Worker 的 `CACHE_VERSION` 也要 bump**，否则老访客被旧缓存拦着看不到新统计代码！

提示用户：
- 百度后台数据 5 分钟内到
- GA4 后台数据 30 秒内到（但中国大陆访客可能数据稀疏）
- 24 小时后报表（非实时）才会聚合稳定

---

## 进阶（用户问到再做）

- **跨域追踪**（多个子站合并统计）：GA4 用 `linker` config
- **隐私合规**：cookie consent → 默认拒绝 → 用户点同意才上 tag
- **微信小程序 + H5 统一统计**：用 GTM Server-side 中转
- **A/B 测试**：GA4 实验或 Google Optimize（已下线，建议 VWO / Statsig）
- **自定义维度**：GA4 定义 `card_level` 这类自定义参数 → 后台报表才能切片

如果用户问"我要配漏斗"、"我要看用户路径" → 引导到 GA4 探索 → 漏斗探索 / 路径探索，自己用拖拽配（这里教不动，让他自学）。

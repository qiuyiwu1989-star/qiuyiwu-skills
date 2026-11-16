---
name: design-tokens
description: 设计资产库。统一管理品牌色/字体/图标/间距/阴影等设计规范，确保所有设计输出视觉一致。触发词：品牌规范 / 设计系统 / design tokens / 配色方案 / 字体规范
version: "v1.0"
---

# Design Tokens · 设计资产库

## 这是什么

设计资产库是构成的"设计DNA"——把品牌视觉规范（颜色、字体、间距、阴影、圆角等）存成结构化JSON，所有设计输出自动引用，确保视觉一致性。

**核心价值：** 做10次设计，看起来像一个人做的。

## 工作流程

```
Step 1：检查是否有现成的 design-tokens.json
  ├─ 有 → 加载并使用
  └─ 没有 → 走 Step 2
  ↓
Step 2：建立品牌规范
  ├─ 用户提供品牌指南 → 提取token
  ├─ 用户说"帮我定" → 根据行业/调性推荐方案
  └─ 无明确需求 → 使用默认中性方案
  ↓
Step 3：输出 design-tokens.json
  ↓
Step 4：后续设计自动引用（所有引擎读取同一份token）
```

## Token 结构

```json
{
  "brand": {
    "name": "品牌名",
    "tagline": "一句话定位"
  },
  "colors": {
    "primary": "#2563EB",
    "secondary": "#7C3AED",
    "accent": "#F59E0B",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "neutral": {
      "50": "#F9FAFB",
      "100": "#F3F4F6",
      "200": "#E5E7EB",
      "300": "#D1D5DB",
      "400": "#9CA3AF",
      "500": "#6B7280",
      "600": "#4B5563",
      "700": "#374151",
      "800": "#1F2937",
      "900": "#111827"
    }
  },
  "typography": {
    "heading": {
      "family": "Inter, system-ui, sans-serif",
      "weights": [600, 700, 800],
      "sizes": {
        "h1": "2.5rem",
        "h2": "2rem",
        "h3": "1.5rem",
        "h4": "1.25rem"
      }
    },
    "body": {
      "family": "Inter, system-ui, sans-serif",
      "weights": [400, 500],
      "sizes": {
        "sm": "0.875rem",
        "base": "1rem",
        "lg": "1.125rem"
      }
    },
    "mono": {
      "family": "JetBrains Mono, monospace",
      "weights": [400, 500]
    }
  },
  "spacing": {
    "xs": "0.25rem",
    "sm": "0.5rem",
    "md": "1rem",
    "lg": "1.5rem",
    "xl": "2rem",
    "2xl": "3rem",
    "3xl": "4rem"
  },
  "radius": {
    "sm": "0.25rem",
    "md": "0.5rem",
    "lg": "0.75rem",
    "xl": "1rem",
    "full": "9999px"
  },
  "shadows": {
    "sm": "0 1px 2px rgba(0,0,0,0.05)",
    "md": "0 4px 6px -1px rgba(0,0,0,0.1)",
    "lg": "0 10px 15px -3px rgba(0,0,0,0.1)",
    "xl": "0 20px 25px -5px rgba(0,0,0,0.1)"
  }
}
```

## 行业预设

| 行业 | 主色 | 字体风格 | 调性 |
|------|------|---------|------|
| 科技/SaaS | 蓝色系 | 现代Sans-Serif | 专业、可信 |
| 教育 | 绿色系 | 圆润Sans | 友好、亲和 |
| 金融 | 深蓝/金 | 稳重Serif/Sans | 可靠、权威 |
| 消费品 | 活力色 | 现代Sans | 年轻、活力 |
| 奢侈品 | 黑/金 | 衬线体 | 高端、克制 |
| 医疗健康 | 浅蓝/绿 | 清晰Sans | 专业、安全 |

## 引用方式

所有设计引擎在生成前读取 `构成/skills/design-tokens/tokens.json`：
- frontend-slides：读取颜色和字体，注入CSS变量
- html-ppt-skill：读取主题色，匹配最接近的预设主题
- guizang-ppt-skill：保留其独特美学，但用token的颜色做点缀
- feishu-doc-visual：用token的颜色规范Mermaid图的颜色语义
- huqiu-design：读取全部token，确保原型与品牌一致

## 安全边界

| 规则 | 说明 |
|------|------|
| **不覆盖已有品牌** | 如果用户已有品牌指南，不擅自修改 |
| **修改需确认** | 修改颜色/字体等核心token前必须用户确认 |
| **版本化** | 每次修改记录版本号和变更原因 |

## 输出

- `tokens.json` — 结构化设计token
- `README.md` — 使用说明（给Agent看的）
- `preview.html` — 可选，品牌预览页面

---
name: file-hub
description: "个人文件管理系统。当用户发送文件（图片/文档/PDF/HTML/音频/视频）要求存储、归档、索引、管理时使用。也适用于查询已存储文件、搜索文件、同步索引、查看文件目录。触发词：存储/存起来/归档/文件管理/查文件/文件列表/同步"
---

# 文件管理系统（File Hub）

懿武的个人云盘 + 索引系统。接收文件 → 存储到 COS → 维护索引 → 可查可检索。

> 归属：范德 CEO | 懿武发文件时自动触发

## 你是谁

你是文件管理员。你的职责是：收到文件后安全存储、建立索引、方便后续检索和管线处理。

**核心原则：**
- 文件来了就存，不问多余的问题
- 大文件（>5MB）优先存 COS，小文件可存服务器本地
- 索引是核心资产，每次操作后必须同步
- 凭据绝不外泄

---

## 存储架构

```
懿武发文件（飞书）
    ↓
OpenClaw 接收（/media/inbound/）
    ↓
┌─────────────────────────────┐
│  范德（处理层）              │
│  ① 下载文件到本地            │
│  ② 推送到 COS               │
│  ③ 更新索引（index.json）    │
│  ④ 同步索引到服务器          │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  COS（存储层）               │
│  opendesign-1359505647       │
│    ├── inbound/    原始文件   │
│    ├── processed/  清洗后     │
│    └── assets/     可发布的   │
└─────────────────────────────┘
    ↓
索引页：https://qiuyiwu.com/files/
```

## 核心流程

### 流程一：接收并存储文件

当用户通过飞书发送文件时：

**Step 1：下载文件**
```
feishu_im_bot_image(message_id, file_key, type)
→ 保存到 /tmp/openclaw/
```

**Step 2：推送到 COS**
```bash
coscmd upload <本地路径> inbound/<文件名>
```

**Step 3：更新本地索引**
```python
# 读取 file-hub/index.json
# 添加新条目（name, size, type, tags, cos_url, uploaded）
# 写回 index.json
```

**Step 4：同步索引到服务器**
```bash
# 方式1：scp 到服务器
scp file-hub/index.json ubuntu@146.56.239.22:/var/www/html/files/.index/index.json

# 方式2：推到 COS
coscmd upload file-hub/index.json .index/index.json
```

**Step 5：回复用户**
```
✅ 文件已存储
📄 文件名：xxx.pdf
📦 大小：2.3MB
🔗 COS：https://opendesign-1359505647.cos.ap-guangzhou.myqcloud.com/inbound/xxx.pdf
📋 索引已同步
```

### 流程二：查询文件

当用户问"我有什么文件"或"找一下XX文件"时：

```bash
# 本地查询
python3 file-hub/fm.py list [category]
python3 file-hub/fm.py search <关键词>
```

返回：文件名、大小、标签、上传时间、COS链接

### 流程三：同步索引

当用户要求同步时：

```bash
python3 file-hub/fm.py sync
```

这会：
1. 同步索引到 COS（.index/index.json）
2. 同步索引到服务器（/var/www/html/files/.index/index.json）

### 流程四：部署 HTML 文件

如果用户发的是 HTML 文件，走 HTML 部署流程：

```bash
# 1. 推到 COS
coscmd upload <文件> html/<项目名>/index.html

# 2. 部署到服务器
sshpass -p '...' scp <文件> ubuntu@146.56.239.22:/tmp/<文件>
ssh ubuntu@146.56.239.22 "sudo cp /tmp/<文件> /var/www/html/html/<项目名>/index.html && sudo chown www-data:www-data /var/www/html/html/<项目名>/index.html"

# 3. 更新 HTML 目录页
# 编辑 /tmp/html-index.html 的 DATA 数组
scp /tmp/html-index.html ubuntu@146.56.239.22:/tmp/html-index.html
ssh ubuntu@146.56.239.22 "sudo cp /tmp/html-index.html /var/www/html/html/index.html && sudo chown www-data:www-data /var/www/html/html/index.html"
```

详见 `html-deploy-registry.md`

---

## 工具链

| 工具 | 用途 | 安装 |
|------|------|------|
| `coscmd` | COS 命令行上传/下载 | `pip3 install coscmd` |
| `sshpass` + `scp` | 服务器文件传输 | `apt install sshpass` |
| `fm.py` | 本地索引管理脚本 | `file-hub/fm.py` |

### fm.py 用法

```bash
# 添加文件（上传到COS + 更新索引）
python3 fm.py add <文件路径> [category] [tags] [desc]

# 列出文件
python3 fm.py list [category] [tag]

# 搜索文件
python3 fm.py search <关键词>

# 同步索引到COS和服务器
python3 fm.py sync
```

---

## 文件分类

| 分类 | 说明 | COS路径 |
|------|------|---------|
| `inbound` | 收件箱（原始文件） | `inbound/` |
| `processed` | 已清洗/结构化 | `processed/` |
| `assets` | 可发布资产 | `assets/` |
| `html` | HTML 页面 | `html/` |

---

## 凭据管理

凭据存储在 `file-hub/config.env`（已加入 .gitignore）。

需要时读取：
```bash
source file-hub/config.env
```

关键变量：
- `COS_BUCKET`：opendesign-1359505647
- `COS_REGION`：ap-guangzhou
- `SERVER_HOST`：146.56.239.22
- `SERVER_USER`：ubuntu

---

## 索引格式

`file-hub/index.json` 结构：

```json
{
  "version": 1,
  "updated": "2026-08-16T00:25:00Z",
  "stats": {
    "total_files": 0,
    "total_size_bytes": 0,
    "by_type": {}
  },
  "files": [
    {
      "id": "abc123",
      "name": "document.pdf",
      "size": 123456,
      "type": "application/pdf",
      "category": "inbound",
      "tags": ["AI", "教育"],
      "desc": "说明文字",
      "hash": "abc123",
      "cos_key": "inbound/document.pdf",
      "cos_url": "https://...cos.../inbound/document.pdf",
      "uploaded": "2026-08-16T00:25:00Z",
      "source": "feishu"
    }
  ]
}
```

---

## 网页索引

https://qiuyiwu.com/files/

- 风格与 qiuyiwu.com 主站一致
- 支持搜索、分类筛选、标签过滤
- 服务器路径：`/var/www/html/files/index.html`

---

## 后续管线（预留）

```
inbound（原始）→ 清洗 → processed（结构化）→ 入知识库
```

待懿武确认后启动。管线逻辑：
1. 新文件进入 inbound/
2. 脚本自动分类（文档/图片/音频/视频/HTML）
3. 清洗（OCR/转写/格式标准化）
4. 结构化（提取标题/摘要/关键词）
5. 写入 processed/
6. 入知识库（二脑/飞书多维表格）

---

## 安全规则

- ⚠️ `config.env` 包含敏感凭据，绝不提交到 git
- ⚠️ COS bucket 为私有读写，文件链接需签名才能访问
- ⚠️ 服务器密码不写入任何可分享文件
- ✅ 凭据只在本地使用，不传给其他 Agent

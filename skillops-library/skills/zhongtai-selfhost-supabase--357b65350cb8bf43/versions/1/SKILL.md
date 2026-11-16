---
name: zhongtai-selfhost-supabase
description: >-
  把一个应用接入自托管在「自己服务器/中台」上的数据库——重点是 Supabase（自建 Docker 栈、从 Supabase 云迁移
  数据与登录态、应用 repoint），也覆盖直连中台共享 Postgres。包含两个在国内服务器上必踩的硬坑解法：①未备案域名
  会被 ICP 墙拦截（连 443 都掐），用一个已备案域名的子域名做指向来绕过；②Supabase 云→自托管的跨版本/IPv6/
  权限迁移坑。当用户说「把数据放到自己的服务器」「自托管 Supabase」「迁移 Supabase 云到自己机器」「接入中台数据库」
  「数据库迁到 122.51.221.171 这类自有服务器」时使用本 skill。
id: qiuyiwu/zhongtai-selfhost-supabase
---

# 自托管 / 中台数据库接入（Supabase 优先）

把一个跑在 Supabase 云（或任意托管 DB）上的应用，搬到**你自己的服务器**上，代码几乎不改，登录态/RLS/向量/存储全保留。这份 skill 是从「深脑(DeepBrain)」真实迁移中提炼的可复用打法 + 两个国内服务器必踩的硬坑解法。

## 先决策：三条路，选哪条

| 场景 | 选 | 为什么 |
|---|---|---|
| 应用本来就用 **Supabase**（auth/RLS/pgvector/storage） | **A. 自托管 Supabase 整栈** | 代码零改，客户端还是 supabase-js，只换 URL+key |
| 应用只用普通 **Postgres**，不依赖 Supabase 那套 | **B. 直连中台共享 PG** | 不必再起一套栈，连共享库即可 |
| 想要 Supabase 体验但 DB 想用现成共享 PG | A 的变体 | 自托管 Supabase 各服务指向外部 PG（少见，慎用） |

> **铁律：不碰中台共享库 `zhongtai_app`。** 自托管要跑一套**独立**的 Supabase Postgres，与共享库**并存、互不干扰、独立端口**。共享机器上别图省事去共用一个 PG 实例。

本 skill 主要讲 **A（自托管 Supabase）**——这是深脑实际走的路，也是最容易踩坑的路。B 在文末「附：直连中台共享 PG」一节。

---

## ⚠️ 两个必踩的硬坑（先看，能省你半天）

### 坑 1：国内服务器 + 未备案域名 = 被 ICP 墙拦截（这是真正的拦路虎）

- 大陆腾讯云/阿里云服务器上，**未做 ICP 备案的域名**，HTTP **和 HTTPS 都会被运营商/云厂商在入口拦截**，跳到 dnspod 的 webblock 提示页。从国内访问必现；从海外访问反而正常——**别被"我这能打开"骗了**。
- 表现：`certbot` 签证书失败（80 口被拦）；从国内 `curl https://你的子域名` 直接 TLS 握手被掐断（`time_appconnect=0.000000`、返回 000）。
- **解法（深脑实测有效）：借一个已经备案、且备案绑定在这台服务器上的域名，用它的子域名做指向。**
  - 深脑的 `deepagent.wiki` 没在这台服务器备案 → 被墙。
  - `zaowuyun.com` 已备案且绑这台机器 → 用 **`sb.ai.zaowuyun.com`** 这个子域名暴露 Supabase API，**从国内 curl 返回 200，畅通**。
  - 操作：在 DNS 把 `sb.ai.<已备案域名>` A 记录指到服务器 IP → nginx server_name 用这个子域名 → certbot 对这个子域名签证书（这个域名备案过，80 口不被拦，能签）。
- **检查清单**：
  ```bash
  # 从国内网络测（关键！海外测不出来）。被墙 = 返回 000 或 dnspod 页面；通 = 200
  curl -sS -o /dev/null -w "%{http_code} appconnect=%{time_appconnect}\n" https://sb.ai.<已备案域名>/auth/v1/health
  ```
- 谁来给这个域名：**问用户** ——「你有没有已经备案、且备案主体绑这台服务器的域名？给我一个，我用它的子域名。」这是绕墙的唯一干净办法，别自己瞎试未备案域名。

### 坑 2：Supabase 云 → 自托管的迁移四连坑

按顺序，每个都真实踩过（见 `reference/migration-gotchas.md` 详解）：

1. **云直连串是 IPv6-only，你的服务器没 IPv6** → TLS 握手 0.000000s 秒断。**改用 Session Pooler 串**（`...pooler.supabase.com:5432`，走 IPv4）。问用户要 pooler 串，不是 direct 串。
2. **云是 PG17、容器是 PG15 → `pg_dump: server version mismatch`**。用 `postgres:17-alpine` 容器跑 pg_dump，别用宿主机的 client。
3. **restore 报 `must be owner of table users` / `must be member of supabase_admin`**：`postgres` 不是超级用户，**`supabase_admin` 才是**。所有 restore（尤其 `--disable-triggers` 灌 auth.users）都用 `supabase_admin` 跑。
4. **`drop schema public cascade` 把 pgvector 一起 drop 了** → import 时 `type "vector" does not exist`。**先 `create extension vector with schema public`，再 import schema。**

---

## 主流程（A：自托管 Supabase）

完整可执行 Runbook 在 **`reference/RUNBOOK.md`**；这里是骨架，配套脚本都在 `scripts/`：

1. **侦察服务器（只读）**：核 CPU/内存/磁盘、Docker/nginx 版本、**已占端口**。共享机器务必避开占用端口，全部重映射到空闲段（深脑用 PG `5433`、Kong `8100`、Studio `8101`）。
2. **拉官方 `supabase/docker`**，别手搓整套 compose。
3. **生成生产密钥**：`node scripts/gen-secrets.mjs >> .env`（零依赖，原生 crypto 签 anon/service_role JWT）。`chmod 600 .env`。
4. **注入端口/URL 片段**：`cat reference/env.ports.template >> .env`，按你的占用情况改端口。**所有服务只听 `127.0.0.1`，唯一出网口是 nginx 后的 Kong。**
5. **起栈**：`docker compose up -d`；`curl 127.0.0.1:<kong>/auth/v1/health` 自检。内存紧可在 compose 停掉 `realtime`/`vector`/`edge-functions`。
6. **建 schema**：用**你仓库自己的迁移 SQL**在目标库跑一遍（`scripts/migrate-from-cloud.sh schema`），而不是依赖云上 schema——避免"云 schema vs 自托管初始 schema"冲突。
7. **搬数据**：`migrate-from-cloud.sh data`——只搬 `public` 业务数据 + `auth.users/identities`（保住登录）。注意上面的坑 2。
8. **nginx + 证书**：`reference/nginx-supabase.conf` → certbot 对**已备案子域名**签（坑 1）。然后把 `.env` 的 `API_EXTERNAL_URL`/`SUPABASE_PUBLIC_URL` 改成 `https://sb.ai.<已备案域名>`，重载。
9. **应用 repoint**：只改三个 env，秒切、可秒回：
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://sb.ai.<已备案域名>
   NEXT_PUBLIC_SUPABASE_ANON_KEY=<自托管 ANON_KEY>
   SUPABASE_SERVICE_ROLE_KEY=<自托管 SERVICE_ROLE_KEY>
   ```
10. **验收**：`/auth/v1/health` ok、旧账号能登录、首屏有数据、向量检索跑通、`/api/health` 200。
11. **存储文件（音频/图片）**单独搬：Supabase Storage 的对象在 S3 后端，**不随 pg_dump 走**。够用就让新上传落自托管、历史不搬；要全搬用 `supabase storage cp`。

### 回滚
env 三连指回云即可**秒回**（迁移是**复制不是搬移**，云库保留到确认无误再停）。自托管栈 `docker compose down`。零数据损失。

---

## 安全红线（每次都守）

- **绝不碰账号密码这条线**：不替用户输/存任何账号密码、连接串密钥；密钥只进服务器 `.env`(chmod 600)，**不进仓库、不进日志、不打印进聊天**。要密钥时让用户自己贴，或 server→server 直传，**不经过本地中转**。
- secret 出现在命令输出时用 `sed` 掩码再展示。
- 生产库写操作、生产 `.env` 改写、部署，都要**用户明确授权**那一次（"部署"/"改"要是明确动词，不接受含糊的"嗯""行吧"）。授权是一次一议，不外推。
- Postgres/Studio 只听 `127.0.0.1`；唯一公网入口是 nginx 后的 Kong。别把 PG/Kong 端口 bind 到 `0.0.0.0`（深脑踩过：默认 compose 暴露到公网，要加 `127.0.0.1:` 前缀收口）。

---

## 本项目实例（深脑实际值，复用时替换）

| 项 | 深脑实际值 |
|---|---|
| 服务器 | `122.51.221.171`（腾讯云 Ubuntu 24.04，8核15G） |
| 已备案绕墙域名 | `zaowuyun.com` → Supabase 暴露在 `sb.ai.zaowuyun.com` |
| 未备案被墙域名 | `deepagent.wiki`（站点主域，但没在这台机备案） |
| 端口 | PG `5433` / Kong `8100` / Studio `8101`（避开共享 PG 的 5432） |
| 共享库（零接触） | `zhongtai_app` |
| 迁移源 | Supabase 云（ap-southeast-1），用 Session Pooler 串迁 |
| 迁移结果 | 31 表 / 137 函数 / 3 auth 用户 / 行数与云完全对齐 |

---

## 附：直连中台共享 PG（路 B，简版）

应用只用普通 Postgres、不依赖 Supabase 那套时：

- 找中台管理员要**只读或限定 schema** 的连接串；**不要**用超级用户串跑业务。
- 给你的应用建**独立 schema / 独立用户**，权限最小化，别和别的服务共用一张表空间。
- 连接走**连接池**（PgBouncer/Supavisor），共享机器上 `pool_size` 给小（深脑自托管池子设 10，铁律：共享机器克制）。
- 同样只在内网/隧道连，公网别裸暴 5432。
- 迁移/建表仍以**你仓库的迁移 SQL** 为准，别手动在共享库里改结构。

---

## 配套文件清单

- `scripts/gen-secrets.mjs` — 零依赖生成 Supabase 生产密钥（PG 密码、JWT_SECRET、anon/service_role JWT、Studio 登录、加密钥）。
- `scripts/migrate-from-cloud.sh` — `schema|data|all` 三档：先在目标库跑你的迁移建 schema，再 data-only 搬 public + auth.users，自带行数校验。
- `reference/RUNBOOK.md` — 完整 10 步可执行 Runbook（含端口规划、compose 精简、验收清单）。
- `reference/migration-gotchas.md` — 迁移四连坑 + ICP 墙的完整复盘与排查命令。
- `reference/env.ports.template` — 端口/URL/鉴权策略 .env 片段。
- `reference/nginx-supabase.conf` — Supabase API 网关的 nginx 反代（放开 body/超时/WebSocket）。

# 🎁 秘密赠礼抽签（Secret Santa）

一个自托管的秘密赠礼抽签 Web 应用：组织者录入参与者和**禁止配对关系**后一键抽签，
系统保证生成一个**完整匹配**；每位参与者拿到一条**只能成功揭晓一次**的专属随机链接，
组织者只能看到“是否已揭晓”，看不到任何人的配对结果。

技术栈：**Python + FastAPI + React（Vite）+ SQLite**，单容器镜像，多阶段构建。

---

## ✨ 功能与保证

- **完整匹配**：抽签后每人**恰好送出一份、收到一份**礼物（完美匹配）。
- **硬性约束**：无人抽到自己；不命中任何组织者设定的“送礼者 ⊘ 收礼者”禁配关系。
- **无解明确提示**：当禁配关系导致不存在任何合法方案时，接口返回明确错误说明，
  **不会写入任何配对或发放链接**（无部分结果）；组织者放宽约束后可重新抽签。
- **一次性揭晓链接**：为每位参与者生成 24 字节随机令牌（`secrets.token_urlsafe`）。
  - 打开链接只看到“待揭晓”页面；点击揭晓是原子条件更新，**只能成功一次**。
  - 揭晓后再次打开只显示“此链接已揭晓过，结果不再显示”。
- **对组织者保密**：组织者页面仅显示每个链接的“尚未揭晓 / 已揭晓（时间）”，
  任何接口都不会向组织者返回他人的收礼人。
- **抽签后锁定**：抽签完成即不可再增删参与者或禁配关系，防止结果被篡改。

---

## 🚀 一条命令启动

需要 Docker 与 Docker Compose v2：

```bash
docker compose up -d --build
```

启动后访问：

- 应用首页： **http://localhost:8000**
- API 文档（Swagger）： **http://localhost:8000/docs**
- 健康检查： **http://localhost:8000/api/health**

停止与查看日志：

```bash
docker compose down        # 停止（保留数据）
docker compose logs -f     # 查看日志
```

> React 构建产物由 FastAPI 在同一端口（8000）托管，无需单独的前端服务或反向代理。

---

## ⚙️ 必要配置（均有默认值，可不设置）

通过环境变量或在项目根目录创建 `.env` 配置：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `SECRET_SANTA_PORT` | `8000` | **宿主机**映射端口（容器内固定监听 8000） |
| `DATABASE_PATH` | `/data/secret_santa.db` | SQLite 数据库文件路径，位于命名卷 `secret-santa-data` 中，容器重建不丢数据 |
| `PORT` | `8000` | 容器内监听端口，一般无需修改 |

例如改用宿主机 9000 端口：

```bash
SECRET_SANTA_PORT=9000 docker compose up -d --build
# 然后访问 http://localhost:9000
```

依赖安装（前端 `npm`、后端 `pip`）与数据库初始化（建目录、建表）都在镜像构建 /
应用启动时自动完成，无需任何手动初始化步骤。

---

## 🧭 使用流程

1. 打开首页，点击**创建活动**（可填写活动名称）。创建后会得到“活动编号 + 组织者令牌”，
   令牌保存在当前浏览器 localStorage 中，也请自行妥善保存（换设备时凭它进入）。
2. 在活动页**添加参与者**。
3.（可选）添加**禁配关系**：选择“送礼者 ⊘ 不可以送给 → 收礼者”。
   “不能抽到自己”无需添加，系统默认保证。
4. 点击**开始抽签**。
   - 成功：页面出现每位参与者的专属链接（形如 `http://host:8000/r/<随机令牌>`），
     可逐条复制或一键复制全部，私下分发给本人。
   - 无解：弹出明确错误，活动保持未抽签状态，调整禁配后重试。
5. 参与者打开自己的链接，确认后点击**揭晓**，看到自己要送礼物的对象；
   结果只显示这一次，组织者页面只更新“已揭晓”状态。

---

## 🔌 HTTP API 摘要

所有组织者接口需携带请求头 `X-Event-Token: <组织者令牌>`。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/events` | 创建活动，返回 `id` 与 `edit_token` |
| `GET` | `/api/events/{id}` | 活动详情（参与者、禁配、揭晓状态；抽签后含每人的揭晓令牌） |
| `POST` | `/api/events/{id}/participants` | 添加参与者（抽签后 409） |
| `DELETE` | `/api/events/{id}/participants/{pid}` | 删除参与者（关联禁配一并删除） |
| `POST` | `/api/events/{id}/constraints` | 添加禁配 `{giver_id, receiver_id}` |
| `DELETE` | `/api/events/{id}/constraints/{cid}` | 删除禁配 |
| `POST` | `/api/events/{id}/draw` | 执行抽签；**无解返回 422 且不产生任何结果** |
| `GET` | `/api/reveal/{token}` | 查询揭晓状态（未揭晓时返回收礼人以便页面展示待确认结果；已揭晓后不返回） |
| `POST` | `/api/reveal/{token}` | 原子揭晓（成功仅一次，重复调用 409） |
| `GET` | `/api/health` | 健康检查 |

---

## 🛠️ 本地开发（不用 Docker）

后端：

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000
# SQLite 文件默认位于 backend/data/secret_santa.db，可用 DATABASE_PATH 覆盖
```

前端（开发服务器带 `/api` 代理到 8000）：

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
```

运行端到端接口测试：

```bash
cd backend
python3 e2e_test.py
```

---

## 📁 目录结构

```
.
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 入口、建表 lifespan、静态托管与 SPA 回退
│   │   ├── database.py      # SQLAlchemy 引擎 / Session / SQLite 外键开关
│   │   ├── models.py        # Event / Participant / Constraint
│   │   ├── schemas.py       # Pydantic 模型
│   │   ├── matching.py      # MRV 回溯随机完美匹配求解器（无解返回 None）
│   │   ├── deps.py          # 组织者令牌鉴权依赖
│   │   ├── serialize.py
│   │   └── routers/
│   │       ├── events.py    # 组织者接口 + 抽签
│   │       └── reveal.py    # 参与者一次性揭晓
│   ├── requirements.txt
│   └── e2e_test.py
├── frontend/
│   ├── src/                 # React 页面（首页 / 活动控制台 / 揭晓页）
│   ├── index.html
│   └── vite.config.js
├── Dockerfile               # 多阶段：Node 构建 -> python-slim 运行
├── docker-compose.yml
└── README.md
```

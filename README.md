# LabAgent｜智能实验室预约系统

面向学生与实验室管理员的 Web 产品原型，结合实验室资源管理、预约审核与 AI 助手，让用户通过页面或自然语言完成规则咨询、资源查询和预约申请。

**项目定位：课程作品、毕业设计原型及产品 Demo。** 当前版本用于展示业务流程，尚未完成生产环境的并发与稳定性验证。

## 产品场景

学生需要预约实验室时，往往需要先了解开放时间、使用规则和设备情况，再填写预约申请。LabAgent 将这些环节连接起来：

> 咨询规则 → 查询实验室与设备 → 核对预约信息 → 提交申请 → 管理员审核 → 查看结果

AI 助手通过工具访问业务数据和预约服务，知识问答通过本地文档向量检索提供参考内容。

## 核心功能

| 模块 | 功能 |
| --- | --- |
| 账号与权限 | 注册、登录、JWT 鉴权、学生与管理员角色、个人资料与密码维护 |
| 实验室管理 | 实验室信息维护、开放状态与开放时间管理、实验室列表查询 |
| 设备管理 | 设备信息维护、所属实验室关联、设备状态查询 |
| 预约管理 | 实验室或设备预约、时段冲突检查、个人预约查询、待审核预约取消 |
| 审核管理 | 管理员通过或拒绝预约申请 |
| 过期处理 | 后台定时扫描并取消已过期的待审核预约 |
| AI 助手 | 实验室规则检索、资源查询、预约工具调用、SSE 流式回答与工具执行状态展示 |

预约状态：`0 待审核`、`1 已通过`、`2 已拒绝`、`3 已取消`。提交预约后需要管理员审核。

## 技术架构

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3、Vite、Vue Router、Element Plus、Axios |
| 内容展示 | Marked、DOMPurify |
| 后端 | Python、FastAPI、Pydantic、SQLAlchemy |
| 关系数据库 | 通过 SQLAlchemy 配置；下方启动示例使用 MySQL 与 PyMySQL |
| 身份认证 | JWT、bcrypt 密码哈希 |
| AI 工作流 | LangGraph、LangChain、兼容 OpenAI API 的模型服务 |
| 知识库 | Chroma、Sentence Transformers、BAAI/bge-small-zh-v1.5 |
| 实时输出 | Server-Sent Events（SSE） |

前端调用 FastAPI 接口，业务数据由 SQLAlchemy 持久化。AI 工作流在模型与工具节点之间执行，工具复用实验室、设备及预约业务服务，并通过 Chroma 检索实验室知识文档。

## 目录结构

```text
lab-agent/
├─ backend/
│  ├─ app/
│  │  ├─ api/              # HTTP 接口
│  │  ├─ common/           # 响应格式与异常处理
│  │  ├─ dependencies/     # 登录鉴权与管理员权限
│  │  ├─ models/           # 数据库模型
│  │  ├─ schemas/          # 请求与响应模型
│  │  ├─ services/         # 业务、Agent 工具与知识库服务
│  │  ├─ utils/            # 密码与 JWT 工具
│  │  ├─ config.py         # 环境配置
│  │  ├─ database.py       # 数据库连接
│  │  └─ main.py           # 应用入口
│  ├─ data/kb/             # Markdown 知识文档
│  ├─ data/chroma/         # 本地向量数据库
│  ├─ uploads/             # 上传文件
│  └─ requirements.txt
├─ frontend/
│  ├─ src/
│  │  ├─ api/              # 接口调用
│  │  ├─ components/       # 公共组件
│  │  ├─ layouts/          # 页面布局
│  │  ├─ router/           # 路由
│  │  └─ views/            # 业务页面
│  └─ package.json
└─ README.md
```

## 本地运行

以下命令从项目根目录开始，使用 Windows PowerShell。前后端分别在两个终端中运行。

### 1. 环境准备

- Python：建议使用 3.11 或 3.12，具体以依赖安装兼容性为准。
- Node.js：满足 `frontend/package.json` 中的 `^22.18.0 || >=24.12.0`。
- npm。
- 可连接的 MySQL 数据库。
- 支持工具调用与流式响应的 OpenAI API 兼容模型服务。

首次运行知识库可能下载嵌入模型，需要可用网络和本地磁盘空间。当前知识库代码配置了 Hugging Face 镜像地址。

### 2. 创建数据库

在 MySQL 客户端执行：

```sql
CREATE DATABASE lab_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

为应用准备可访问该数据库的账号。后端启动时会自动创建数据表，但不会自动创建数据库，也不会自动生成管理员或演示数据。

### 3. 配置后端

在 `backend/.env` 中填写以下配置。占位值需要替换为自己的数据库和模型服务信息；已有配置时请先核对，避免覆盖。

```dotenv
DATABASE_URL=mysql+pymysql://YOUR_DB_USER:YOUR_DB_PASSWORD@127.0.0.1:3306/lab_agent?charset=utf8mb4
JWT_SECRET_KEY=REPLACE_WITH_A_LONG_RANDOM_SECRET
JWT_EXPIRE_HOURS=24
JWT_ALGORITHM=HS256
LLM_API_KEY=YOUR_MODEL_API_KEY
LLM_MODEL=YOUR_TOOL_CALLING_MODEL
LLM_BASE_URL=https://YOUR_MODEL_PROVIDER/v1
```

| 配置项 | 说明 |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy 数据库连接地址；用户名或密码含 URL 特殊字符时需要编码 |
| `JWT_SECRET_KEY` | JWT 签名密钥 |
| `JWT_EXPIRE_HOURS` | 登录有效期，默认 24 小时 |
| `JWT_ALGORITHM` | JWT 算法，默认 HS256 |
| `LLM_API_KEY` | 模型服务密钥 |
| `LLM_MODEL` | 模型名称，需要支持工具调用与流式输出 |
| `LLM_BASE_URL` | 模型服务的 OpenAI API 兼容地址 |

当前配置类要求填写数据库、JWT 密钥及三个模型配置项。不要将真实 `.env`、密钥或生产数据提交到公开仓库。

### 4. 安装并启动后端

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

如果使用其他 Python 版本，请调整创建虚拟环境的命令。

- 后端入口：<http://127.0.0.1:8000/>
- Swagger 接口文档：<http://127.0.0.1:8000/docs>
- ReDoc 接口文档：<http://127.0.0.1:8000/redoc>

知识库会在应用启动时预热。预热失败时应查看后端日志；普通接口可访问不代表 AI 与知识库已经可用。

### 5. 安装并启动前端

新开终端，从项目根目录执行：

```powershell
cd frontend
npm install
npm run dev
```

确认 `frontend/.env.development` 配置：

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

默认访问 <http://localhost:5173>。若端口被占用，以 Vite 输出为准；使用其他前端端口或域名时，还需要调整后端 `app/main.py` 中的 CORS 白名单。

前端开发代理配置在 `frontend/vite.config.js`。AI 流式请求直接使用 `VITE_API_BASE_URL`，修改后端地址时需同时核对代理目标与环境变量。

### 6. 准备演示账号与数据

1. 在注册页创建一个学生账号和一个准备作为管理员的账号。
2. 在本地演示数据库中，将后者提升为管理员，例如将下方账号名替换为实际注册名后执行：

   ```sql
   UPDATE users SET role = 'admin' WHERE username = 'YOUR_DEMO_ADMIN_USERNAME';
   ```

3. 重新登录管理员账号，创建实验室和关联设备，配置开放时间与可用状态。
4. 使用学生账号进行预约，再用管理员账号审核。

项目目前没有内置的默认演示账号或初始化数据脚本，请自行准备并记录。密码通过注册流程生成哈希，不要在数据库中直接写入明文密码。

## 产品 Demo 演示流程

建议演示时长 3～5 分钟，提前准备开放的实验室、可用设备及未被占用的未来时段。

| 步骤 | 操作 | 展示重点 |
| --- | --- | --- |
| 1 | 学生登录并查看实验室列表 | 真实资源与开放状态 |
| 2 | 向 AI 提问“预约实验室需要遵守哪些规定？” | 知识库检索与流式回答 |
| 3 | 提问“有哪些开放的实验室？某实验室有哪些设备？” | 查询业务数据库与工具执行状态 |
| 4 | 提供实验室、日期、起止时间，核对后确认预约 | 对话连接业务操作 |
| 5 | 打开“我的预约” | 申请落库、状态为待审核 |
| 6 | 管理员登录并通过申请 | 审核流程 |
| 7 | 学生刷新预约记录 | 状态更新，完成闭环 |

AI 预约链路应在正式演示前完整验证。模型服务异常时，可通过页面预约继续展示业务流程。

## 知识库说明

知识文档位于 `backend/data/kb/`，当前包含预约规则、设备使用、开放时间及安全规范。文档内容应与实际演示资源和业务规则保持一致。

当前实现以整份 Markdown 文档为检索单元，仅在集合为空时自动导入。修改文档不会自动更新已有向量索引；更新时需要另行实现或执行索引重建，并注意保留需要的数据。

## 前端构建与部署注意事项

在 `frontend` 目录执行：

```powershell
npm run build
npm run preview
```

构建产物位于 `frontend/dist/`。`preview` 用于本地检查构建结果。

部署前应设置生产环境的 `VITE_API_BASE_URL`，再执行构建；开发环境的 Vite 代理不会随静态产物部署。Web 服务需要配置 API 与上传文件访问、Vue Router history 回退，并同步调整后端 CORS。使用反向代理时，应确认 SSE 响应不会被缓冲。

## 当前限制与待完善项

- 缺少自动化测试、数据库迁移和一键初始化演示数据的脚本。
- AI 提交预约的确认目前依赖提示词，尚未实现独立的后端确认机制。
- 预约工具名称 `create_lab_servation` 与提示词、展示标签中的 `create_lab_reservation` 尚未统一。
- 预约时间格式、零时长预约、设备所属实验室及并发冲突控制仍需完善。
- 鉴权需补充用户已被删除的情况处理。
- 知识库文档更新尚未实现自动同步索引。
- 模型服务可用性、生产部署与端到端演示效果需要在目标环境中验证。

以上功能描述依据当前代码整理，不代表已通过完整运行验收。提交作品时建议同时提供演示视频、实际运行截图和环境说明。

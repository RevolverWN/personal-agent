# Personal Agent 部署文档

本文档介绍如何部署 Personal Agent 应用。

## 目录

- [环境要求](#环境要求)
- [本地开发](#本地开发)
- [Docker 部署](#docker-部署)
- [环境变量说明](#环境变量说明)
- [常见问题](#常见问题)

## 环境要求

| 依赖 | 版本要求 |
|------|----------|
| Python | >= 3.11 |
| Node.js | >= 20 |
| Docker | >= 24.0 (可选，用于容器部署) |
| Docker Compose | >= 2.0 (可选，用于容器部署) |

## 本地开发

### 方式一：使用安装脚本（推荐）

**Linux/macOS:**
```bash
# 安装依赖
./scripts/install.sh

# 启动服务
./scripts/start.sh
```

**Windows:**
```cmd
REM 安装依赖
scripts\install.bat

REM 启动服务
scripts\start.bat
```

### 方式二：手动安装

**1. 安装后端依赖**
```bash
cd backend
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -e .
```

**2. 安装前端依赖**
```bash
cd frontend
npm install
```

**3. 启动服务**

后端（在一个终端）:
```bash
cd backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

前端（在另一个终端）:
```bash
cd frontend
npm run dev
```

**4. 访问应用**

打开浏览器访问: http://localhost:5173

## Docker 部署

### 快速启动

```bash
# 在项目根目录
cd docker
docker compose up -d
```

应用将在 http://localhost 启动。

### 开发模式

使用开发配置（支持热重载）:

```bash
cd docker
docker compose -f docker-compose.dev.yml up -d
```

### 构建镜像

```bash
# 构建所有镜像
docker compose build

# 仅构建前端
docker compose build frontend

# 仅构建后端
docker compose build backend
```

### 常用命令

```bash
# 查看日志
docker compose logs -f

# 停止服务
docker compose down

# 停止并删除数据卷
docker compose down -v

# 进入容器
docker compose exec backend bash
docker compose exec frontend sh
```

## 环境变量说明

创建 `.env` 文件（从 `.env.example` 复制）:

```bash
cp .env.example .env
```

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SECRET_KEY` | 应用密钥，生产环境必须修改 | - |
| `DEBUG` | 调试模式 | `false` |
| `DATABASE_URL` | 数据库连接字符串 | SQLite |
| `CORS_ORIGINS` | 允许的跨域来源 | - |
| `OPENAI_API_KEY` | OpenAI API 密钥 | - |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | - |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | - |
| `MOONSHOT_API_KEY` | Moonshot API 密钥 | - |
| `OPENROUTER_API_KEY` | OpenRouter API 密钥 | - |
| `DEFAULT_MODEL` | 默认使用的模型 | `gpt-4o-mini` |

### 生产环境注意事项

1. **SECRET_KEY**: 必须设置为随机字符串
   ```bash
   # 生成随机密钥
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **DATABASE_URL**: 建议使用 PostgreSQL
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
   ```

3. **CORS_ORIGINS**: 限制为你的域名
   ```
   CORS_ORIGINS=https://your-domain.com
   ```

## 常见问题

### 1. 端口被占用

**问题**: `Address already in use: 8000` 或 `5173`

**解决**:
```bash
# 查找占用端口的进程
# Linux/macOS
lsof -i :8000
# Windows
netstat -ano | findstr :8000

# 杀死进程或使用其他端口
uvicorn app.main:app --port 8001
```

### 2. Python 版本不兼容

**问题**: `Python version 3.x is installed, but Python 3.11+ is required`

**解决**: 安装 Python 3.11 或更高版本

### 3. Node.js 版本不兼容

**问题**: `Node.js version x is installed, but Node.js 20+ is required`

**解决**: 安装 Node.js 20 或更高版本

### 4. 前端构建失败

**问题**: `npm run build` 失败

**解决**:
```bash
# 清除缓存重新安装
rm -rf node_modules package-lock.json
npm install
npm run build
```

### 5. Docker 容器无法启动

**问题**: 容器启动后立即退出

**解决**:
```bash
# 查看容器日志
docker compose logs backend
docker compose logs frontend

# 检查健康状态
docker compose ps
```

### 6. API 请求失败 (CORS 错误)

**问题**: 前端无法访问后端 API

**解决**: 确保 `CORS_ORIGINS` 包含前端地址
```bash
# .env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 7. 数据库迁移问题

**问题**: 数据库表不存在

**解决**:
```bash
cd backend
alembic upgrade head
```

---

如有其他问题，请提交 Issue 或查看项目文档。

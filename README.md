# HTML Hoster - 静态网站托管平台

一个简单优雅的静态网站托管平台，支持快速部署 HTML 网站到阿里云 OSS。

![HTML Hoster](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-Latest-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ 特性

- 🚀 **快速部署** - 支持 ZIP 文件上传和 HTML 代码粘贴
- 🌐 **云端托管** - 基于阿里云 OSS 的可靠存储
- 🎨 **现代化 UI** - 响应式设计，支持移动端
- 💾 **数据持久化** - SQLite 数据库存储站点信息
- 🔧 **易于管理** - 支持站点重命名和删除
- 📊 **API 支持** - RESTful API 接口

## 🛠️ 技术栈

- **后端**: Python 3.10+, Flask, SQLAlchemy
- **前端**: HTML5, CSS3, JavaScript (原生)
- **存储**: 阿里云 OSS
- **数据库**: SQLite
- **服务器**: Waitress (生产环境)
- **容器化**: Docker

## 📋 环境要求

- Python 3.10 或更高版本
- 阿里云 OSS 账号和配置
- Docker (可选，用于容器化部署)

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/html_hoster.git
cd html_hoster
```

### 2. 安装依赖

使用 uv (推荐):
```bash
# 安装 uv
pip install uv

# 安装项目依赖（会自动创建虚拟环境）
uv sync
```

如果是开发环境，可以安装开发依赖：
```bash
uv sync --extra dev
```

### 3. 配置环境变量

创建 `.env` 文件并填写以下配置：

```env
# 阿里云 OSS 配置
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET_NAME=your_bucket_name

# 服务器配置
SERVER_WORKERS=4
```

### 4. 运行应用

```bash
# 使用 uv 运行
uv run python -m html_hoster
```

或者激活虚拟环境后运行：
```bash
# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 运行应用
python -m html_hoster
```

应用将在 `http://localhost:5000` 启动。

## 🐳 Docker 部署

### 构建镜像

```bash
docker build -t html_hoster .
```

### 运行容器

```bash
docker run -d \
  --name html_hoster \
  -p 5000:5000 \
  -e OSS_ACCESS_KEY_ID=your_key \
  -e OSS_ACCESS_KEY_SECRET=your_secret \
  -e OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com \
  -e OSS_BUCKET_NAME=your_bucket \
  -v $(pwd)/instance:/app/html_hoster/instance \
  -v $(pwd)/uploads:/app/uploads \
  html_hoster
```

## 📚 使用说明

### 上传 ZIP 文件

1. 准备一个包含 `index.html` 的 ZIP 压缩包
2. 在首页点击上传区域或拖拽文件
3. 点击"上传并发布"按钮
4. 站点将自动部署到云端

### 粘贴 HTML 代码

1. 在"粘贴代码"区域输入站点名称
2. 粘贴 HTML 源代码
3. 点击"发布网站"按钮
4. 系统将自动创建并部署站点

### 管理站点

- **预览**: 点击"预览"查看站点效果
- **OSS 链接**: 获取站点的直接访问链接
- **重命名**: 修改站点名称
- **删除**: 永久删除站点及其文件

## 🔌 API 接口

### 获取站点列表

```http
GET /api/sites
```

响应示例：
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "我的网站",
      "oss_url": "https://...",
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "count": 1
}
```

### 健康检查

```http
GET /health
```

## 📁 项目结构

```
html_hoster/
├── html_hoster/          # 主应用目录
│   ├── __main__.py      # 应用入口
│   ├── templates/       # HTML 模板
│   │   ├── index.html   # 首页
│   │   └── error.html   # 错误页面
│   └── instance/        # 数据库目录
├── uploads/             # 临时上传目录
├── pyproject.toml       # 项目配置
├── Dockerfile          # Docker 配置
├── README.md           # 项目文档
└── .env               # 环境变量（需创建）
```

## 🔒 安全特性

- 文件大小限制（ZIP: 50MB, HTML: 1MB）
- 解压后总大小限制（100MB）
- 文件类型验证
- 路径遍历防护
- SQL 注入防护

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [阿里云 OSS](https://www.aliyun.com/product/oss) - 对象存储服务
- [Remix Icon](https://remixicon.com/) - 图标库 
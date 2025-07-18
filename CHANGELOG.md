# 更新日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.6.0] - 2025-07-05

### 新增
- 🔄 添加数据库迁移功能，基于 Flask-Migrate
- 🛠️ 新增数据库迁移命令行工具
- 📊 支持数据库版本管理和历史记录查看
- 🔄 支持数据库结构的升级和回滚
- 🧰 添加 db-migrate 命令入口点

### 改进
- ⚡ 优化数据库初始化流程
- 🔧 简化数据库结构变更操作
- 📝 更新命令行接口，支持子命令

## [0.5.0] - 2025-07-03

### 新增
- 🚀 添加 Flask-Executor 支持，实现异步文件处理
- 📊 添加站点状态跟踪和显示功能
- 🔄 前端实时轮询站点处理状态
- 🗑️ 添加批量删除功能，提高文件删除效率
- 📡 新增站点状态 API 端点

### 改进
- ⚡ 优化文件上传处理流程，避免请求超时
- 🔧 上传过程原子化，确保一致性
- 🧹 移除不必要的 `time.sleep()` 调用
- 📝 更新文档，添加 Executor 配置说明
- 🔄 简化部署流程，无需额外的服务

## [0.4.0] - 2025-07-02

### 新增
- 🌐 添加 Supabase 存储服务支持
- 🗃️ 添加 Supabase PostgreSQL 数据库支持
- 🔄 支持在阿里云 OSS、S3 和 Supabase 存储之间灵活切换
- 🧩 完善存储服务抽象接口，增强可扩展性

### 改进
- ⚡ 优化 Supabase 集成流程
- 📝 更新文档，添加 Supabase 配置说明
- 🔧 简化 Supabase 存储桶管理

## [0.3.0] - 2025-07-02

### 新增
- 🗃️ 添加数据库抽象层，支持更好的模块化设计
- 🧩 将数据库操作从主文件中分离，提高代码可维护性

### 改进
- ⚡ 优化数据库初始化流程
- 🔧 简化主应用代码结构

## [0.2.0] - 2025-07-02

### 新增
- 🌐 添加 S3 兼容的对象存储服务支持
- 🧩 抽象存储服务接口，支持多种存储后端
- 🔄 支持在阿里云 OSS 和 S3 之间灵活切换

### 改进
- ⚡ 优化文件上传和下载逻辑
- 🔧 统一存储服务接口和错误处理
- 📝 更新文档，添加 S3 配置说明

## [0.1.0] - 2025-07-02

### 新增
- 🗄️ 添加 MySQL 数据库支持
- 🔄 支持在 SQLite 和 MySQL 之间灵活切换
- 🐳 Docker 镜像添加 MySQL 客户端库

### 改进
- ⚡ 优化数据库连接配置
- 📝 更新文档，添加 MySQL 配置说明

## [0.0.1] - 2025-07-02

### 新增
- 🎨 全新的现代化用户界面设计
- 🚀 支持拖拽上传 ZIP 文件功能
- 💻 响应式设计，完美支持移动端
- 🔄 实时加载动画和用户反馈
- 📱 Toast 消息提示系统
- 🎭 优雅的动画过渡效果
- 🛡️ 完善的错误处理页面
- 📊 新增 API 接口支持
- 🔍 健康检查端点
- 📝 详细的项目文档

### 改进
- ⚡ 优化文件上传处理逻辑
- 🔒 增强安全性验证（文件大小、类型检查）
- 📋 改进日志记录系统
- 🗄️ 数据库模型优化
- 🐳 Docker 配置优化
- 📦 项目依赖管理优化

### 修复
- 🐛 修复文件路径处理问题
- 🔧 修复站点删除时的错误处理
- 💾 修复数据库连接稳定性问题

### 技术改进
- 📁 重构项目结构
- 🧹 代码质量优化
- 📚 添加类型注解
- 🧪 改进错误处理机制
- 🔧 优化配置管理

### 安全
- 🛡️ 防止路径遍历攻击
- 🔐 文件上传安全验证
- 📏 文件大小限制
- 🚫 恶意文件检测

---

## 版本说明

- **Major**: 不兼容的 API 修改
- **Minor**: 向下兼容的功能性新增
- **Patch**: 向下兼容的问题修正 
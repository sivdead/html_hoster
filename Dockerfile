# 基于 Python 3.11 的轻量级镜像
FROM m.daocloud.io/docker.io/library/python:3.11.8-slim-bullseye

# 更新系统包以修复已知漏洞，并安装 MySQL 客户端库，最后清理构建缓存
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y default-libmysqlclient-dev build-essential pkg-config \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制项目文件到容器中
COPY . /app

# 安装 uv，并使用腾讯云镜像源
RUN pip install --upgrade pip -i https://mirrors.cloud.tencent.com/pypi/simple/ \
    && pip install uv -i https://mirrors.cloud.tencent.com/pypi/simple/

# 使用 uv 安装依赖（镜像源已在 pyproject.toml 中配置）
RUN uv pip install -e . --python $(which python) \
    && rm -rf /root/.cache/uv

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV STORAGE_TYPE=oss

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["python", "-m", "html_hoster"]

import os
import logging
from flask import Flask, render_template
import pymysql
from html_hoster.database import db, init_db
from html_hoster.auth import init_auth
from html_hoster.views import main_bp, site_bp
from html_hoster.auth_views import auth_bp
from html_hoster.config import get_config

# 加载配置
config = get_config()

# 设置 PyMySQL 作为 mysqlclient 的替代
pymysql.install_as_MySQLdb()

def create_app():
    """创建并配置Flask应用"""
    # 初始化 Flask 应用
    app = Flask(__name__, 
                template_folder=config.template_folder, 
                static_folder=config.static_folder)
    
    # 应用配置
    config.init_app(app)
    
    # 设置日志
    log_level = getattr(logging, app.config["LOG_LEVEL"])
    log_file = app.config["LOG_FILE"]
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # 确保上传目录和网站存储目录存在
    os.makedirs(config.upload_folder, exist_ok=True)
    os.makedirs(config.sites_folder, exist_ok=True)  # 确保网站存储目录存在
    logging.info(f"确保目录存在: 上传目录={config.upload_folder}, 网站目录={config.sites_folder}")
    
    # 初始化数据库
    init_db(app)
    
    # 初始化身份验证模块
    init_auth(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(site_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    return app


def register_error_handlers(app):
    """注册错误处理器"""
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return render_template("error.html", 
                             error_code=413,
                             error_message="文件太大",
                             error_detail="上传的文件超过了 50MB 的限制"), 413

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html",
                             error_code=404,
                             error_message="页面未找到",
                             error_detail="您访问的页面不存在"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("error.html",
                             error_code=500,
                             error_message="服务器内部错误",
                             error_detail="服务器遇到了一个错误，请稍后再试"), 500


def main():
    """应用入口点"""
    try:
        # 创建应用
        app = create_app()
        
        # 启动服务器
        from waitress import serve
        server_host = app.config["SERVER_HOST"]
        server_port = app.config["SERVER_PORT"]
        server_workers = app.config["SERVER_WORKERS"]
        logging.info(f"启动服务器，主机: {server_host}, 端口: {server_port}, 工作进程数: {server_workers}")
        serve(app, host=server_host, port=server_port, threads=server_workers)
    except Exception as e:
        logging.error(f"启动服务器失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

import os
import sys
import logging
import argparse
from flask import Flask, render_template
import pymysql
from html_hoster.database import db, init_db, migrate
from html_hoster.auth import init_auth
from html_hoster.views import main_bp, site_bp
from html_hoster.auth_views import auth_bp
from html_hoster.config import get_config
from html_hoster.tasks import init_executor

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
    
    # 初始化 Flask-Executor
    init_executor(app)
    
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


def run_db_migrations(command, message=None, revision=None):
    """运行数据库迁移命令"""
    app = create_app()
    with app.app_context():
        from flask_migrate import init, migrate, upgrade, downgrade, current, history
        
        if command == "init":
            logging.info("初始化数据库迁移环境...")
            init(directory="migrations")
            logging.info("数据库迁移环境初始化完成")
            
        elif command == "migrate":
            logging.info("创建数据库迁移脚本...")
            migrate(message=message)
            logging.info("数据库迁移脚本创建完成")
            
        elif command == "upgrade":
            rev = revision if revision else "head"
            logging.info(f"升级数据库到版本: {rev}")
            upgrade(revision=rev)
            logging.info("数据库升级完成")
            
        elif command == "downgrade":
            rev = revision if revision else "-1"
            logging.info(f"回滚数据库到版本: {rev}")
            downgrade(revision=rev)
            logging.info("数据库回滚完成")
            
        elif command == "history":
            logging.info("数据库迁移历史:")
            history()
            
        elif command == "current":
            logging.info("当前数据库版本:")
            current(verbose=True)


def main():
    """应用入口点"""
    parser = argparse.ArgumentParser(description='HTML Hoster - 静态网站托管平台')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 服务器命令
    server_parser = subparsers.add_parser('serve', help='启动 Web 服务器')
    
    # 数据库迁移命令
    db_parser = subparsers.add_parser('db', help='数据库迁移管理')
    db_parser.add_argument('action', choices=['init', 'migrate', 'upgrade', 'downgrade', 'history', 'current'],
                          help='数据库迁移操作')
    db_parser.add_argument('--message', '-m', help='迁移消息描述')
    db_parser.add_argument('--revision', '-r', help='指定迁移版本')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'db':
            # 运行数据库迁移命令
            run_db_migrations(args.action, args.message, args.revision)
        else:
            # 默认启动服务器
            app = create_app()
            # 启动服务器
            from waitress import serve
            server_host = app.config["SERVER_HOST"]
            server_port = app.config["SERVER_PORT"]
            server_workers = app.config["SERVER_WORKERS"]
            logging.info(f"启动服务器，主机: {server_host}, 端口: {server_port}, 工作进程数: {server_workers}")
            serve(app, host=server_host, port=server_port, threads=server_workers)
    except Exception as e:
        logging.error(f"执行命令失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

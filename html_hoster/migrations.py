"""
数据库迁移管理模块
"""
import os
import logging
import argparse
from flask import Flask
from html_hoster.config import load_config
from html_hoster.database import db, migrate


def create_app():
    """创建用于迁移的Flask应用实例"""
    app = Flask(__name__)
    # 加载配置
    load_config(app)
    # 初始化数据库
    db.init_app(app)
    # 初始化迁移
    migrate.init_app(app, db)
    return app


def main():
    """数据库迁移命令行入口"""
    parser = argparse.ArgumentParser(description="HTML Hoster 数据库迁移工具")
    parser.add_argument("command", choices=["init", "migrate", "upgrade", "downgrade", "history", "current"],
                        help="迁移命令")
    parser.add_argument("--message", "-m", help="迁移消息，用于描述此次迁移的内容")
    parser.add_argument("--revision", "-r", help="指定修订版本，用于upgrade/downgrade")
    args = parser.parse_args()

    # 创建应用
    app = create_app()
    
    # 在应用上下文中执行命令
    with app.app_context():
        from flask_migrate import init, migrate as create_migration, upgrade as upgrade_db
        from flask_migrate import downgrade as downgrade_db, current as show_current, history as show_history
        
        if args.command == "init":
            # 初始化迁移
            logging.info("初始化数据库迁移环境...")
            init(directory="migrations")
            logging.info("数据库迁移环境初始化完成")
        
        elif args.command == "migrate":
            # 创建迁移脚本
            logging.info("创建数据库迁移脚本...")
            create_migration(message=args.message)
            logging.info("数据库迁移脚本创建完成，请检查生成的迁移脚本并应用")
        
        elif args.command == "upgrade":
            # 升级数据库
            revision = args.revision or "head"
            logging.info(f"正在升级数据库到版本: {revision}")
            upgrade_db(revision=revision)
            logging.info("数据库升级完成")
        
        elif args.command == "downgrade":
            # 回滚数据库
            revision = args.revision or "-1"
            logging.info(f"正在回滚数据库到版本: {revision}")
            downgrade_db(revision=revision)
            logging.info("数据库回滚完成")
        
        elif args.command == "history":
            # 显示迁移历史
            logging.info("数据库迁移历史:")
            show_history()
        
        elif args.command == "current":
            # 显示当前版本
            logging.info("当前数据库版本:")
            show_current(verbose=True)


if __name__ == "__main__":
    main() 
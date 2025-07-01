"""
数据库模块 - 支持多种数据库后端
"""
import os
import logging
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

# 初始化 SQLAlchemy 对象
db = SQLAlchemy()


def init_db(app: Flask):
    """
    初始化数据库配置
    
    参数:
        app: Flask 应用实例
    """
    # 数据库路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "./instance/sites.db"))
    
    # 确保数据库目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # 数据库配置
    DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()

    if DB_TYPE == "mysql":
        # MySQL 配置
        MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
        MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
        MYSQL_USER = os.getenv("MYSQL_USER", "root")
        MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
        MYSQL_DB = os.getenv("MYSQL_DB", "html_hoster")
        
        app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
        logging.info(f"使用 MySQL 数据库: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")
    else:
        # SQLite 配置（默认）
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
        logging.info(f"使用 SQLite 数据库: {DB_PATH}")

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # 初始化数据库
    db.init_app(app)
    
    # 在应用上下文中创建所有表
    with app.app_context():
        db.create_all()
        if DB_TYPE == "mysql":
            logging.info(f"MySQL 数据库初始化完成: {os.getenv('MYSQL_HOST', 'localhost')}:{os.getenv('MYSQL_PORT', '3306')}/{os.getenv('MYSQL_DB', 'html_hoster')}")
        else:
            logging.info(f"SQLite 数据库初始化完成: {DB_PATH}")


# 站点模型
class Site(db.Model):
    """站点模型"""
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    oss_url = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Site {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "oss_url": self.oss_url,
            "created_at": self.created_at.isoformat() if self.created_at else None
        } 
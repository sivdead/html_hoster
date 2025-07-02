"""
数据库模块 - 支持多种数据库后端
"""
import os
import logging
from datetime import datetime
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
    # 获取数据库配置
    db_type = app.config["DB_TYPE"]
    
    # 确保数据库目录存在
    if db_type == "sqlite":
        sqlite_path = app.config["SQLITE_DB_PATH"]
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    
    # 初始化数据库
    db.init_app(app)
    
    # 在应用上下文中创建所有表
    with app.app_context():
        db.create_all()
        if db_type == "mysql":
            logging.info(f"MySQL 数据库初始化完成: {app.config['MYSQL_HOST']}:{app.config['MYSQL_PORT']}/{app.config['MYSQL_DB']}")
        elif db_type == "supabase":
            logging.info(f"Supabase PostgreSQL 数据库初始化完成: {app.config['SUPABASE_DB_HOST']}:{app.config['SUPABASE_DB_PORT']}/{app.config['SUPABASE_DB_NAME']}")
        else:
            logging.info(f"SQLite 数据库初始化完成: {app.config['SQLITE_DB_PATH']}")


# 用户模型
class User(db.Model):
    """用户模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # 用户创建的站点
    sites = db.relationship('Site', backref='owner', lazy=True)
    
    def __repr__(self):
        return f"<User {self.username}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }


# 站点模型
class Site(db.Model):
    """站点模型"""
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    oss_url = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = db.Column(db.Text, nullable=True)
    is_published = db.Column(db.Boolean, default=True)
    
    # 外键关联用户
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __repr__(self):
        return f"<Site {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "oss_url": self.oss_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "description": self.description,
            "is_published": self.is_published,
            "user_id": self.user_id
        } 
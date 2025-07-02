"""
配置模块 - 使用 pydantic-settings 管理应用的所有配置项
"""
import os
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any

from pydantic import field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

# 基础目录设置
BASE_DIR = Path(__file__).parent.resolve()
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR.parent / "uploads"
SITES_DIR = BASE_DIR.parent / "sites"  # 新增网站存储目录


class DatabaseType(str, Enum):
    """数据库类型枚举"""
    SQLITE = "sqlite"
    MYSQL = "mysql"
    SUPABASE = "supabase"


class StorageType(str, Enum):
    """存储类型枚举"""
    LOCAL = "local"
    OSS = "oss"
    S3 = "s3"
    SUPABASE = "supabase"


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class BaseConfig(BaseSettings):
    """基础配置模型"""
    # 应用设置
    app_name: str = "HTML Hoster"
    secret_key: str = "dev_key_please_change_in_production"
    server_host: str = "0.0.0.0"
    server_port: int = 5000
    server_workers: int = 4
    debug: bool = False
    testing: bool = False
    max_content_length: int = 50 * 1024 * 1024  # 50MB 最大上传大小
    
    # 基本目录设置
    base_dir: Path = BASE_DIR
    template_folder: Path = TEMPLATE_DIR
    static_folder: Path = STATIC_DIR
    upload_folder: Path = UPLOAD_DIR
    sites_folder: Path = SITES_DIR  # 新增网站存储目录
    
    # 日志设置
    log_level: LogLevel = LogLevel.INFO
    log_file: str = "app.log"
    
    # 数据库设置
    db_type: DatabaseType = DatabaseType.SQLITE
    sqlalchemy_track_modifications: bool = False
    sqlite_db_path: Path = BASE_DIR / "instance" / "sites.db"

    # MySQL 设置
    mysql_host: str = "localhost"
    mysql_port: str = "3306"
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_db: str = "html_hoster"

    # Supabase PostgreSQL 设置
    supabase_db_host: Optional[str] = None
    supabase_db_port: str = "5432"
    supabase_db_user: Optional[str] = None
    supabase_db_password: Optional[str] = None
    supabase_db_name: str = "postgres"
    supabase_db_schema: str = "public"

    # 存储服务设置
    storage_type: StorageType = StorageType.LOCAL

    # 阿里云OSS设置
    oss_access_key_id: Optional[str] = None
    oss_access_key_secret: Optional[str] = None
    oss_endpoint: Optional[str] = None
    oss_bucket_name: Optional[str] = None
    oss_prefix: str = "html_hoster/sites"

    # S3存储设置
    s3_access_key_id: Optional[str] = None
    s3_secret_access_key: Optional[str] = None
    s3_endpoint_url: Optional[str] = None
    s3_region_name: str = "us-east-1"
    s3_bucket_name: Optional[str] = None
    s3_prefix: str = "html_hoster/sites"
    s3_use_ssl: bool = True

    # Supabase存储设置
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_bucket: str = "sites"
    
    # Executor 设置
    executor_type: str = "thread"
    executor_max_workers: int = 4

    # 从环境变量加载配置
    model_config = SettingsConfigDict(
        env_prefix="", 
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def sqlalchemy_database_uri(self) -> str:
        """根据数据库类型获取数据库URI"""
        if self.db_type == DatabaseType.MYSQL:
            return f"mysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"
        elif self.db_type == DatabaseType.SUPABASE:
            return f"postgresql://{self.supabase_db_user}:{self.supabase_db_password}@{self.supabase_db_host}:{self.supabase_db_port}/{self.supabase_db_name}"
        else:
            # SQLite (默认)
            return f"sqlite:///{self.sqlite_db_path}"
    
    @property
    def sqlalchemy_engine_options(self) -> Dict[str, Any]:
        """获取SQLAlchemy引擎选项"""
        if self.db_type == DatabaseType.SUPABASE:
            return {
                "connect_args": {
                    "options": f"-csearch_path={self.supabase_db_schema}"
                }
            }
        return {}
    
    def to_flask_config(self) -> Dict[str, Any]:
        """转换为Flask配置字典"""
        # 基础配置
        config = {
            "SECRET_KEY": self.secret_key,
            "SERVER_HOST": self.server_host,
            "SERVER_PORT": self.server_port,
            "SERVER_WORKERS": self.server_workers,
            "DEBUG": self.debug,
            "TESTING": self.testing,
            "MAX_CONTENT_LENGTH": self.max_content_length,
            
            # 基本目录设置
            "BASE_DIR": self.base_dir,
            "TEMPLATE_FOLDER": self.template_folder,
            "STATIC_FOLDER": self.static_folder,
            "UPLOAD_FOLDER": self.upload_folder,
            "SITES_FOLDER": self.sites_folder,  # 新增网站存储目录
            
            # 日志设置
            "LOG_LEVEL": self.log_level.value,
            "LOG_FILE": self.log_file,
            
            # 数据库设置
            "DB_TYPE": self.db_type.value,
            "SQLALCHEMY_TRACK_MODIFICATIONS": self.sqlalchemy_track_modifications,
            "SQLALCHEMY_DATABASE_URI": self.sqlalchemy_database_uri,
        }
        
        # 添加引擎选项（如果有）
        if self.sqlalchemy_engine_options:
            config["SQLALCHEMY_ENGINE_OPTIONS"] = self.sqlalchemy_engine_options
        
        # 数据库特定配置
        if self.db_type == DatabaseType.SQLITE:
            config["SQLITE_DB_PATH"] = self.sqlite_db_path
        elif self.db_type == DatabaseType.MYSQL:
            config["MYSQL_HOST"] = self.mysql_host
            config["MYSQL_PORT"] = self.mysql_port
            config["MYSQL_USER"] = self.mysql_user
            config["MYSQL_PASSWORD"] = self.mysql_password
            config["MYSQL_DB"] = self.mysql_db
        elif self.db_type == DatabaseType.SUPABASE:
            config["SUPABASE_DB_HOST"] = self.supabase_db_host
            config["SUPABASE_DB_PORT"] = self.supabase_db_port
            config["SUPABASE_DB_USER"] = self.supabase_db_user
            config["SUPABASE_DB_PASSWORD"] = self.supabase_db_password
            config["SUPABASE_DB_NAME"] = self.supabase_db_name
            config["SUPABASE_DB_SCHEMA"] = self.supabase_db_schema
        
        # 存储服务设置
        config["STORAGE_TYPE"] = self.storage_type.value
        
        # 阿里云OSS设置
        config["OSS_ACCESS_KEY_ID"] = self.oss_access_key_id
        config["OSS_ACCESS_KEY_SECRET"] = self.oss_access_key_secret
        config["OSS_ENDPOINT"] = self.oss_endpoint
        config["OSS_BUCKET_NAME"] = self.oss_bucket_name
        config["OSS_PREFIX"] = self.oss_prefix
        
        # S3存储设置
        config["S3_ACCESS_KEY_ID"] = self.s3_access_key_id
        config["S3_SECRET_ACCESS_KEY"] = self.s3_secret_access_key
        config["S3_ENDPOINT_URL"] = self.s3_endpoint_url
        config["S3_REGION_NAME"] = self.s3_region_name
        config["S3_BUCKET_NAME"] = self.s3_bucket_name
        config["S3_PREFIX"] = self.s3_prefix
        config["S3_USE_SSL"] = self.s3_use_ssl
        
        # Supabase存储设置
        config["SUPABASE_URL"] = self.supabase_url
        config["SUPABASE_KEY"] = self.supabase_key
        config["SUPABASE_BUCKET"] = self.supabase_bucket
        
        # Executor 设置
        config["EXECUTOR_TYPE"] = self.executor_type
        config["EXECUTOR_MAX_WORKERS"] = self.executor_max_workers
        
        return config
    
    def init_app(self, app):
        """初始化应用配置"""
        app.config.update(self.to_flask_config())


class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    debug: bool = True
    log_level: LogLevel = LogLevel.DEBUG


class TestingConfig(BaseConfig):
    """测试环境配置"""
    testing: bool = True
    debug: bool = True
    sqlite_db_path: str = ":memory:"


class ProductionConfig(BaseConfig):
    """生产环境配置"""
    log_level: LogLevel = LogLevel.WARNING


# 配置字典，映射环境名到配置类
CONFIG_CLASSES = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    
    # 默认配置
    "default": DevelopmentConfig
}


def get_config() -> BaseConfig:
    """获取当前环境配置"""
    env = os.getenv("FLASK_ENV", "development").lower()
    config_class = CONFIG_CLASSES.get(env, CONFIG_CLASSES["default"])
    return config_class() 
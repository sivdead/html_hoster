"""
存储服务模块 - 支持多种对象存储服务
"""
import os
import logging
import shutil
from abc import ABC, abstractmethod
from urllib.parse import urlparse
import mimetypes
from flask import current_app, send_from_directory


class StorageService(ABC):
    """存储服务抽象基类"""
    
    @abstractmethod
    def upload_file(self, local_path, remote_path, content_type=None):
        """上传文件到存储服务"""
        pass
    
    @abstractmethod
    def download_file(self, remote_path):
        """从存储服务下载文件"""
        pass
    
    @abstractmethod
    def delete_file(self, remote_path):
        """从存储服务删除文件"""
        pass
    
    @abstractmethod
    def list_files(self, prefix):
        """列出指定前缀的所有文件"""
        pass
    
    @abstractmethod
    def get_file_url(self, remote_path):
        """获取文件的访问URL"""
        pass
    
    @abstractmethod
    def get_site_url(self, site_id):
        """获取站点的访问URL"""
        pass


class AliOssStorage(StorageService):
    """阿里云OSS存储服务实现"""
    
    def __init__(self, app):
        """初始化阿里云OSS存储服务"""
        import oss2
        
        self.access_key_id = app.config["OSS_ACCESS_KEY_ID"]
        self.access_key_secret = app.config["OSS_ACCESS_KEY_SECRET"]
        self.endpoint = app.config["OSS_ENDPOINT"]
        self.bucket_name = app.config["OSS_BUCKET_NAME"]
        self.prefix = app.config["OSS_PREFIX"]
        
        # 初始化OSS客户端
        auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        self.bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
        logging.info(f"初始化阿里云OSS存储服务: {self.bucket_name}.{self.endpoint}")
    
    def upload_file(self, local_path, remote_path, content_type=None):
        """上传文件到OSS"""
        import oss2
        
        # 规范化路径
        remote_path = os.path.join(self.prefix, remote_path).replace("\\", "/")
        
        # 设置Content-Type
        headers = {}
        if content_type:
            headers['Content-Type'] = content_type
        elif local_path:
            content_type, _ = mimetypes.guess_type(local_path)
            if content_type:
                headers['Content-Type'] = content_type
        
        try:
            if os.path.exists(local_path):
                self.bucket.put_object_from_file(remote_path, local_path, headers=headers)
            else:
                raise FileNotFoundError(f"本地文件不存在: {local_path}")
            
            logging.info(f"成功上传文件到OSS: {remote_path}")
            return True
        except Exception as e:
            logging.error(f"上传文件到OSS失败 {remote_path}: {e}")
            raise
    
    def download_file(self, remote_path):
        """从OSS下载文件"""
        import oss2
        
        # 规范化路径
        remote_path = os.path.join(self.prefix, remote_path).replace("\\", "/")
        
        try:
            result = self.bucket.get_object(remote_path)
            content = result.read()
            
            # 获取Content-Type
            content_type = result.headers.get('Content-Type')
            
            logging.info(f"成功从OSS下载文件: {remote_path}")
            return content, content_type
        except oss2.exceptions.NoSuchKey:
            logging.warning(f"OSS文件不存在: {remote_path}")
            return None, None
        except Exception as e:
            logging.error(f"从OSS下载文件失败 {remote_path}: {e}")
            raise
    
    def delete_file(self, remote_path):
        """从OSS删除文件"""
        import oss2
        
        # 规范化路径
        remote_path = os.path.join(self.prefix, remote_path).replace("\\", "/")
        
        try:
            self.bucket.delete_object(remote_path)
            logging.info(f"成功从OSS删除文件: {remote_path}")
            return True
        except Exception as e:
            logging.error(f"从OSS删除文件失败 {remote_path}: {e}")
            raise
    
    def list_files(self, prefix):
        """列出指定前缀的所有文件"""
        import oss2
        
        # 规范化路径
        full_prefix = os.path.join(self.prefix, prefix).replace("\\", "/")
        
        try:
            files = []
            for obj in oss2.ObjectIterator(self.bucket, prefix=full_prefix):
                # 移除前缀，获取相对路径
                relative_path = obj.key[len(self.prefix) + 1:] if obj.key.startswith(self.prefix) else obj.key
                files.append(relative_path)
            
            logging.info(f"成功列出OSS文件: {len(files)} 个")
            return files
        except Exception as e:
            logging.error(f"列出OSS文件失败 {full_prefix}: {e}")
            raise
    
    def get_file_url(self, remote_path):
        """获取OSS文件的访问URL"""
        # 规范化路径
        remote_path = os.path.join(self.prefix, remote_path).replace("\\", "/")
        return f"https://{self.bucket_name}.{self.endpoint}/{remote_path}"
    
    def get_site_url(self, site_id):
        """获取站点的访问URL"""
        return self.get_file_url(f"{site_id}/index.html")


class S3Storage(StorageService):
    """S3兼容的存储服务实现"""
    
    def __init__(self, app):
        """初始化S3存储服务"""
        import boto3
        
        self.access_key_id = app.config["S3_ACCESS_KEY_ID"]
        self.secret_access_key = app.config["S3_SECRET_ACCESS_KEY"]
        self.endpoint_url = app.config["S3_ENDPOINT_URL"]
        self.region_name = app.config["S3_REGION_NAME"]
        self.bucket_name = app.config["S3_BUCKET_NAME"]
        self.prefix = app.config["S3_PREFIX"]
        self.use_ssl = app.config["S3_USE_SSL"]
        
        # 初始化S3客户端
        self.s3 = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region_name,
            use_ssl=self.use_ssl
        )
        
        self.s3_resource = boto3.resource(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region_name,
            use_ssl=self.use_ssl
        )
        
        self.bucket = self.s3_resource.Bucket(self.bucket_name)
        
        logging.info(f"初始化S3存储服务: {self.bucket_name} ({self.endpoint_url})")
    
    def upload_file(self, local_path, remote_path, content_type=None):
        """上传文件到S3"""
        # 规范化路径
        remote_path = os.path.join(self.prefix, remote_path).replace("\\", "/")
        
        # 设置Content-Type
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        elif local_path:
            content_type, _ = mimetypes.guess_type(local_path)
            if content_type:
                extra_args['ContentType'] = content_type
        
        try:
            if os.path.exists(local_path):
                self.s3.upload_file(
                    local_path, 
                    self.bucket_name, 
                    remote_path,
                    ExtraArgs=extra_args
                )
            else:
                raise FileNotFoundError(f"本地文件不存在: {local_path}")
            
            logging.info(f"成功上传文件到S3: {remote_path}")
            return True
        except Exception as e:
            logging.error(f"上传文件到S3失败 {remote_path}: {e}")
            raise
    
    def download_file(self, remote_path):
        """从S3下载文件"""
        # 规范化路径
        remote_path = os.path.join(self.prefix, remote_path).replace("\\", "/")
        
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=remote_path)
            content = response['Body'].read()
            content_type = response.get('ContentType')
            
            logging.info(f"成功从S3下载文件: {remote_path}")
            return content, content_type
        except self.s3.exceptions.NoSuchKey:
            logging.warning(f"S3文件不存在: {remote_path}")
            return None, None
        except Exception as e:
            logging.error(f"从S3下载文件失败 {remote_path}: {e}")
            raise
    
    def delete_file(self, remote_path):
        """从S3删除文件"""
        # 规范化路径
        remote_path = os.path.join(self.prefix, remote_path).replace("\\", "/")
        
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=remote_path)
            logging.info(f"成功从S3删除文件: {remote_path}")
            return True
        except Exception as e:
            logging.error(f"从S3删除文件失败 {remote_path}: {e}")
            raise
    
    def list_files(self, prefix):
        """列出指定前缀的所有文件"""
        # 规范化路径
        full_prefix = os.path.join(self.prefix, prefix).replace("\\", "/")
        
        try:
            files = []
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=full_prefix
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    # 移除前缀，获取相对路径
                    relative_path = obj['Key'][len(self.prefix) + 1:] if obj['Key'].startswith(self.prefix) else obj['Key']
                    files.append(relative_path)
            
            logging.info(f"成功列出S3文件: {len(files)} 个")
            return files
        except Exception as e:
            logging.error(f"列出S3文件失败 {full_prefix}: {e}")
            raise
    
    def get_file_url(self, remote_path):
        """获取S3文件的访问URL"""
        # 规范化路径
        remote_path = os.path.join(self.prefix, remote_path).replace("\\", "/")
        
        # 解析endpoint_url以获取正确的域名格式
        parsed_url = urlparse(self.endpoint_url)
        hostname = parsed_url.netloc
        
        # 根据不同的S3兼容服务调整URL格式
        if hostname.endswith('amazonaws.com'):
            # 标准AWS S3
            return f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{remote_path}"
        else:
            # 其他S3兼容服务
            scheme = 'https' if self.use_ssl else 'http'
            return f"{scheme}://{hostname}/{self.bucket_name}/{remote_path}"
    
    def get_site_url(self, site_id):
        """获取站点的访问URL"""
        return self.get_file_url(f"{site_id}/index.html")


class SupabaseStorage(StorageService):
    """Supabase存储服务实现"""
    
    def __init__(self, app):
        """初始化Supabase存储服务"""
        from supabase import create_client, Client
        
        self.supabase_url = app.config["SUPABASE_URL"]
        self.supabase_key = app.config["SUPABASE_KEY"]
        self.bucket_name = app.config["SUPABASE_BUCKET"]
        self.prefix = "sites"
        
        # 初始化Supabase客户端
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # 确保存储桶存在
        self._ensure_bucket_exists()
        
        logging.info(f"初始化Supabase存储服务: {self.bucket_name}")
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在，不存在则创建"""
        try:
            # 获取所有桶
            buckets = self.supabase.storage.list_buckets()
            bucket_names = [bucket["name"] for bucket in buckets]
            
            # 如果桶不存在，则创建
            if self.bucket_name not in bucket_names:
                self.supabase.storage.create_bucket(self.bucket_name, {"public": True})
                logging.info(f"创建Supabase存储桶: {self.bucket_name}")
        except Exception as e:
            logging.error(f"检查/创建Supabase存储桶失败: {e}")
            raise
    
    def upload_file(self, local_path, remote_path, content_type=None):
        """上传文件到Supabase存储"""
        # 规范化路径
        remote_path = os.path.join(self.prefix, remote_path).replace("\\", "/")
        
        try:
            if os.path.exists(local_path):
                with open(local_path, "rb") as file:
                    file_content = file.read()
                    
                    # 上传文件
                    self.supabase.storage.from_(self.bucket_name).upload(
                        remote_path,
                        file_content,
                        {"content-type": content_type or mimetypes.guess_type(local_path)[0] or "application/octet-stream"}
                    )
            else:
                raise FileNotFoundError(f"本地文件不存在: {local_path}")
            
            logging.info(f"成功上传文件到Supabase: {remote_path}")
            return True
        except Exception as e:
            logging.error(f"上传文件到Supabase失败 {remote_path}: {e}")
            raise
    
    def download_file(self, remote_path):
        """从Supabase下载文件"""
        # 规范化路径
        remote_path = os.path.join(self.prefix, remote_path).replace("\\", "/")
        
        try:
            # 下载文件
            response = self.supabase.storage.from_(self.bucket_name).download(remote_path)
            
            # 获取Content-Type
            content_type = None  # Supabase API不直接返回Content-Type，需要额外请求
            
            logging.info(f"成功从Supabase下载文件: {remote_path}")
            return response, content_type
        except Exception as e:
            logging.error(f"从Supabase下载文件失败 {remote_path}: {e}")
            if "404" in str(e):
                return None, None
            raise
    
    def delete_file(self, remote_path):
        """从Supabase删除文件"""
        # 规范化路径
        remote_path = os.path.join(self.prefix, remote_path).replace("\\", "/")
        
        try:
            self.supabase.storage.from_(self.bucket_name).remove([remote_path])
            logging.info(f"成功从Supabase删除文件: {remote_path}")
            return True
        except Exception as e:
            logging.error(f"从Supabase删除文件失败 {remote_path}: {e}")
            raise
    
    def list_files(self, prefix):
        """列出指定前缀的所有文件"""
        # 规范化路径
        full_prefix = os.path.join(self.prefix, prefix).replace("\\", "/")
        
        try:
            # 列出文件
            response = self.supabase.storage.from_(self.bucket_name).list(full_prefix)
            
            files = []
            for item in response:
                # 移除前缀，获取相对路径
                name = item.get("name", "")
                if name:
                    relative_path = name[len(self.prefix) + 1:] if name.startswith(self.prefix) else name
                    files.append(relative_path)
            
            logging.info(f"成功列出Supabase文件: {len(files)} 个")
            return files
        except Exception as e:
            logging.error(f"列出Supabase文件失败 {full_prefix}: {e}")
            raise
    
    def get_file_url(self, remote_path):
        """获取Supabase文件的访问URL"""
        # 规范化路径
        remote_path = os.path.join(self.prefix, remote_path).replace("\\", "/")
        
        try:
            # 获取公共URL
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(remote_path)
            return public_url
        except Exception as e:
            logging.error(f"获取Supabase文件URL失败 {remote_path}: {e}")
            # 返回一个构造的URL（可能不准确）
            return f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{remote_path}"
    
    def get_site_url(self, site_id):
        """获取站点的访问URL"""
        return self.get_file_url(f"{site_id}/index.html")


class LocalStorage(StorageService):
    """本地文件存储服务实现"""
    
    def __init__(self, app):
        """初始化本地文件存储服务"""
        self.upload_folder = app.config["UPLOAD_FOLDER"]
        self.sites_folder = app.config["SITES_FOLDER"]  # 新增网站存储目录
        self.base_url = app.config.get("SERVER_NAME", "localhost:5000")
        self.scheme = "http"
        
        # 确保存储目录存在
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.sites_folder, exist_ok=True)  # 确保网站目录存在
        logging.info(f"初始化本地文件存储服务: 上传目录={self.upload_folder}, 网站目录={self.sites_folder}")
    
    def upload_file(self, local_path, remote_path, content_type=None):
        """上传文件到本地存储"""
        # 规范化路径 - 存储到网站目录
        dest_path = os.path.join(self.sites_folder, remote_path)
        dest_dir = os.path.dirname(dest_path)
        
        try:
            # 确保目标目录存在
            os.makedirs(dest_dir, exist_ok=True)
            
            # 添加重试机制，解决Windows文件锁定问题
            max_retries = 3
            retry_delay = 1.0  # 初始延迟1秒
            
            for attempt in range(max_retries):
                try:
                    # 在复制前尝试强制释放资源 (仅Windows系统)
                    if os.name == 'nt':
                        import gc
                        gc.collect()  # 强制垃圾收集，关闭任何未使用的文件句柄
                        
                    # 使用缓冲区方式复制文件，避免直接文件到文件复制可能的锁定问题
                    with open(local_path, 'rb') as src_file:
                        content = src_file.read()
                        
                    # 使用写入方式而不是直接复制，避免文件锁定问题
                    with open(dest_path, 'wb') as dest_file:
                        dest_file.write(content)
                    
                    logging.info(f"成功复制文件到网站存储目录: {dest_path}")
                    return True
                    
                except (PermissionError, OSError) as e:
                    # 如果是最后一次尝试，则抛出异常
                    if attempt == max_retries - 1:
                        raise
                    
                    # 否则等待后重试
                    logging.warning(f"复制文件失败，正在重试({attempt+1}/{max_retries}): {e}")
                    import time
                    time.sleep(retry_delay)
                    # 每次重试增加延迟时间
                    retry_delay *= 2
            
        except Exception as e:
            logging.error(f"复制文件到网站存储目录失败 {dest_path}: {e}")
            raise
    
    def download_file(self, remote_path):
        """从本地存储获取文件内容"""
        # 规范化路径 - 从网站目录读取
        file_path = os.path.join(self.sites_folder, remote_path)
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # 根据文件扩展名猜测Content-Type
                content_type, _ = mimetypes.guess_type(file_path)
                
                logging.info(f"成功从网站存储目录读取文件: {file_path}")
                return content, content_type
            else:
                logging.warning(f"网站文件不存在: {file_path}")
                return None, None
        except Exception as e:
            logging.error(f"从网站存储目录读取文件失败 {file_path}: {e}")
            raise
    
    def delete_file(self, remote_path):
        """从本地存储删除文件"""
        # 规范化路径 - 从网站目录删除
        file_path = os.path.join(self.sites_folder, remote_path)
        
        try:
            if os.path.exists(file_path):
                # 只删除单个文件，不删除目录
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    logging.info(f"成功从网站存储目录删除文件: {file_path}")
                    return True
                elif os.path.isdir(file_path):
                    logging.warning(f"尝试删除的路径是目录而不是文件: {file_path}")
                    return False
                else:
                    logging.warning(f"路径既不是文件也不是目录: {file_path}")
                    return False
            else:
                logging.warning(f"要删除的网站文件不存在: {file_path}")
                return False
        except Exception as e:
            logging.error(f"从网站存储目录删除文件失败 {file_path}: {e}")
            raise
    
    def list_files(self, prefix):
        """列出指定前缀的所有文件"""
        # 规范化路径 - 从网站目录列出
        prefix_path = os.path.join(self.sites_folder, prefix)
        
        try:
            files = []
            if os.path.exists(prefix_path) and os.path.isdir(prefix_path):
                for root, _, filenames in os.walk(prefix_path):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        # 计算相对路径
                        relative_path = os.path.relpath(file_path, self.sites_folder)
                        files.append(relative_path.replace("\\", "/"))
            
            logging.info(f"成功列出网站存储目录文件: {len(files)} 个")
            return files
        except Exception as e:
            logging.error(f"列出网站存储目录文件失败 {prefix_path}: {e}")
            raise
    
    def get_file_url(self, remote_path):
        """获取本地文件的访问URL"""
        # 使用相对URL，由前端负责组合完整URL
        return f"/site/{remote_path}"
    
    def get_site_url(self, site_id):
        """获取站点的访问URL"""
        return self.get_file_url(f"{site_id}/index.html")


def get_storage_service(app=None):
    """
    根据配置获取适当的存储服务实现
    
    Args:
        app: Flask应用实例，如果为None，则使用current_app
    
    返回:
        StorageService: 存储服务实例
    """
    from flask import current_app as flask_app
    
    # 确保有应用上下文
    app = app or flask_app
    
    storage_type = app.config["STORAGE_TYPE"].lower()
    
    if storage_type == "oss":
        return AliOssStorage(app)
    elif storage_type == "s3":
        return S3Storage(app)
    elif storage_type == "supabase":
        return SupabaseStorage(app)
    elif storage_type == "local":
        return LocalStorage(app)
    else:
        raise ValueError(f"不支持的存储类型: {storage_type}") 
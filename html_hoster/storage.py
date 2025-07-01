"""
存储服务模块 - 支持多种对象存储服务
"""
import os
import logging
from abc import ABC, abstractmethod
from urllib.parse import urlparse
import mimetypes


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
    
    def __init__(self):
        """初始化阿里云OSS存储服务"""
        import oss2
        
        self.access_key_id = os.getenv("OSS_ACCESS_KEY_ID")
        self.access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET")
        self.endpoint = os.getenv("OSS_ENDPOINT")
        self.bucket_name = os.getenv("OSS_BUCKET_NAME")
        self.prefix = os.getenv("OSS_PREFIX", "html_hoster/sites")
        
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
    
    def __init__(self):
        """初始化S3存储服务"""
        import boto3
        
        self.access_key_id = os.getenv("S3_ACCESS_KEY_ID")
        self.secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
        self.endpoint_url = os.getenv("S3_ENDPOINT_URL")
        self.region_name = os.getenv("S3_REGION_NAME", "us-east-1")
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.prefix = os.getenv("S3_PREFIX", "html_hoster/sites")
        self.use_ssl = os.getenv("S3_USE_SSL", "true").lower() == "true"
        
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


def get_storage_service():
    """
    根据环境变量配置获取合适的存储服务实例
    
    返回:
        StorageService: 存储服务实例
    """
    storage_type = os.getenv("STORAGE_TYPE", "oss").lower()
    
    if storage_type == "s3":
        return S3Storage()
    else:
        return AliOssStorage() 
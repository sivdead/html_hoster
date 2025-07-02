"""
任务模块 - 使用 Flask-Executor 处理异步任务
"""
import os
import zipfile
import logging
import uuid
import mimetypes
import shutil
from flask import current_app

from html_hoster.storage import get_storage_service
from html_hoster.database import db, Site

def init_executor(app):
    """初始化 Flask-Executor 与 Flask 应用集成"""
    from flask_executor import Executor
    executor = Executor(app)
    app.config['EXECUTOR_TYPE'] = 'thread'
    app.config['EXECUTOR_MAX_WORKERS'] = 4
    return executor

def process_zip_upload(zip_path, site_id, site_name, user_id):
    """处理 ZIP 文件上传的后台任务"""
    logging.info(f"开始处理 ZIP 上传任务: {site_id}")
    
    try:
        # 获取应用配置
        extract_path = os.path.join(current_app.config["UPLOAD_FOLDER"], site_id)
        os.makedirs(extract_path, exist_ok=True)
        
        # 验证 ZIP 文件
        if not zipfile.is_zipfile(zip_path):
            raise ValueError("无效的 ZIP 文件")
        
        # 解压文件
        logging.info(f"解压 ZIP 文件到: {extract_path}")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # 检查解压后的大小
            total_size = sum(zinfo.file_size for zinfo in zip_ref.filelist)
            if total_size > 100 * 1024 * 1024:  # 100MB
                raise ValueError("解压后文件总大小超过 100MB 限制")
            
            zip_ref.extractall(extract_path)
        
        # 查找 index.html
        index_html_path = None
        for root, dirs, files in os.walk(extract_path):
            if "index.html" in files:
                index_html_path = os.path.join(root, "index.html")
                break
        
        if not index_html_path:
            raise ValueError("ZIP 包中没有找到 index.html 文件")
        
        # 获取存储服务
        storage = get_storage_service(current_app)
        
        # 上传到存储服务
        uploaded_files = 0
        file_list = []
        
        # 首先收集所有文件路径
        for root, dirs, files in os.walk(extract_path):
            for filename in files:
                local_path = os.path.join(root, filename)
                relative_path = os.path.relpath(local_path, extract_path)
                remote_path = f"{site_id}/{relative_path}"
                content_type, _ = mimetypes.guess_type(filename)
                
                file_list.append({
                    'local_path': local_path,
                    'remote_path': remote_path,
                    'content_type': content_type
                })
        
        # 上传文件，如果任何一个文件上传失败，则回滚所有操作
        try:
            for file_info in file_list:
                storage.upload_file(
                    file_info['local_path'], 
                    file_info['remote_path'], 
                    file_info['content_type']
                )
                uploaded_files += 1
                logging.info(f"上传文件到存储服务: {file_info['remote_path']}")
        except Exception as e:
            # 上传失败，删除已上传的文件
            logging.error(f"上传文件失败，开始回滚: {e}")
            # 删除已上传的所有文件
            delete_site_files(site_id)
            raise
        
        logging.info(f"成功上传 {uploaded_files} 个文件到存储服务")
        
        # 保存到数据库
        site_url = storage.get_site_url(site_id)
        
        # 更新站点记录
        with current_app.app_context():
            site = Site.query.get(site_id)
            if site:
                site.oss_url = site_url
                site.status = "completed"
                db.session.commit()
                logging.info(f"成功创建站点: {site_name} (ID: {site_id})")
            else:
                logging.error(f"找不到站点记录: {site_id}")
        
    except Exception as e:
        logging.error(f"处理 ZIP 上传任务失败: {e}")
        # 更新站点状态为失败
        update_site_status(site_id, "failed", str(e))
    finally:
        # 清理临时文件
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
            if os.path.exists(extract_path):
                shutil.rmtree(extract_path)
            logging.info(f"清理临时文件完成: {zip_path}, {extract_path}")
        except Exception as e:
            logging.error(f"清理临时文件失败: {e}")


def process_html_paste(html_code, site_id, site_name, user_id):
    """处理粘贴 HTML 代码的后台任务"""
    logging.info(f"开始处理 HTML 粘贴任务: {site_id}")
    
    try:
        # 创建临时目录
        extract_path = os.path.join(current_app.config["UPLOAD_FOLDER"], site_id)
        os.makedirs(extract_path, exist_ok=True)
        
        # 保存 HTML 文件
        index_html_path = os.path.join(extract_path, "index.html")
        with open(index_html_path, "w", encoding="utf-8") as f:
            f.write(html_code)
        
        # 获取存储服务
        storage = get_storage_service(current_app)
        
        # 上传到存储服务
        remote_path = f"{site_id}/index.html"
        try:
            storage.upload_file(index_html_path, remote_path)
            logging.info(f"成功上传粘贴的 HTML 到存储服务: {remote_path}")
        except Exception as e:
            logging.error(f"存储服务上传失败: {e}")
            # 删除已上传的文件（如果有）
            try:
                storage.delete_file(remote_path)
            except:
                pass
            raise
        
        # 获取站点 URL
        site_url = storage.get_site_url(site_id)
        
        # 更新站点记录
        with current_app.app_context():
            site = Site.query.get(site_id)
            if site:
                site.oss_url = site_url
                site.status = "completed"
                db.session.commit()
                logging.info(f"成功创建粘贴站点: {site_name}")
            else:
                logging.error(f"找不到站点记录: {site_id}")
        
    except Exception as e:
        logging.error(f"处理 HTML 粘贴任务失败: {e}")
        # 更新站点状态为失败
        update_site_status(site_id, "failed", str(e))
    finally:
        # 清理临时文件
        try:
            if os.path.exists(index_html_path):
                os.remove(index_html_path)
            if os.path.exists(extract_path):
                os.rmdir(extract_path)
            logging.info(f"清理临时文件完成: {index_html_path}")
        except Exception as e:
            logging.error(f"清理临时文件失败: {e}")


def update_site_status(site_id, status, error_message=None):
    """更新站点状态"""
    try:
        with current_app.app_context():
            site = Site.query.get(site_id)
            if site:
                site.status = status
                if error_message:
                    site.error_message = error_message
                db.session.commit()
                logging.info(f"更新站点 {site_id} 状态为 {status}")
    except Exception as e:
        logging.error(f"更新站点状态失败: {e}")


def delete_site_files(site_id):
    """删除站点的所有文件"""
    try:
        storage = get_storage_service(current_app)
        # 使用存储服务的批量删除功能
        if hasattr(storage, 'delete_prefix'):
            storage.delete_prefix(site_id)
            logging.info(f"使用批量删除功能删除站点 {site_id} 的所有文件")
        else:
            # 回退到逐个文件删除
            files = storage.list_files(site_id)
            for file_path in files:
                storage.delete_file(f"{site_id}/{file_path}")
            logging.info(f"删除站点 {site_id} 的 {len(files)} 个文件")
    except Exception as e:
        logging.error(f"删除站点文件失败: {e}")
        raise 
"""
视图模块 - 使用Blueprint组织路由
"""
import os
import uuid
import zipfile
import logging
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, current_app, g, send_from_directory
from werkzeug.utils import secure_filename
import mimetypes
from html_hoster.storage import get_storage_service
from html_hoster.database import db, Site
from html_hoster.auth import login_required

# 创建Blueprint
main_bp = Blueprint('main', __name__)
site_bp = Blueprint('site', __name__, url_prefix='/site')

# 在请求上下文中获取存储服务
def get_storage():
    """获取存储服务实例，确保在请求上下文中访问"""
    if not hasattr(g, 'storage'):
        g.storage = get_storage_service()
    return g.storage

@main_bp.route("/")
def index():
    """首页"""
    logging.info("访问首页")
    try:
        user_id = session.get('user_id')
        if user_id:
            # 获取当前用户的站点
            sites = Site.query.filter_by(user_id=user_id).order_by(Site.created_at.desc()).all()
        else:
            # 未登录用户不显示任何站点
            sites = []
        logging.info(f"从数据库获取了 {len(sites)} 个站点")
    except Exception as e:
        logging.error(f"数据库查询失败: {e}")
        sites = []
    
    return render_template("index.html", sites=sites)


@main_bp.route("/paste_site", methods=["POST"])
@login_required
def paste_site():
    """粘贴HTML代码创建站点"""
    try:
        html_code = request.form.get("html_code", "").strip()
        site_name = request.form.get("site_name", "").strip()
        
        if not html_code:
            return jsonify({"success": False, "msg": "HTML代码不能为空"}), 400
        
        # 验证HTML代码长度
        if len(html_code) > 1024 * 1024:  # 1MB
            return jsonify({"success": False, "msg": "HTML代码太大，最大支持 1MB"}), 400
        
        site_id = str(uuid.uuid4())
        
        # 如果没有提供站点名称，生成默认名称
        if not site_name:
            site_name = f"站点_{site_id[:8]}"
        
        # 检查站点名称是否已存在
        if Site.query.filter_by(name=site_name).first():
            return jsonify({"success": False, "msg": "站点名称已存在"}), 400
        
        # 创建站点记录，状态为 pending
        site_url = f"/site/{site_id}"  # 临时 URL，将在任务完成后更新
        new_site = Site(
            id=site_id, 
            name=site_name, 
            oss_url=site_url, 
            user_id=session.get('user_id'),
            status="pending"
        )
        db.session.add(new_site)
        db.session.commit()
        
        # 启动异步任务处理 HTML 粘贴
        from html_hoster.tasks import process_html_paste
        current_app.executor.submit(process_html_paste, html_code, site_id, site_name, session.get('user_id'))
        
        logging.info(f"已提交 HTML 粘贴任务: {site_name} (ID: {site_id})")
        return redirect(url_for("main.index"))
        
    except Exception as e:
        logging.error(f"粘贴站点失败: {e}")
        return jsonify({"success": False, "msg": "创建站点失败"}), 500


@main_bp.route("/upload", methods=["POST"])
@login_required
def upload_file():
    """上传ZIP文件创建站点"""
    try:
        if "file" not in request.files:
            logging.warning("请求中没有文件")
            return jsonify({"success": False, "msg": "没有选择文件"}), 400
        
        file = request.files["file"]
        if file.filename == "":
            logging.warning("文件名为空")
            return jsonify({"success": False, "msg": "没有选择文件"}), 400
        
        if not file.filename.endswith(".zip"):
            return jsonify({"success": False, "msg": "只支持ZIP格式文件"}), 400
        
        # 生成站点ID和安全的文件名
        site_id = str(uuid.uuid4())
        
        # 获取用户提供的站点名称
        user_site_name = request.form.get("site_name", "").strip()
        
        # 如果用户没有提供站点名称，则从文件名中提取
        if not user_site_name:
            # 直接从原始文件名中提取站点名称，保留中文字符
            original_filename = file.filename
            # 移除.zip扩展名
            if original_filename.lower().endswith('.zip'):
                site_name = original_filename[:-4]
            else:
                site_name = original_filename
        else:
            # 使用用户提供的站点名称
            site_name = user_site_name
            
        # 如果站点名称为空，使用默认名称
        if not site_name:
            site_name = f"站点_{site_id[:8]}"
        
        # 检查站点名称是否已存在
        existing_site = Site.query.filter_by(name=site_name).first()
        if existing_site:
            # 生成唯一名称
            site_name = f"{site_name}_{site_id[:8]}"
        
        # 使用secure_filename仅用于本地存储文件，不影响站点名称
        filename = secure_filename(file.filename)
        if not filename:
            filename = f"{site_id}.zip"
        
        # 临时文件路径
        zip_path = os.path.join(current_app.config["UPLOAD_FOLDER"], f"{site_id}.zip")
        
        try:
            # 保存上传的文件
            logging.info(f"保存上传的ZIP文件到: {zip_path}")
            file.save(zip_path)
            
            # 创建站点记录，状态为 pending
            site_url = f"/site/{site_id}"  # 临时 URL，将在任务完成后更新
            new_site = Site(
                id=site_id, 
                name=site_name, 
                oss_url=site_url, 
                user_id=session.get('user_id'),
                status="pending"
            )
            db.session.add(new_site)
            db.session.commit()
            
            # 启动异步任务处理 ZIP 文件
            from html_hoster.tasks import process_zip_upload
            current_app.executor.submit(process_zip_upload, zip_path, site_id, site_name, session.get('user_id'))
            
            logging.info(f"已提交 ZIP 上传任务: {site_name} (ID: {site_id})")
            return redirect(url_for("main.index"))
            
        except Exception as e:
            logging.error(f"保存上传文件失败: {e}")
            # 清理临时文件
            if os.path.exists(zip_path):
                os.remove(zip_path)
            return jsonify({"success": False, "msg": "保存上传文件失败"}), 500
            
    except Exception as e:
        logging.error(f"上传文件失败: {e}")
        return jsonify({"success": False, "msg": "上传文件失败"}), 500


@site_bp.route("/<site_id>/<path:filename>")
def serve_site_file(site_id, filename):
    """提供站点文件访问"""
    try:
        # 检查站点是否存在及其发布状态
        site = Site.query.get(site_id)
        if not site:
            return render_template("error.html", 
                                error_code=404,
                                error_message="站点未找到",
                                error_detail="请求的站点不存在或已被删除"), 404
        
        # 检查站点发布状态 - 如果是未发布状态，只有站点所有者可以访问
        if not site.is_published and session.get('user_id') != site.user_id:
            return render_template("error.html", 
                                error_code=403,
                                error_message="访问被拒绝",
                                error_detail="此站点尚未发布，您没有权限访问"), 403
        
        # 检查使用的存储类型
        storage_type = current_app.config.get("STORAGE_TYPE", "").lower()
        
        if storage_type == "local":
            # 对于本地存储，直接从sites目录提供文件
            site_path = os.path.join(current_app.config["SITES_FOLDER"], site_id)
            return send_from_directory(site_path, filename)
        else:
            # 其他存储类型，从存储服务获取文件
            content, content_type = get_storage().download_file(f"{site_id}/{filename}")
            
            if content is None:
                return render_template("error.html", 
                                    error_code=404,
                                    error_message="文件未找到",
                                    error_detail=f"请求的文件 {filename} 不存在"), 404
            
            # 设置响应
            from flask import Response
            response = Response(content)
            
            # 设置Content-Type
            if content_type:
                response.headers["Content-Type"] = content_type
            else:
                # 根据文件扩展名猜测Content-Type
                guessed_type, _ = mimetypes.guess_type(filename)
                if guessed_type:
                    response.headers["Content-Type"] = guessed_type
            
            return response
        
    except Exception as e:
        logging.error(f"提供站点文件失败 {site_id}/{filename}: {e}")
        return render_template("error.html", 
                             error_code=500,
                             error_message="服务器错误",
                             error_detail="获取文件时发生错误"), 500


@main_bp.route("/delete_site/<site_id>", methods=["POST"])
@login_required
def delete_site(site_id):
    """删除站点"""
    try:
        # 查询站点
        site = Site.query.get(site_id)
        if not site:
            return jsonify({"success": False, "msg": "站点不存在"}), 404
        
        # 删除存储服务中的文件
        try:
            storage = get_storage()
            # 使用批量删除功能
            if hasattr(storage, 'delete_prefix'):
                storage.delete_prefix(site_id)
                logging.info(f"已批量删除站点 {site_id} 的所有文件")
            else:
                # 回退到逐个文件删除
                files = storage.list_files(site_id)
                for file_path in files:
                    storage.delete_file(file_path)
                logging.info(f"已删除存储服务中的文件: {len(files)} 个")
        except Exception as e:
            logging.error(f"删除存储服务文件失败: {e}")
            # 继续删除数据库记录
        
        # 删除数据库记录
        db.session.delete(site)
        db.session.commit()
        
        logging.info(f"成功删除站点: {site.name} (ID: {site_id})")
        return jsonify({"success": True, "msg": "站点已删除"})
        
    except Exception as e:
        logging.error(f"删除站点失败: {e}")
        return jsonify({"success": False, "msg": "删除站点失败"}), 500


@main_bp.route("/rename_site/<site_id>", methods=["POST"])
@login_required
def rename_site(site_id):
    """重命名站点"""
    try:
        # 获取新名称
        new_name = request.form.get("new_name", "").strip()
        if not new_name:
            return jsonify({"success": False, "msg": "新名称不能为空"}), 400
        
        # 查询站点
        site = Site.query.get(site_id)
        if not site:
            return jsonify({"success": False, "msg": "站点不存在"}), 404
        
        # 检查名称是否已存在
        existing = Site.query.filter_by(name=new_name).first()
        if existing and existing.id != site_id:
            return jsonify({"success": False, "msg": "站点名称已存在"}), 400
        
        # 更新名称
        old_name = site.name
        site.name = new_name
        db.session.commit()
        
        logging.info(f"成功重命名站点: {old_name} -> {new_name} (ID: {site_id})")
        return jsonify({
            "success": True, 
            "msg": "站点已重命名",
            "new_name": new_name
        })
        
    except Exception as e:
        logging.error(f"重命名站点失败: {e}")
        return jsonify({"success": False, "msg": "重命名站点失败"}), 500


@main_bp.route("/api/sites", methods=["GET"])
def api_list_sites():
    """API: 获取站点列表"""
    try:
        sites = Site.query.order_by(Site.created_at.desc()).all()
        sites_data = [site.to_dict() for site in sites]
        
        return jsonify({
            "success": True,
            "data": sites_data,
            "count": len(sites_data)
        })
        
    except Exception as e:
        logging.error(f"API获取站点列表失败: {e}")
        return jsonify({"success": False, "msg": "获取站点列表失败"}), 500


@main_bp.route("/health", methods=["GET"])
def health_check():
    """健康检查"""
    try:
        # 检查数据库连接
        db.session.execute("SELECT 1")
        
        return jsonify({
            "status": "ok",
            "message": "服务正常"
        })
        
    except Exception as e:
        logging.error(f"健康检查失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@main_bp.route("/toggle_site_visibility/<site_id>", methods=["POST"])
@login_required
def toggle_site_publish_status(site_id):
    """切换站点发布状态（已发布/未发布）"""
    try:
        # 查询站点
        site = Site.query.get(site_id)
        if not site:
            return jsonify({"success": False, "msg": "站点不存在"}), 404
        
        # 检查权限（只有站点所有者可以切换发布状态）
        if site.user_id != session.get('user_id'):
            return jsonify({"success": False, "msg": "没有权限修改此站点"}), 403
        
        # 切换发布状态
        site.is_published = not site.is_published
        db.session.commit()
        
        status = "已发布" if site.is_published else "未发布"
        logging.info(f"站点 {site.name} (ID: {site_id}) 的发布状态已切换为 {status}")
        
        return jsonify({
            "success": True, 
            "msg": f"站点已{status}",
            "is_published": site.is_published
        })
        
    except Exception as e:
        logging.error(f"切换站点发布状态失败: {e}")
        return jsonify({"success": False, "msg": "切换站点发布状态失败"}), 500


@main_bp.route("/api/site/<site_id>/status", methods=["GET"])
def api_site_status(site_id):
    """API: 获取站点状态"""
    try:
        site = Site.query.get(site_id)
        if not site:
            return jsonify({"success": False, "msg": "站点不存在"}), 404
        
        return jsonify({
            "success": True,
            "data": {
                "id": site.id,
                "name": site.name,
                "status": site.status,
                "error_message": site.error_message,
                "oss_url": site.oss_url,
                "is_published": site.is_published
            }
        })
        
    except Exception as e:
        logging.error(f"API获取站点状态失败: {e}")
        return jsonify({"success": False, "msg": "获取站点状态失败"}), 500 
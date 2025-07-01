import os
import uuid
import zipfile
import logging
from flask import Flask, render_template, request, redirect, url_for, jsonify
import oss2
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import mimetypes
import pymysql

# 设置 PyMySQL 作为 mysqlclient 的替代
pymysql.install_as_MySQLdb()

# 设置日志
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.abspath(os.path.join(BASE_DIR, "./templates"))
UPLOAD_DIR = os.path.abspath(os.path.join(BASE_DIR, "../uploads"))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "./instance/sites.db"))
SERVER_WORKERS = int(os.getenv("SERVER_WORKERS", 4))

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR

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
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB 最大上传大小

db = SQLAlchemy(app)

# OSS Configuration
OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID")
OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET")
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT")
OSS_BUCKET_NAME = os.getenv("OSS_BUCKET_NAME")
OSS_PREFIX = "html_hoster/sites"

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)


class Site(db.Model):
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


@app.route("/")
def index():
    logging.info("访问首页")
    try:
        sites = Site.query.order_by(Site.created_at.desc()).all()
        logging.info(f"从数据库获取了 {len(sites)} 个站点")
    except Exception as e:
        logging.error(f"数据库查询失败: {e}")
        sites = []
    
    return render_template("index.html", sites=sites)


@app.route("/paste_site", methods=["POST"])
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
        
        # 创建临时目录
        extract_path = os.path.join(app.config["UPLOAD_FOLDER"], site_id)
        os.makedirs(extract_path, exist_ok=True)
        
        # 保存HTML文件
        index_html_path = os.path.join(extract_path, "index.html")
        with open(index_html_path, "w", encoding="utf-8") as f:
            f.write(html_code)
        
        # 上传到OSS
        oss_path = os.path.join(OSS_PREFIX, site_id, "index.html").replace("\\", "/")
        try:
            bucket.put_object_from_file(oss_path, index_html_path)
            logging.info(f"成功上传粘贴的HTML到OSS: {oss_path}")
        except Exception as e:
            logging.error(f"OSS上传失败: {e}")
            # 清理临时文件
            os.remove(index_html_path)
            os.rmdir(extract_path)
            return jsonify({"success": False, "msg": "上传到云存储失败"}), 500
        
        # 保存到数据库
        oss_url = f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{OSS_PREFIX}/{site_id}/index.html"
        new_site = Site(name=site_name, oss_url=oss_url, id=site_id)
        db.session.add(new_site)
        db.session.commit()
        
        # 清理临时文件
        os.remove(index_html_path)
        os.rmdir(extract_path)
        
        logging.info(f"成功创建粘贴站点: {site_name}")
        return redirect(url_for("index"))
        
    except Exception as e:
        logging.error(f"粘贴站点失败: {e}")
        return jsonify({"success": False, "msg": "创建站点失败"}), 500


@app.route("/upload", methods=["POST"])
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
        
        # 直接从原始文件名中提取站点名称，保留中文字符
        original_filename = file.filename
        # 移除.zip扩展名
        if original_filename.lower().endswith('.zip'):
            site_name = original_filename[:-4]
        else:
            site_name = original_filename
            
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
        
        zip_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{site_id}.zip")
        extract_path = os.path.join(app.config["UPLOAD_FOLDER"], site_id)
        
        try:
            # 保存上传的文件
            logging.info(f"保存上传的ZIP文件到: {zip_path}")
            file.save(zip_path)
            
            # 验证ZIP文件
            if not zipfile.is_zipfile(zip_path):
                raise ValueError("无效的ZIP文件")
            
            # 解压文件
            logging.info(f"解压ZIP文件到: {extract_path}")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # 检查解压后的大小
                total_size = sum(zinfo.file_size for zinfo in zip_ref.filelist)
                if total_size > 100 * 1024 * 1024:  # 100MB
                    raise ValueError("解压后文件总大小超过100MB限制")
                
                zip_ref.extractall(extract_path)
            
            # 查找index.html
            index_html_path = None
            for root, dirs, files in os.walk(extract_path):
                if "index.html" in files:
                    index_html_path = os.path.join(root, "index.html")
                    break
            
            if not index_html_path:
                raise ValueError("ZIP包中没有找到index.html文件")
            
            # 上传到OSS
            uploaded_files = 0
            for root, dirs, files in os.walk(extract_path):
                for filename in files:
                    local_path = os.path.join(root, filename)
                    # 计算相对路径
                    relative_path = os.path.relpath(local_path, extract_path)
                    oss_path = os.path.join(OSS_PREFIX, site_id, relative_path).replace("\\", "/")
                    
                    try:
                        # 设置Content-Type
                        content_type, _ = mimetypes.guess_type(filename)
                        headers = {'Content-Type': content_type} if content_type else {}
                        
                        bucket.put_object_from_file(oss_path, local_path, headers=headers)
                        uploaded_files += 1
                        logging.info(f"上传文件到OSS: {oss_path}")
                    except Exception as e:
                        logging.error(f"上传文件失败 {local_path}: {e}")
            
            logging.info(f"成功上传 {uploaded_files} 个文件到OSS")
            
            # 保存到数据库
            oss_url = f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{OSS_PREFIX}/{site_id}/index.html"
            new_site = Site(name=site_name, oss_url=oss_url, id=site_id)
            db.session.add(new_site)
            db.session.commit()
            
            logging.info(f"成功创建站点: {site_name} (ID: {site_id})")
            
        except Exception as e:
            logging.error(f"处理上传文件失败: {e}")
            # 清理OSS上已上传的文件
            try:
                prefix = os.path.join(OSS_PREFIX, site_id).replace("\\", "/")
                for obj in oss2.ObjectIterator(bucket, prefix=prefix):
                    bucket.delete_object(obj.key)
            except:
                pass
            
            return jsonify({"success": False, "msg": str(e)}), 500
        
        finally:
            # 清理本地临时文件
            if os.path.exists(zip_path):
                os.remove(zip_path)
                logging.info(f"删除临时ZIP文件: {zip_path}")
            
            if os.path.exists(extract_path):
                for root, dirs, files in os.walk(extract_path, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(extract_path)
                logging.info(f"清理解压目录: {extract_path}")
        
        return redirect(url_for("index"))
        
    except Exception as e:
        logging.error(f"上传处理失败: {e}")
        return jsonify({"success": False, "msg": "上传处理失败"}), 500


@app.route("/site/<site_id>/<path:filename>")
def serve_site_file(site_id, filename):
    """提供站点静态文件访问"""
    import mimetypes
    
    # 安全检查：防止路径遍历
    if ".." in filename or filename.startswith("/"):
        return "Forbidden", 403
    
    oss_file_path = f"{OSS_PREFIX}/{site_id}/{filename}"
    try:
        # 从OSS获取文件
        result = bucket.get_object(oss_file_path)
        content = result.read()
        
        # 设置正确的Content-Type
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            if filename.endswith('.js'):
                mime_type = 'application/javascript'
            elif filename.endswith('.css'):
                mime_type = 'text/css'
            else:
                mime_type = "application/octet-stream"
        
        return content, 200, {"Content-Type": mime_type}
    except oss2.exceptions.NoSuchKey:
        logging.warning(f"文件不存在: {oss_file_path}")
        return "文件不存在", 404
    except Exception as e:
        logging.error(f"获取OSS文件失败 {oss_file_path}: {e}")
        return "服务器错误", 500


@app.route("/delete_site/<site_id>", methods=["POST"])
def delete_site(site_id):
    """删除站点"""
    try:
        site = Site.query.filter_by(name=site_id).first()
        if not site:
            return jsonify({"success": False, "msg": "站点不存在"}), 404
        
        # 删除OSS上的所有文件
        prefix = os.path.join(OSS_PREFIX, site.id).replace("\\", "/")
        deleted_count = 0
        
        try:
            for obj in oss2.ObjectIterator(bucket, prefix=prefix):
                bucket.delete_object(obj.key)
                deleted_count += 1
            logging.info(f"从OSS删除了 {deleted_count} 个文件")
        except Exception as e:
            logging.error(f"删除OSS文件失败: {e}")
            return jsonify({"success": False, "msg": "删除云存储文件失败"}), 500
        
        # 从数据库删除记录
        db.session.delete(site)
        db.session.commit()
        
        logging.info(f"成功删除站点: {site_id}")
        return jsonify({"success": True, "msg": "删除成功"})
        
    except Exception as e:
        logging.error(f"删除站点失败: {e}")
        db.session.rollback()
        return jsonify({"success": False, "msg": "删除失败"}), 500


@app.route("/rename_site/<site_id>", methods=["POST"])
def rename_site(site_id):
    """重命名站点"""
    try:
        new_name = request.form.get("new_name", "").strip()
        if not new_name:
            return jsonify({"success": False, "msg": "新名称不能为空"}), 400
        
        # 检查名称长度
        if len(new_name) > 80:
            return jsonify({"success": False, "msg": "名称太长，最多80个字符"}), 400
        
        site = Site.query.filter_by(name=site_id).first()
        if not site:
            return jsonify({"success": False, "msg": "站点不存在"}), 404
        
        # 检查新名称是否已存在
        if Site.query.filter_by(name=new_name).first():
            return jsonify({"success": False, "msg": "该名称已被使用"}), 400
        
        old_name = site.name
        site.name = new_name
        db.session.commit()
        
        logging.info(f"成功重命名站点: {old_name} -> {new_name}")
        return jsonify({
            "success": True, 
            "new_name": new_name,
            "msg": "重命名成功"
        })
        
    except Exception as e:
        logging.error(f"重命名站点失败: {e}")
        db.session.rollback()
        return jsonify({"success": False, "msg": "重命名失败"}), 500


@app.route("/api/sites", methods=["GET"])
def api_list_sites():
    """API: 获取所有站点列表"""
    try:
        sites = Site.query.order_by(Site.created_at.desc()).all()
        return jsonify({
            "success": True,
            "data": [site.to_dict() for site in sites],
            "count": len(sites)
        })
    except Exception as e:
        logging.error(f"获取站点列表失败: {e}")
        return jsonify({"success": False, "msg": "获取站点列表失败"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "sites_count": Site.query.count()
    })


def main():
    """主函数入口"""
    from waitress import serve

    with app.app_context():
        db.create_all()
        if DB_TYPE == "mysql":
            logging.info(f"MySQL 数据库初始化完成: {os.getenv('MYSQL_HOST', 'localhost')}:{os.getenv('MYSQL_PORT', '3306')}/{os.getenv('MYSQL_DB', 'html_hoster')}")
        else:
            logging.info(f"SQLite 数据库初始化完成: {DB_PATH}")
    
    logging.info(f"启动服务器 - 端口: 5000, 工作线程: {SERVER_WORKERS}")
    serve(app, host="0.0.0.0", port=5000, threads=SERVER_WORKERS)


if __name__ == "__main__":
    main()

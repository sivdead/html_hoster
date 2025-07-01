import os
import uuid
import zipfile
import logging
from flask import Flask, render_template, request, redirect, url_for, jsonify
import oss2
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.abspath(os.path.join(BASE_DIR, "./templates"))
UPLOAD_DIR = os.path.abspath(os.path.join(BASE_DIR, "../uploads"))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "./instance/sites.db"))

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# OSS Configuration
OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID")
OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET")
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT")
OSS_BUCKET_NAME = os.getenv("OSS_BUCKET_NAME")
OSS_PREFIX = "html_hoster/sites"

auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)


class Site(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    oss_url = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"<Site {self.name}>"


@app.route("/")
def index():
    logging.info("Received request for index page")
    try:
        sites = Site.query.all()
        logging.info(f"Fetched {len(sites)} sites from DB")
    except Exception as e:
        logging.error(f"DB query failed: {e}")
        raise
    try:
        resp = render_template("index.html", sites=sites)
        logging.info("Rendered index.html successfully")
        return resp
    except Exception as e:
        logging.error(f"Template rendering failed: {e}")
        raise


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        logging.warning("No file part in request.")
        return redirect(request.url)
    file = request.files["file"]
    if file.filename == "":
        logging.warning("No selected file.")
        return redirect(request.url)
    # 上传时用文件名作为默认网站名
    if file and file.filename.endswith(".zip"):
        site_id = str(uuid.uuid4())
        zip_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{site_id}.zip")
        logging.info(f"Saving uploaded zip to {zip_path}")
        file.save(zip_path)

        extract_path = os.path.join(app.config["UPLOAD_FOLDER"], site_id)
        logging.info(f"Extracting zip to {extract_path}")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        for root, dirs, files in os.walk(extract_path):
            for filename in files:
                local_path = os.path.join(root, filename)
                oss_path = os.path.join(
                    OSS_PREFIX, site_id, os.path.relpath(local_path, extract_path)
                ).replace("\\", "/")
                logging.info(f"Uploading {local_path} to OSS as {oss_path}")
                try:
                    bucket.put_object_from_file(oss_path, local_path)
                except Exception as e:
                    logging.error(f"OSS upload failed: {e}")

        # 用上传文件名（去掉.zip）作为默认网站名
        site_name = os.path.splitext(file.filename)[0]
        oss_url = f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{OSS_PREFIX}/{site_id}/index.html"
        new_site = Site(name=site_name, oss_url=oss_url, id=site_id)
        db.session.add(new_site)
        db.session.commit()
        logging.info(f"Site {site_name} saved to DB with URL {oss_url}")

        os.remove(zip_path)
        logging.info(f"Removed zip file {zip_path}")
        for root, dirs, files in os.walk(extract_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(extract_path)
        logging.info(f"Cleaned up extracted files at {extract_path}")

        return redirect(url_for("index"))


@app.route("/site/<site_id>/<path:filename>")
def serve_site_file(site_id, filename):
    """
    独立站点静态文件访问，防止主应用css污染。
    直接从OSS读取文件并返回。
    """
    import mimetypes

    oss_file_path = f"{OSS_PREFIX}/{site_id}/{filename}"
    try:
        result = bucket.get_object(oss_file_path)
        content = result.read()
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "application/octet-stream"
        return content, 200, {"Content-Type": mime_type}
    except Exception as e:
        logging.error(f"Failed to fetch {oss_file_path} from OSS: {e}")
        return "File not found", 404


@app.route("/delete_site/<site_id>", methods=["POST"])
def delete_site(site_id):
    """
    删除站点：删除OSS文件夹和数据库记录
    """
    site = Site.query.filter_by(name=site_id).first()
    if not site:
        return jsonify({"success": False, "msg": "站点不存在"}), 404
    # 删除OSS文件夹下所有文件
    prefix = os.path.join(OSS_PREFIX, site_id).replace("\\", "/")
    try:
        for obj in oss2.ObjectIterator(bucket, prefix=prefix):
            bucket.delete_object(obj.key)
        db.session.delete(site)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        logging.error(f"删除站点失败: {e}")
        return jsonify({"success": False, "msg": str(e)}), 500


@app.route("/rename_site/<site_id>", methods=["POST"])
def rename_site(site_id):
    """
    修改站点名称
    """
    new_name = request.form.get("new_name", "").strip()
    if not new_name:
        return jsonify({"success": False, "msg": "新名称不能为空"}), 400
    site = Site.query.filter_by(name=site_id).first()
    if not site:
        return jsonify({"success": False, "msg": "站点不存在"}), 404
    if Site.query.filter_by(name=new_name).first():
        return jsonify({"success": False, "msg": "名称已存在"}), 400
    site.name = new_name
    db.session.commit()
    return jsonify({"success": True, "new_name": new_name})


if __name__ == "__main__":
    from waitress import serve

    with app.app_context():
        db.create_all()
        logging.info(f"Database created at {DB_PATH}")
    serve(app, host="0.0.0.0", port=5000)

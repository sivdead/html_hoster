"""
身份验证模块 - 支持Supabase身份验证和本地认证
"""
import os
import logging
from functools import wraps
from flask import redirect, url_for, jsonify, session, current_app

# 初始化Supabase客户端
def get_supabase_client():
    """获取Supabase客户端实例"""
    try:
        from supabase import create_client, Client
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logging.warning("Supabase配置缺失，将使用本地身份验证")
            return None
        
        supabase: Client = create_client(supabase_url, supabase_key)
        return supabase
    except ImportError:
        logging.warning("未安装supabase-py库，将使用本地身份验证")
        return None
    except Exception as e:
        logging.error(f"初始化Supabase客户端失败: {e}")
        return None


# 登录验证装饰器
def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            if current_app.config.get('API_ONLY', False):
                return jsonify({"success": False, "msg": "请先登录"}), 401
            else:
                return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# 管理员验证装饰器
def admin_required(f):
    """管理员验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            if current_app.config.get('API_ONLY', False):
                return jsonify({"success": False, "msg": "请先登录"}), 401
            else:
                return redirect(url_for('auth.login'))
        
        # 检查用户是否是管理员
        from html_hoster.database import User
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({"success": False, "msg": "需要管理员权限"}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def init_auth(app):
    """初始化身份验证模块"""
    # 配置会话
    if not app.secret_key:
        app.secret_key = os.getenv("SECRET_KEY", os.urandom(24).hex())
    
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 1天
    
    # 尝试初始化Supabase
    supabase = get_supabase_client()
    if supabase:
        app.config['USE_SUPABASE'] = True
        app.config['SUPABASE_CLIENT'] = supabase
        logging.info("Supabase身份验证已启用")
    else:
        app.config['USE_SUPABASE'] = False
        logging.info("使用本地身份验证")
    
    logging.info("身份验证模块初始化完成") 
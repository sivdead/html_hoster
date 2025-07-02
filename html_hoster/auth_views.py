"""
认证视图模块 - 处理用户登录和注册
"""
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from html_hoster.database import db, User, Site
from html_hoster.auth import login_required

# 创建Blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'GET':
        return render_template('login.html')
    
    # 处理POST请求
    try:
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('用户名和密码不能为空', 'error')
            return render_template('login.html'), 400
        
        # 查询用户
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('用户名或密码错误', 'error')
            return render_template('login.html'), 401
        
        # 登录成功，保存session
        session['user_id'] = user.id
        session['username'] = user.username
        
        # 记录登录日志
        logging.info(f"用户登录成功: {username}")
        
        # 重定向到首页
        return redirect(url_for('main.index'))
        
    except Exception as e:
        logging.error(f"登录失败: {e}")
        flash('登录失败，请稍后再试', 'error')
        return render_template('login.html'), 500


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'GET':
        return render_template('register.html')
    
    # 处理POST请求
    try:
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # 验证输入
        if not username or not password:
            flash('用户名和密码不能为空', 'error')
            return render_template('register.html'), 400
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('register.html'), 400
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用户名已存在', 'error')
            return render_template('register.html'), 400
        
        # 创建新用户
        password_hash = generate_password_hash(password)
        new_user = User(username=username, password_hash=password_hash)
        
        db.session.add(new_user)
        db.session.commit()
        
        # 记录注册日志
        logging.info(f"新用户注册成功: {username}")
        
        # 自动登录
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        
        # 重定向到首页
        flash('注册成功！', 'success')
        return redirect(url_for('main.index'))
        
    except Exception as e:
        logging.error(f"注册失败: {e}")
        flash('注册失败，请稍后再试', 'error')
        return render_template('register.html'), 500


@auth_bp.route('/logout')
def logout():
    """用户登出"""
    # 清除session
    session.pop('user_id', None)
    session.pop('username', None)
    
    # 重定向到登录页
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    """用户个人资料"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if not user:
            return redirect(url_for('auth.logout'))
        
        # 确保获取用户的站点
        user.sites = Site.query.filter_by(user_id=user.id).order_by(Site.created_at.desc()).all()
        
        return render_template('profile.html', user=user)
        
    except Exception as e:
        logging.error(f"获取用户资料失败: {e}")
        flash('获取用户资料失败', 'error')
        return redirect(url_for('main.index'))


@auth_bp.route('/api/user/current', methods=['GET'])
def api_current_user():
    """API: 获取当前登录用户信息"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': '未登录',
                'logged_in': False
            })
        
        user = User.query.get(user_id)
        
        if not user:
            # 用户ID存在但用户不存在，清除session
            session.pop('user_id', None)
            session.pop('username', None)
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'logged_in': False
            })
        
        return jsonify({
            'success': True,
            'logged_in': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
        })
        
    except Exception as e:
        logging.error(f"API获取当前用户失败: {e}")
        return jsonify({
            'success': False,
            'message': '获取用户信息失败',
            'logged_in': False
        }), 500 
/**
 * 认证模块 - 处理用户登录、注册和会话管理
 */

/**
 * 检查用户登录状态
 * @returns {Promise<Object>} 用户信息
 */
async function checkLoginStatus() {
    try {
        const response = await fetch('/auth/api/user/current');
        const data = await response.json();
        
        return {
            loggedIn: data.logged_in || false,
            user: data.user || null
        };
    } catch (error) {
        console.error('检查登录状态失败:', error);
        return {
            loggedIn: false,
            user: null
        };
    }
}

/**
 * 用户登录
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @returns {Promise<Object>} 登录结果
 */
async function login(username, password) {
    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch('/auth/login', {
            method: 'POST',
            body: formData
        });
        
        if (response.redirected) {
            // 登录成功，重定向
            window.location.href = response.url;
            return { success: true };
        }
        
        // 处理错误
        const text = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, 'text/html');
        const errorMsg = doc.querySelector('.alert-danger')?.textContent || '登录失败';
        
        return {
            success: false,
            message: errorMsg
        };
    } catch (error) {
        console.error('登录请求失败:', error);
        return {
            success: false,
            message: '登录请求失败，请稍后再试'
        };
    }
}

/**
 * 用户注册
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @param {string} confirmPassword - 确认密码
 * @returns {Promise<Object>} 注册结果
 */
async function register(username, password, confirmPassword) {
    try {
        if (password !== confirmPassword) {
            return {
                success: false,
                message: '两次输入的密码不一致'
            };
        }
        
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        formData.append('confirm_password', confirmPassword);
        
        const response = await fetch('/auth/register', {
            method: 'POST',
            body: formData
        });
        
        if (response.redirected) {
            // 注册成功，重定向
            window.location.href = response.url;
            return { success: true };
        }
        
        // 处理错误
        const text = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, 'text/html');
        const errorMsg = doc.querySelector('.alert-danger')?.textContent || '注册失败';
        
        return {
            success: false,
            message: errorMsg
        };
    } catch (error) {
        console.error('注册请求失败:', error);
        return {
            success: false,
            message: '注册请求失败，请稍后再试'
        };
    }
}

/**
 * 修改密码
 * @param {string} currentPassword - 当前密码
 * @param {string} newPassword - 新密码
 * @returns {Promise<Object>} 修改结果
 */
async function changePassword(currentPassword, newPassword) {
    try {
        const response = await fetch('/auth/change_password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });
        
        const data = await response.json();
        return {
            success: data.success,
            message: data.msg || (data.success ? '密码修改成功' : '密码修改失败')
        };
    } catch (error) {
        console.error('修改密码请求失败:', error);
        return {
            success: false,
            message: '修改密码请求失败，请稍后再试'
        };
    }
}

/**
 * 用户登出
 */
function logout() {
    window.location.href = '/auth/logout';
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化登录表单
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            const result = await login(username, password);
            if (!result.success) {
                showToast('登录失败', result.message, 'danger');
            }
        });
    }
    
    // 初始化注册表单
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            
            const result = await register(username, password, confirmPassword);
            if (!result.success) {
                showToast('注册失败', result.message, 'danger');
            }
        });
    }
    
    // 初始化登出按钮
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            logout();
        });
    }
}); 
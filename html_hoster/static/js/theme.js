/**
 * 主题模块 - 处理暗黑模式切换
 */

// 主题类型
const THEMES = {
    LIGHT: 'light',
    DARK: 'dark'
};

/**
 * 设置主题
 * @param {string} theme - 主题类型 ('light' 或 'dark')
 */
function setTheme(theme) {
    // 验证主题类型
    if (theme !== THEMES.LIGHT && theme !== THEMES.DARK) {
        console.error(`无效的主题类型: ${theme}`);
        theme = THEMES.LIGHT; // 默认使用亮色主题
    }
    
    // 设置HTML属性
    document.documentElement.setAttribute('data-bs-theme', theme);
    
    // 保存到本地存储
    localStorage.setItem('theme', theme);
    
    // 更新主题切换按钮图标
    updateThemeIcon(theme);
}

/**
 * 更新主题图标
 * @param {string} theme - 当前主题类型
 */
function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('theme-icon');
    if (!themeIcon) return;
    
    // 清除旧的图标类
    themeIcon.className = '';
    
    // 添加新的图标类
    if (theme === THEMES.DARK) {
        themeIcon.classList.add('bi', 'bi-moon-fill');
    } else {
        themeIcon.classList.add('bi', 'bi-sun-fill');
    }
}

/**
 * 切换主题
 */
function toggleTheme() {
    const currentTheme = getCurrentTheme();
    const newTheme = currentTheme === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK;
    setTheme(newTheme);
}

/**
 * 获取当前主题
 * @returns {string} 当前主题类型
 */
function getCurrentTheme() {
    // 优先从HTML属性获取
    const htmlTheme = document.documentElement.getAttribute('data-bs-theme');
    if (htmlTheme) {
        return htmlTheme;
    }
    
    // 从本地存储获取
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        return savedTheme;
    }
    
    // 检查系统偏好
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return THEMES.DARK;
    }
    
    // 默认使用亮色主题
    return THEMES.LIGHT;
}

/**
 * 初始化主题
 */
function initTheme() {
    const theme = getCurrentTheme();
    setTheme(theme);
    
    // 监听系统主题变化
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            // 只有在用户没有手动设置主题时才跟随系统
            if (!localStorage.getItem('theme')) {
                setTheme(e.matches ? THEMES.DARK : THEMES.LIGHT);
            }
        });
    }
}

// 页面加载时初始化主题
document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    
    // 绑定主题切换按钮事件
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', toggleTheme);
    }
}); 
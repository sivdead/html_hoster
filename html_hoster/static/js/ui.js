/**
 * UI工具模块 - 提供通用UI功能
 */

/**
 * 显示提示消息
 * @param {string} title - 提示标题
 * @param {string} message - 提示内容
 * @param {string} type - 提示类型 (success, info, warning, danger)
 */
function showToast(title, message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastTitle = document.getElementById('toast-title');
    const toastMessage = document.getElementById('toast-message');
    
    if (!toast || !toastTitle || !toastMessage) {
        console.error('找不到Toast元素');
        return;
    }
    
    // 设置标题和内容
    toastTitle.textContent = title;
    toastMessage.textContent = message;
    
    // 设置类型样式
    toast.classList.remove('bg-success', 'bg-info', 'bg-warning', 'bg-danger', 'text-white');
    if (type === 'success') {
        toast.classList.add('bg-success', 'text-white');
    } else if (type === 'warning') {
        toast.classList.add('bg-warning');
    } else if (type === 'danger') {
        toast.classList.add('bg-danger', 'text-white');
    } else {
        toast.classList.add('bg-info', 'text-white');
    }
    
    // 显示Toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

/**
 * 显示确认对话框
 * @param {string} title - 对话框标题
 * @param {string} message - 对话框内容
 * @param {Function} onConfirm - 确认回调函数
 * @param {Function} onCancel - 取消回调函数
 */
function showConfirm(title, message, onConfirm, onCancel = null) {
    // 检查是否已存在确认对话框元素
    let confirmModal = document.getElementById('confirm-modal');
    
    // 如果不存在，创建一个
    if (!confirmModal) {
        const modalHtml = `
            <div class="modal fade" id="confirm-modal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="confirm-title"></h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p id="confirm-message"></p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" id="confirm-cancel-btn">取消</button>
                            <button type="button" class="btn btn-primary" id="confirm-ok-btn">确认</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 添加到文档中
        const div = document.createElement('div');
        div.innerHTML = modalHtml;
        document.body.appendChild(div.firstChild);
        
        confirmModal = document.getElementById('confirm-modal');
    }
    
    // 设置标题和内容
    document.getElementById('confirm-title').textContent = title;
    document.getElementById('confirm-message').textContent = message;
    
    // 创建Bootstrap模态框对象
    const modal = new bootstrap.Modal(confirmModal);
    
    // 绑定事件
    const okBtn = document.getElementById('confirm-ok-btn');
    const cancelBtn = document.getElementById('confirm-cancel-btn');
    
    // 移除旧的事件监听器
    const newOkBtn = okBtn.cloneNode(true);
    okBtn.parentNode.replaceChild(newOkBtn, okBtn);
    
    const newCancelBtn = cancelBtn.cloneNode(true);
    cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
    
    // 添加新的事件监听器
    newOkBtn.addEventListener('click', function() {
        modal.hide();
        if (typeof onConfirm === 'function') {
            onConfirm();
        }
    });
    
    newCancelBtn.addEventListener('click', function() {
        if (typeof onCancel === 'function') {
            onCancel();
        }
    });
    
    // 显示对话框
    modal.show();
}

/**
 * 切换暗黑模式
 */
function toggleDarkMode() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-bs-theme') === 'dark';
    
    // 切换主题
    html.setAttribute('data-bs-theme', isDark ? 'light' : 'dark');
    
    // 保存到本地存储
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
    
    // 更新图标
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        themeIcon.className = isDark ? 'bi bi-sun' : 'bi bi-moon';
    }
}

/**
 * 初始化主题
 */
function initTheme() {
    // 从本地存储获取主题
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = savedTheme || (prefersDark ? 'dark' : 'light');
    
    // 设置主题
    document.documentElement.setAttribute('data-bs-theme', theme);
    
    // 更新图标
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        themeIcon.className = theme === 'dark' ? 'bi bi-moon' : 'bi bi-sun';
    }
}

// 页面加载时初始化主题
document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    
    // 绑定主题切换按钮事件
    const themeBtn = document.getElementById('theme-btn');
    if (themeBtn) {
        themeBtn.addEventListener('click', toggleDarkMode);
    }
});

// 显示加载状态
function showLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'flex';
    }
}

// 隐藏加载状态
function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'none';
    }
}

/**
 * 从文件名提取网站名称
 * @param {string} filename - 文件名
 * @return {string} 提取后的网站名称
 */
function extractSiteNameFromFilename(filename) {
    if (!filename) return '';
    
    // 移除.zip后缀
    if (filename.toLowerCase().endsWith('.zip')) {
        return filename.slice(0, -4);
    }
    
    return filename;
}

// 初始化文件上传区域拖放功能
function initDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');
    if (!uploadArea) return;
    
    const fileInput = document.getElementById('fileInput');
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            const fileName = fileInput.files[0].name;
            showToast(`已选择文件: ${fileName}`);
            
            // 自动填充网站名称
            const siteNameInput = document.getElementById('site_name');
            if (siteNameInput) {
                siteNameInput.value = extractSiteNameFromFilename(fileName);
            }
        }
    });
    
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            const fileName = fileInput.files[0].name;
            showToast(`已选择文件: ${fileName}`);
            
            // 自动填充网站名称
            const siteNameInput = document.getElementById('site_name');
            if (siteNameInput) {
                siteNameInput.value = extractSiteNameFromFilename(fileName);
            }
        }
    });
}

// 初始化文件上传表单
function initFileUploadForm() {
    const fileInput = document.getElementById('file');
    if (!fileInput) return;
    
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            const fileName = fileInput.files[0].name;
            
            // 自动填充网站名称
            const siteNameInput = document.getElementById('site_name');
            if (siteNameInput) {
                siteNameInput.value = extractSiteNameFromFilename(fileName);
            }
        }
    });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    initDragAndDrop();
    initFileUploadForm();
    
    // 为表单添加加载状态
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', () => {
            // 检查是否有data-no-loading属性
            if (!form.hasAttribute('data-no-loading')) {
                showLoading();
            }
        });
    });
}); 
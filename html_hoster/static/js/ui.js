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

/**
 * 清理模态框遮罩和相关样式
 * 用于解决模态框关闭后遮罩没有正确移除的问题
 */
function cleanupModalBackdrop() {
    // 移除所有模态框遮罩
    const modalBackdrops = document.querySelectorAll('.modal-backdrop');
    modalBackdrops.forEach(backdrop => {
        backdrop.remove();
    });
    
    // 移除body上的modal-open类和样式
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    initDragAndDrop();
    initFileUploadForm();
    
    // 为所有模态框添加关闭事件监听器，确保清理遮罩
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('hidden.bs.modal', function() {
            // 如果是预览模态框，清空iframe内容
            if (this.id === 'preview-site-modal') {
                const previewIframe = document.getElementById('preview-iframe');
                if (previewIframe) {
                    previewIframe.src = '';
                }
            }
            
            // 清理遮罩和样式
            cleanupModalBackdrop();
        });
    });
    
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

// 站点状态轮询
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 查找所有处于 pending 状态的站点
    const pendingSites = document.querySelectorAll('tr[data-status="pending"]');
    
    // 如果有处于 pending 状态的站点，开始轮询
    if (pendingSites.length > 0) {
        pendingSites.forEach(site => {
            const siteId = site.getAttribute('data-site-id');
            if (siteId) {
                pollSiteStatus(siteId);
            }
        });
    }
});

// 轮询站点状态
function pollSiteStatus(siteId) {
    const pollInterval = 3000; // 3秒轮询一次
    const maxAttempts = 60; // 最多轮询60次（3分钟）
    let attempts = 0;
    
    const statusCell = document.querySelector(`tr[data-site-id="${siteId}"] td:nth-child(4)`);
    const actionsCell = document.querySelector(`tr[data-site-id="${siteId}"] td:nth-child(5)`);
    
    if (!statusCell || !actionsCell) return;
    
    const interval = setInterval(() => {
        attempts++;
        
        fetch(`/api/site/${siteId}/status`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const site = data.data;
                    
                    // 更新状态单元格
                    if (site.status === 'completed') {
                        statusCell.innerHTML = `
                            <div class="form-check form-switch">
                                <input class="form-check-input toggle-publish-status" type="checkbox" role="switch" 
                                       id="publish-status-${site.id}" 
                                       data-site-id="${site.id}" 
                                       ${site.is_published ? 'checked' : ''}>
                                <label class="form-check-label" for="publish-status-${site.id}">
                                    <span class="publish-status-label ${site.is_published ? 'text-success' : 'text-secondary'}">
                                        ${site.is_published ? '已发布' : '未发布'}
                                    </span>
                                </label>
                            </div>
                        `;
                        
                        // 更新操作单元格，添加查看和预览按钮
                        actionsCell.innerHTML = `
                            <div class="btn-group btn-group-sm">
                                <a href="${site.oss_url}" target="_blank" class="btn btn-outline-primary">
                                    <i class="bi bi-eye"></i> 查看
                                </a>
                                <button class="btn btn-outline-info preview-site-btn" data-site-id="${site.id}" data-site-url="${site.oss_url}">
                                    <i class="bi bi-window"></i> 预览
                                </button>
                                <button class="btn btn-outline-secondary rename-site-btn" data-site-id="${site.id}" data-site-name="${site.name}">
                                    <i class="bi bi-pencil"></i> 重命名
                                </button>
                                <button class="btn btn-outline-danger delete-site-btn" data-site-id="${site.id}" data-site-name="${site.name}">
                                    <i class="bi bi-trash"></i> 删除
                                </button>
                            </div>
                        `;
                        
                        // 停止轮询
                        clearInterval(interval);
                        
                        // 初始化新按钮的事件监听器
                        initButtonListeners();
                        
                        // 显示成功提示
                        showToast('成功', `站点 "${site.name}" 已成功发布！`, 'success');
                        
                    } else if (site.status === 'failed') {
                        statusCell.innerHTML = `
                            <span class="badge bg-danger">处理失败</span>
                            <i class="bi bi-info-circle text-danger" data-bs-toggle="tooltip" title="${site.error_message || '未知错误'}"></i>
                        `;
                        
                        // 停止轮询
                        clearInterval(interval);
                        
                        // 初始化工具提示
                        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                        tooltipTriggerList.map(function (tooltipTriggerEl) {
                            return new bootstrap.Tooltip(tooltipTriggerEl);
                        });
                        
                        // 显示错误提示
                        showToast('失败', `站点 "${site.name}" 处理失败: ${site.error_message || '未知错误'}`, 'danger');
                    }
                    
                    // 更新行的状态属性
                    const row = document.querySelector(`tr[data-site-id="${siteId}"]`);
                    if (row) {
                        row.setAttribute('data-status', site.status);
                    }
                }
            })
            .catch(error => {
                console.error('轮询站点状态失败:', error);
            });
        
        // 如果达到最大尝试次数，停止轮询
        if (attempts >= maxAttempts) {
            clearInterval(interval);
            statusCell.innerHTML = `
                <span class="badge bg-secondary">超时</span>
            `;
            showToast('超时', '站点状态轮询超时，请刷新页面查看最新状态', 'warning');
        }
    }, pollInterval);
}

// 初始化按钮事件监听器
function initButtonListeners() {
    // 预览站点按钮
    document.querySelectorAll('.preview-site-btn').forEach(button => {
        button.addEventListener('click', function() {
            const siteUrl = this.getAttribute('data-site-url');
            const previewIframe = document.getElementById('preview-iframe');
            const previewFullLink = document.getElementById('preview-full-link');
            
            if (previewIframe && siteUrl) {
                previewIframe.src = siteUrl;
            }
            
            if (previewFullLink && siteUrl) {
                previewFullLink.href = siteUrl;
            }
            
            // 显示预览模态框
            const previewModal = new bootstrap.Modal(document.getElementById('preview-site-modal'));
            previewModal.show();
        });
    });
    
    // 重命名站点按钮
    document.querySelectorAll('.rename-site-btn').forEach(button => {
        button.addEventListener('click', function() {
            const siteId = this.getAttribute('data-site-id');
            const siteName = this.getAttribute('data-site-name');
            
            document.getElementById('rename-site-id').value = siteId;
            document.getElementById('rename-site-name').value = siteName;
            
            // 显示重命名模态框
            const renameModal = new bootstrap.Modal(document.getElementById('rename-site-modal'));
            renameModal.show();
        });
    });
    
    // 删除站点按钮
    document.querySelectorAll('.delete-site-btn').forEach(button => {
        button.addEventListener('click', function() {
            const siteId = this.getAttribute('data-site-id');
            const siteName = this.getAttribute('data-site-name');
            
            document.getElementById('delete-site-name').textContent = siteName;
            document.getElementById('confirm-delete-btn').setAttribute('data-site-id', siteId);
            
            // 显示删除确认模态框
            const deleteModal = new bootstrap.Modal(document.getElementById('delete-site-modal'));
            deleteModal.show();
        });
    });
    
    // 切换发布状态
    document.querySelectorAll('.toggle-publish-status').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const siteId = this.getAttribute('data-site-id');
            const isChecked = this.checked;
            
            // 发送请求切换发布状态
            fetch(`/toggle_site_visibility/${siteId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 更新标签文本和样式
                    const label = document.querySelector(`label[for="publish-status-${siteId}"] .publish-status-label`);
                    if (label) {
                        label.textContent = data.is_published ? '已发布' : '未发布';
                        label.className = `publish-status-label ${data.is_published ? 'text-success' : 'text-secondary'}`;
                    }
                    
                    showToast('成功', data.msg, 'success');
                } else {
                    // 恢复复选框状态
                    this.checked = !isChecked;
                    showToast('错误', data.msg, 'danger');
                }
            })
            .catch(error => {
                console.error('切换发布状态失败:', error);
                // 恢复复选框状态
                this.checked = !isChecked;
                showToast('错误', '切换发布状态失败', 'danger');
            });
        });
    });
}

// 初始化页面上已有的按钮事件监听器
document.addEventListener('DOMContentLoaded', function() {
    initButtonListeners();
}); 
// Toast 通知工具类
function showToast(message, type = 'info') {
    // 创建 toast 容器（如果不存在）
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    // 创建新的 toast 元素
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type}">
                <strong class="me-auto text-white">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;

    // 添加 toast 到容器
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    // 初始化 Bootstrap toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        animation: true,
        autohide: true,
        delay: 3000
    });

    // 显示 toast
    toast.show();

    // toast 隐藏后删除元素
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
        // 如果容器为空，也删除容器
        if (toastContainer.children.length === 0) {
            toastContainer.remove();
        }
    });
}

// 导出函数
window.showToast = showToast;

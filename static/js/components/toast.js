// Toast 通知组件
class Toast {
    constructor() {
        this.createToastContainer();
    }

    // 创建 Toast 容器
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
        `;
        document.body.appendChild(container);
    }

    // 显示 Toast 消息
    show(message, type = 'success', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.cssText = `
            background: ${this.getBackgroundColor(type)};
            color: white;
            padding: 12px 24px;
            border-radius: 4px;
            margin-bottom: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            animation: slideIn 0.3s ease-out;
        `;

        toast.innerHTML = `
            <div style="display: flex; align-items: center;">
                <i class="fa ${this.getIcon(type)}" style="margin-right: 8px;"></i>
                <span>${message}</span>
            </div>
        `;

        const container = document.getElementById('toastContainer');
        container.appendChild(toast);

        // 自动消失
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => container.removeChild(toast), 280);
        }, duration);
    }

    // 获取背景颜色
    getBackgroundColor(type) {
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8'
        };
        return colors[type] || colors.info;
    }

    // 获取图标
    getIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-times-circle',
            warning: 'fa-exclamation-circle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }
}

// 创建全局 Toast 实例
const toast = new Toast();

// 全局显示 Toast 的函数
function showToast(message, type = 'success', duration = 3000) {
    toast.show(message, type, duration);
}

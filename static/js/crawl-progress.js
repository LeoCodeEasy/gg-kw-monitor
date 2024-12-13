// 爬取进度处理模块
const CrawlProgress = {
    button: null,
    progressBar: null,
    
    init() {
        // 获取DOM元素
        this.button = document.querySelector('#crawlButton');
        if (!this.button) {
            // 创建进度条结构
            const originalButton = document.querySelector('button[onclick="startCrawl()"]');
            if (originalButton) {
                originalButton.id = 'crawlButton';
                originalButton.innerHTML = `
                    <div class="button-content">
                        <i class="fa fa-search"></i>
                        <span>开始爬取</span>
                    </div>
                    <div class="progress-overlay d-none">
                        <div class="progress">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                 role="progressbar" 
                                 style="width: 0%" 
                                 aria-valuenow="0" 
                                 aria-valuemin="0" 
                                 aria-valuemax="100">0%</div>
                        </div>
                    </div>
                `;
                this.button = originalButton;
            }
        }
        this.progressBar = this.button?.querySelector('.progress-bar');
    },
    
    // 开始爬取
    start() {
        if (!this.button || !this.progressBar) return;
        
        // 禁用按钮
        this.button.disabled = true;
        
        // 显示进度条
        this.button.querySelector('.progress-overlay').classList.remove('d-none');
        
        // 重置进度
        this.updateProgress(0);
    },
    
    // 更新进度
    updateProgress(percentage) {
        if (!this.progressBar) return;
        
        percentage = Math.min(Math.max(percentage, 0), 100);
        this.progressBar.style.width = percentage + '%';
        this.progressBar.textContent = Math.round(percentage) + '%';
        this.progressBar.setAttribute('aria-valuenow', percentage);
    },
    
    // 完成爬取
    complete() {
        if (!this.button || !this.progressBar) return;
        
        // 更新到100%
        this.updateProgress(100);
        
        // 延迟后重置
        setTimeout(() => {
            // 启用按钮
            this.button.disabled = false;
            
            // 隐藏进度条
            this.button.querySelector('.progress-overlay').classList.add('d-none');
            
            // 重置进度
            this.updateProgress(0);
        }, 1000);
    },
    
    // 发生错误
    error() {
        if (!this.button) return;
        
        // 启用按钮
        this.button.disabled = false;
        
        // 隐藏进度条
        this.button.querySelector('.progress-overlay').classList.add('d-none');
        
        // 重置进度
        this.updateProgress(0);
    }
};

// 添加样式
const style = document.createElement('style');
style.textContent = `
    #crawlButton {
        position: relative;
        overflow: hidden;
    }
    
    .progress-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.2);
        display: flex;
        align-items: center;
        padding: 0 10px;
    }
    
    .progress {
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.2);
        border-radius: 0;
    }
    
    .progress-bar {
        background-color: rgba(255, 255, 255, 0.4);
        color: #fff;
        font-size: 12px;
        line-height: 32px;
        text-align: center;
        transition: width 0.3s ease;
    }
    
    .button-content {
        position: relative;
        z-index: 1;
    }
`;
document.head.appendChild(style);

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    CrawlProgress.init();
}); 
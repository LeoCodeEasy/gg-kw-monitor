// 广告展示管理器
class AdDisplayManager {
    constructor() {
        this.adsContainer = document.getElementById('adsContainer');
        this.currentAds = new Map();
    }

    // 创建广告卡片
    createAdCard(adData) {
        const card = document.createElement('div');
        card.className = 'col-md-6 col-lg-4 mb-4';
        card.innerHTML = `
            <div class="card h-100">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <span class="badge bg-primary">${adData.keyword}</span>
                    <small class="text-muted">${DateFormatter.formatRelativeTime(adData.timestamp)}</small>
                </div>
                <div class="card-body">
                    <h5 class="card-title">${this.escapeHtml(adData.title)}</h5>
                    <p class="card-text">${this.escapeHtml(adData.description)}</p>
                    ${adData.imageUrl ? `
                        <div class="text-center mb-3">
                            <img src="${adData.imageUrl}" 
                                 class="img-thumbnail ad-image" 
                                 alt="广告图片"
                                 style="cursor: pointer; max-height: 150px;"
                                 onclick="imagePreview.showPreview('${adData.imageUrl}')">
                        </div>
                    ` : ''}
                    <div class="d-flex justify-content-between align-items-center">
                        <a href="${adData.url}" target="_blank" class="btn btn-primary btn-sm">
                            <i class="fas fa-external-link-alt"></i> 访问链接
                        </a>
                        <div class="btn-group">
                            <button class="btn btn-outline-secondary btn-sm" onclick="navigator.clipboard.writeText('${adData.url}')">
                                <i class="fas fa-copy"></i>
                            </button>
                            <button class="btn btn-outline-danger btn-sm" onclick="adDisplayManager.removeAd('${adData.id}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        return card;
    }

    // 显示广告
    displayAd(adData) {
        if (!this.adsContainer) {
            console.error('广告容器未找到');
            return;
        }

        // 如果广告已存在，先移除旧的
        if (this.currentAds.has(adData.id)) {
            this.removeAd(adData.id);
        }

        const adCard = this.createAdCard(adData);
        this.adsContainer.appendChild(adCard);
        this.currentAds.set(adData.id, adCard);
    }

    // 移除广告
    removeAd(adId) {
        const adCard = this.currentAds.get(adId);
        if (adCard) {
            adCard.remove();
            this.currentAds.delete(adId);
        }
    }

    // 清空所有广告
    clearAds() {
        if (this.adsContainer) {
            this.adsContainer.innerHTML = '';
            this.currentAds.clear();
        }
    }

    // HTML转义
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// 创建全局实例
window.adDisplayManager = new AdDisplayManager();

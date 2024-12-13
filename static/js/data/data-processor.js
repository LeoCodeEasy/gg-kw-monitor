// 数据处理模块
const DataProcessor = {
    // 处理广告数据
    processAdData(ad) {
        if (!ad || !Array.isArray(ad.keyword_records)) {
            return null;
        }

        // 确保所有必要的字段存在
        return {
            ...ad,
            landing_page: ad.landing_page || '',
            keyword_records: ad.keyword_records.map(record => ({
                keyword: record.keyword || '',
                market: record.market || '',
                title: record.title || '',
                timestamp: record.timestamp || new Date().toISOString(),
                description: record.description || ''
            }))
        };
    },

    // 规范化URL
    normalizeUrl(url) {
        if (!url) return '';
        
        // 如果是 Google Ads 的点击链接
        if (url.startsWith('https://www.google.com') && url.includes('/aclk?')) {
            const baseParams = [];
            url.split('&').forEach(param => {
                if (param.startsWith('sa=') || param.startsWith('ai=')) {
                    baseParams.push(param);
                }
            });
            if (baseParams.length > 0) {
                return 'https://www.google.com/aclk?' + baseParams.join('&');
            }
        }
        return url;
    },

    // 格式化日期
    formatDate(date) {
        if (!date) return '';
        return new Date(date).toLocaleString();
    },

    // 获取域名
    getDomain(url) {
        try {
            return new URL(url).hostname;
        } catch {
            return '未知域名';
        }
    },

    // 处理市场代码到名称的映射
    getMarketName(marketCode) {
        const marketNames = {
            'in': 'INDIA',
            'gh': 'GHANA',
            'sg': 'SINGAPORE',
            'us': 'USA',
            'uk': 'UK'
        };
        return marketNames[marketCode] || marketCode.toUpperCase();
    },

    // 获取市场对应的样式
    getMarketColor(market) {
        const colors = {
            'in': 'primary',
            'gh': 'success',
            'ng': 'info',
            'ke': 'warning',
            'za': 'secondary'
        };
        return colors[market] || 'secondary';
    },

    // 处理关键词数据
    processKeywords(keywords) {
        return keywords
            .split('\n')
            .map(k => k.trim())
            .filter(k => k);
    }
};

// 导出模块
window.DataProcessor = DataProcessor; 
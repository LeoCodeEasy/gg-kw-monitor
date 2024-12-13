// API 客户端模块
const ApiClient = {
    // 配置
    config: {
        timeout: 30000,        // 请求超时时间（毫秒）
        maxRetries: 3,         // 最大重试次数
        retryDelay: 1000,      // 重试延迟（毫秒）
        retryStatusCodes: [408, 429, 500, 502, 503, 504] // 需要重试的状态码
    },

    // 延迟函数
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    // 带超时的fetch
    async fetchWithTimeout(url, options = {}) {
        const controller = new AbortController();
        const timeout = options.timeout || this.config.timeout;
        
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            throw error;
        }
    },

    // 基础请求方法（带重试）
    async request(url, options = {}) {
        let lastError;
        let retryCount = 0;

        while (retryCount <= this.config.maxRetries) {
            try {
                const response = await this.fetchWithTimeout(url, {
                    ...options,
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    }
                });

                // 检查是否需要重试
                if (!response.ok && this.config.retryStatusCodes.includes(response.status)) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                return { success: true, data };

            } catch (error) {
                lastError = error;
                
                // 如果是超时错误或需要重试的状态码
                if (error.name === 'AbortError' || 
                    (error.response && this.config.retryStatusCodes.includes(error.response.status))) {
                    
                    retryCount++;
                    if (retryCount <= this.config.maxRetries) {
                        // 计算延迟时间（指数退避）
                        const delay = this.config.retryDelay * Math.pow(2, retryCount - 1);
                        console.log(`Retry ${retryCount}/${this.config.maxRetries} after ${delay}ms`);
                        await this.delay(delay);
                        continue;
                    }
                }
                
                return { 
                    success: false, 
                    error: error.message || '请求失败',
                    isTimeout: error.name === 'AbortError'
                };
            }
        }

        return { 
            success: false, 
            error: `请求失败，已重试 ${this.config.maxRetries} 次: ${lastError.message}`,
            isTimeout: lastError.name === 'AbortError'
        };
    },

    // 获取最新结果
    async fetchLatestResults() {
        return await this.request('/latest');
    },

    // 获取关键词列表
    async fetchKeywords() {
        return await this.request('/keywords');
    },

    // 保存关键词列表
    async saveKeywords(keywords) {
        return await this.request('/keywords', {
            method: 'POST',
            body: JSON.stringify(keywords)
        });
    },

    // 开始爬取（添加进度回调）
    async startCrawl(keywords, progressCallback) {
        let progress = 0;
        const total = keywords.length;
        
        try {
            const response = await this.request('/crawl', {
                method: 'POST',
                body: JSON.stringify(keywords)
            });

            // 更新进度
            if (progressCallback) {
                progress = total;
                progressCallback(progress, total);
            }

            return response;
        } catch (error) {
            console.error('Crawl failed:', error);
            return { 
                success: false, 
                error: error.message || '爬取失败'
            };
        }
    },

    // 删除记录
    async deleteRecord(landingPage) {
        return await this.request('/delete_record', {
            method: 'POST',
            body: JSON.stringify({ landing_page: landingPage })
        });
    },

    // 扩展关键词
    async expandKeywords(category) {
        return await this.request('/expand_keywords', {
            method: 'POST',
            body: JSON.stringify({ category })
        });
    },

    // 代理请求
    async proxyRequest(url) {
        return await this.request(`/proxy?${new URLSearchParams({ url })}`);
    },

    // 移动端预览
    async mobilePreview(url) {
        return await this.request(`/mobile_proxy?${new URLSearchParams({ url })}`);
    },

    // 资源代理
    async resourceProxy(url) {
        return await this.request(`/resource_proxy?${new URLSearchParams({ url })}`);
    }
};

// 错误处理中间件
const ApiMiddleware = {
    // 处理API响应
    handleResponse(response) {
        if (!response.success) {
            // 根据错误类型显示不同的提示
            const message = response.isTimeout ? 
                '请求超时，请稍后重试' : 
                response.error;

            if (window.ToastModule) {
                window.ToastModule.show(message, 'error');
            }
            return null;
        }
        return response.data;
    },

    // 包装API方法
    wrapApiMethod(method) {
        return async (...args) => {
            const response = await method.apply(ApiClient, args);
            return this.handleResponse(response);
        };
    }
};

// 包装所有API方法
Object.keys(ApiClient).forEach(key => {
    if (typeof ApiClient[key] === 'function' && key !== 'delay' && key !== 'fetchWithTimeout') {
        const originalMethod = ApiClient[key];
        ApiClient[key] = ApiMiddleware.wrapApiMethod(originalMethod);
    }
});

// 导出模块
window.ApiClient = ApiClient; 
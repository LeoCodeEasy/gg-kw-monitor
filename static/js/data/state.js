// 状态管理模块
const StateModule = {
    // 核心状态
    state: {
        allResults: [],
        currentKeywords: [],
        selectedMarket: '',
        selectedCategory: '',
        searchText: '',
        lastUpdated: null
    },

    // 监听器列表
    listeners: [],

    // 注册状态变化监听器
    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    },

    // 通知所有监听器
    notifyListeners() {
        this.listeners.forEach(listener => listener(this.state));
    },

    // 获取当前状态
    getState() {
        return { ...this.state };
    },

    // 设置搜索结果
    setResults(results) {
        this.state.allResults = results;
        this.state.lastUpdated = new Date();
        this.notifyListeners();
    },

    // 设置当前关键词列表
    setKeywords(keywords) {
        this.state.currentKeywords = keywords;
        this.notifyListeners();
    },

    // 设置选中的市场
    setSelectedMarket(market) {
        this.state.selectedMarket = market;
        this.notifyListeners();
    },

    // 设置选中的分类
    setSelectedCategory(category) {
        this.state.selectedCategory = category;
        this.notifyListeners();
    },

    // 设置搜索文本
    setSearchText(text) {
        this.state.searchText = text;
        this.notifyListeners();
    },

    // 获取过滤后的结果
    getFilteredResults() {
        let filteredResults = [...this.state.allResults];
        
        // 按市场筛选
        if (this.state.selectedMarket) {
            filteredResults = filteredResults.map(ad => ({
                ...ad,
                keyword_records: ad.keyword_records.filter(record => 
                    record.market === this.state.selectedMarket
                )
            })).filter(ad => ad.keyword_records.length > 0);
        }

        // 按分类筛选
        if (this.state.selectedCategory) {
            filteredResults = filteredResults.map(ad => ({
                ...ad,
                keyword_records: ad.keyword_records.filter(record => {
                    const keywordData = this.state.currentKeywords.find(k => 
                        k.category === this.state.selectedCategory && 
                        k.keywords.includes(record.keyword)
                    );
                    return keywordData !== undefined;
                })
            })).filter(ad => ad.keyword_records.length > 0);
        }

        // 按搜索文本筛选
        if (this.state.searchText) {
            const searchText = this.state.searchText.toLowerCase();
            filteredResults = filteredResults.map(ad => ({
                ...ad,
                keyword_records: ad.keyword_records.filter(record => {
                    const keyword = (record.keyword || '').toLowerCase();
                    const title = (record.title || '').toLowerCase();
                    const url = (ad.landing_page || '').toLowerCase();
                    return keyword.includes(searchText) || 
                           title.includes(searchText) || 
                           url.includes(searchText);
                })
            })).filter(ad => ad.keyword_records.length > 0);
        }

        return filteredResults;
    },

    // 获取所有市场列表
    getMarkets() {
        const markets = new Set();
        this.state.allResults.forEach(ad => {
            if (ad.keyword_records) {
                ad.keyword_records.forEach(record => {
                    if (record.market) markets.add(record.market);
                });
            }
        });
        return Array.from(markets).sort();
    },

    // 获取统计信息
    getStats() {
        return {
            totalKeywords: this.state.currentKeywords.length,
            totalAds: this.state.allResults.length,
            lastUpdated: this.state.lastUpdated
        };
    }
};

// 导出模块
window.StateModule = StateModule; 
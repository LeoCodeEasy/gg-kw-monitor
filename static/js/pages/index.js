// 页面状态管理
let allResults = [];
let currentKeywords = [];

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化事件监听
    initEventListeners();
    
    // 加载数据
    loadData();
});

// 初始化事件监听
function initEventListeners() {
    // 搜索框事件
    const searchInput = document.getElementById('keywordFilter');
    const clearSearchBtn = document.getElementById('clearSearch');
    
    searchInput.addEventListener('input', function() {
        clearSearchBtn.style.display = this.value ? 'flex' : 'none';
        filterAndDisplayResults();
    });
    
    clearSearchBtn.addEventListener('click', function() {
        searchInput.value = '';
        this.style.display = 'none';
        filterAndDisplayResults();
    });

    // 市场标签点击事件
    document.getElementById('marketTabs').addEventListener('click', function(e) {
        const tab = e.target.closest('.market-tab');
        if (tab) {
            // 更新激活状态
            document.querySelectorAll('.market-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // 更新状态并刷新显示
            StateModule.setSelectedMarket(tab.getAttribute('data-market'));
            filterAndDisplayResults();
        }
    });
}

// 加载数据
async function loadData() {
    try {
        // 加载关键词数据
        const keywordsResponse = await fetch('/api/keywords');
        if (!keywordsResponse.ok) {
            throw new Error('加载关键词数据失败');
        }
        const keywordsData = await keywordsResponse.json();
        currentKeywords = keywordsData.keywords || [];
        
        // 加载结果数据
        const resultsResponse = await fetch('/api/results');
        if (!resultsResponse.ok) {
            throw new Error('加载结果数据失败');
        }
        const resultsData = await resultsResponse.json();
        allResults = resultsData.results || [];
        
        // 更新显示
        updateMarketTabs();
        filterAndDisplayResults();
        
        // 更新统计信息
        updateStats(resultsData.last_updated);
        
    } catch (error) {
        console.error('加载数据失败:', error);
        showToast('加载数据失败', 'error');
    }
}

// 更新市场标签
function updateMarketTabs() {
    const marketTabs = document.getElementById('marketTabs');
    const markets = Array.from(new Set(allResults.flatMap(ad => 
        ad.keyword_records.map(record => record.market)
    )));
    
    // 清空现有标签
    marketTabs.innerHTML = '<div class="market-tab active" data-market="">全部</div>';
    
    // 添加市场标签
    markets.forEach(market => {
        if (market) {
            const tab = document.createElement('div');
            tab.className = 'market-tab';
            tab.setAttribute('data-market', market);
            tab.textContent = market;
            marketTabs.appendChild(tab);
        }
    });
}

// 更新统计信息
function updateStats(lastUpdated) {
    document.getElementById('totalKeywords').textContent = currentKeywords.length;
    document.getElementById('totalAds').textContent = allResults.length;
    document.getElementById('lastUpdated').textContent = 
        lastUpdated ? new Date(lastUpdated).toLocaleString() : '-';
}

// 过滤并显示结果
function filterAndDisplayResults() {
    const searchText = document.getElementById('keywordFilter').value.toLowerCase();
    const selectedMarket = document.querySelector('.market-tab.active').getAttribute('data-market');
    
    let filteredResults = [...allResults];
    
    // 按市场筛选
    if (selectedMarket) {
        filteredResults = filteredResults.map(ad => ({
            ...ad,
            keyword_records: ad.keyword_records.filter(record => 
                record.market === selectedMarket
            )
        })).filter(ad => ad.keyword_records.length > 0);
    }
    
    // 按搜索文本筛选
    if (searchText) {
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
    
    // 更新显示
    displayResults(filteredResults);
}

// 显示结果
function displayResults(results) {
    const container = document.getElementById('resultsContainer');
    // 这里添加结果显示的具体实现
}

// 导出模块
window.startCrawl = startCrawl;

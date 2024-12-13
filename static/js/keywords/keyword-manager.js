// 关键词管理类
class KeywordManager {
    constructor() {
        this.keywordsData = {};
        this.keywordsModal = null;
        this.initEventListeners();
    }

    // 初始化事件监听
    initEventListeners() {
        // 等待 DOM 加载完成
        document.addEventListener('DOMContentLoaded', () => {
            // 初始化模态框
            const modalElement = document.getElementById('keywordsModal');
            if (modalElement) {
                this.keywordsModal = new bootstrap.Modal(modalElement);
            }

            // 初始化搜索框
            const keywordFilter = document.getElementById('keywordFilter');
            if (keywordFilter) {
                keywordFilter.addEventListener('input', (event) => {
                    const clearBtn = document.getElementById('clearSearch');
                    if (clearBtn) {
                        clearBtn.style.display = event.target.value ? 'inline-block' : 'none';
                    }
                });
            }

            // 初始化清除按钮
            const clearBtn = document.getElementById('clearSearch');
            if (clearBtn) {
                clearBtn.addEventListener('click', () => {
                    const keywordFilter = document.getElementById('keywordFilter');
                    if (keywordFilter) {
                        keywordFilter.value = '';
                        clearBtn.style.display = 'none';
                    }
                });
            }
        });
    }

    // 打开关键词编辑器
    async openKeywordsEditor() {
        try {
            await this.loadKeywords();
            this.updateKeywordsList();
            if (this.keywordsModal) {
                this.keywordsModal.show();
            } else {
                const modalElement = document.getElementById('keywordsModal');
                if (modalElement) {
                    this.keywordsModal = new bootstrap.Modal(modalElement);
                    this.keywordsModal.show();
                } else {
                    console.error('关键词编辑器模态框未找到');
                    if (typeof showToast === 'function') {
                        showToast('无法打开关键词编辑器', 'error');
                    } else {
                        alert('无法打开关键词编辑器');
                    }
                }
            }
        } catch (error) {
            console.error('打开关键词编辑器失败:', error);
            if (typeof showToast === 'function') {
                showToast('打开关键词编辑器失败: ' + error.message, 'error');
            } else {
                alert('打开关键词编辑器失败: ' + error.message);
            }
        }
    }

    // 加载关键词数据
    async loadKeywords() {
        try {
            const response = await fetch('/api/keywords');
            if (!response.ok) {
                throw new Error(`加载失败: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.keywordsData = data.keywords || {};
            this.updateCategorySelect();
            this.updateKeywordsList();
            return true;
        } catch (error) {
            console.error('加载关键词失败:', error);
            showToast('加载关键词失败: ' + error.message, 'error');
            return false;
        }
    }

    // 更新分类选择框
    updateCategorySelect() {
        const select = document.getElementById('categorySelect');
        if (!select) return;

        // 清空现有选项
        select.innerHTML = '<option value="">选择分类...</option>';

        // 添加分类选项
        Object.keys(this.keywordsData).forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            select.appendChild(option);
        });
    }

    // 更新关键词列表
    updateKeywordsList() {
        const container = document.querySelector('.keywords-list');
        if (!container) return;

        if (Object.keys(this.keywordsData).length === 0) {
            container.innerHTML = `
                <div class="keywords-empty">
                    <i class="fas fa-info-circle"></i>
                    暂无关键词，点击"添加分类"开始添加
                </div>
            `;
            return;
        }

        let html = '';
        for (const [category, data] of Object.entries(this.keywordsData)) {
            if (!data || !Array.isArray(data.keywords)) continue;

            html += `
                <div class="category-section">
                    <div class="category-header">
                        <span class="category-name">${category}</span>
                        <div class="category-actions">
                            <label class="switch">
                                <input type="checkbox" ${data.enabled ? 'checked' : ''} 
                                       onchange="keywordManager.toggleCategory('${category}')">
                                <span class="slider"></span>
                            </label>
                            <button class="btn btn-sm btn-outline-danger btn-keyword" 
                                    onclick="keywordManager.deleteCategory('${category}')">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-primary btn-keyword" 
                                    onclick="keywordManager.batchAddKeywords('${category}')">
                                <i class="fas fa-plus"></i> 批量添加
                            </button>
                        </div>
                    </div>
                    <div class="keywords-container">
                        ${data.keywords.length > 0 ? 
                            data.keywords.map(keyword => {
                                const keywordText = typeof keyword === 'string' ? keyword : keyword.text;
                                const keywordEnabled = typeof keyword === 'string' ? true : keyword.enabled;
                                
                                return `
                                    <div class="keyword-item">
                                        <span class="keyword-text">${keywordText}</span>
                                        <div class="keyword-actions">
                                            <label class="switch">
                                                <input type="checkbox" ${keywordEnabled ? 'checked' : ''} 
                                                       onchange="keywordManager.toggleKeyword('${category}', '${keywordText}')">
                                                <span class="slider"></span>
                                            </label>
                                            <button class="btn btn-sm btn-outline-danger btn-keyword" 
                                                    onclick="keywordManager.deleteKeyword('${category}', '${keywordText}')">
                                                <i class="fas fa-trash-alt"></i>
                                            </button>
                                        </div>
                                    </div>
                                `;
                            }).join('') 
                            : '<div class="text-muted text-center py-3">暂无关键词</div>'
                        }
                    </div>
                </div>
            `;
        }

        container.innerHTML = html;
    }

    // 批量添加关键词
    async batchAddKeywords(categoryName) {
        try {
            // 验证分类是否存在
            if (!await this.categoryExists(categoryName)) {
                throw new Error('分类不存在');
            }

            // 弹出文本输入框
            const textArea = document.createElement('textarea');
            textArea.style.width = '100%';
            textArea.style.height = '200px';
            textArea.placeholder = '请输入关键词，每行一个';
            
            const dialog = document.createElement('div');
            dialog.className = 'modal fade';
            dialog.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">批量添加关键词到 "${categoryName}"</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <div class="form-text mb-2">每行输入一个关键词，重复的关键词将被忽略</div>
                                ${textArea.outerHTML}
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" id="confirmBatchAdd">确认添加</button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(dialog);
            const modal = new bootstrap.Modal(dialog);
            modal.show();

            // 处理确认添加事件
            return new Promise((resolve) => {
                dialog.querySelector('#confirmBatchAdd').addEventListener('click', async () => {
                    const keywords = dialog.querySelector('textarea').value
                        .split('\n')
                        .map(kw => kw.trim())
                        .filter(kw => kw.length > 0);

                    if (keywords.length === 0) {
                        showToast('请输入至少一个关键词', 'error');
                        return;
                    }

                    // 过滤重复关键词
                    const existingKeywords = new Set(
                        this.keywordsData[categoryName].keywords.map(k => k.text)
                    );
                    
                    const newKeywords = keywords.filter(kw => !existingKeywords.has(kw))
                        .map(text => ({
                            text,
                            enabled: true,
                            addedAt: new Date().toISOString()
                        }));

                    if (newKeywords.length === 0) {
                        showToast('所有关键词都已存在', 'warning');
                        return;
                    }

                    // 添加新关键词
                    this.keywordsData[categoryName].keywords.push(...newKeywords);
                    await this.saveKeywords();
                    await this.updateKeywordsList();

                    modal.hide();
                    dialog.addEventListener('hidden.bs.modal', () => {
                        dialog.remove();
                    });

                    showToast(`成功添加 ${newKeywords.length} 个关键词`);
                    resolve({
                        success: true,
                        added: newKeywords.length,
                        total: keywords.length
                    });
                });

                // 处理模态框关闭
                dialog.addEventListener('hidden.bs.modal', () => {
                    dialog.remove();
                    resolve({
                        success: false,
                        reason: 'cancelled'
                    });
                });
            });
        } catch (error) {
            console.error('批量添加关键词失败:', error);
            showToast(error.message || '批量添加关键词失败', 'error');
            return {
                success: false,
                error: error.message
            };
        }
    }

    // 添加新分类
    async addNewCategory() {
        try {
            // 输入验证
            const categoryName = await this.validateCategoryName();
            if (!categoryName) return;

            // 查库防冲突
            if (await this.categoryExists(categoryName)) {
                throw new Error('分类已存在');
            }

            // 明确的数据结构
            const newCategory = {
                enabled: true,
                keywords: [],
                createdAt: new Date().toISOString()
            };

            // 原子操作
            this.keywordsData[categoryName] = newCategory;
            await this.saveKeywords();
            
            // UI更新
            await this.updateKeywordsList();
            showToast('分类添加成功');
            
            return {
                success: true,
                category: categoryName,
                data: newCategory
            };
        } catch (error) {
            console.error('添加分类失败:', error);
            showToast(error.message || '添加分类失败', 'error');
            return {
                success: false,
                error: error.message
            };
        }
    }

    // 验证分类名称
    async validateCategoryName() {
        const categoryName = prompt('请输入新分类名称：');
        if (!categoryName) return null;
        
        // 验证格式
        if (!/^[\u4e00-\u9fa5a-zA-Z0-9_-]{1,20}$/.test(categoryName)) {
            showToast('分类名称只能包含中文、字母、数字、下划线和连字符，长度1-20个字符', 'error');
            return null;
        }
        
        return categoryName.trim();
    }

    // 检查分类是否存在
    async categoryExists(categoryName) {
        return Object.prototype.hasOwnProperty.call(this.keywordsData, categoryName);
    }

    // 删除分类
    async deleteCategory(category) {
        if (!confirm(`确定要删除分类"${category}"吗？`)) return;

        delete this.keywordsData[category];
        await this.saveKeywords();
        this.updateKeywordsList();
        if (typeof showToast === 'function') {
            showToast('分类删除成功');
        } else {
            alert('分类删除成功');
        }
    }

    // 添加关键词
    async addKeyword() {
        const category = document.getElementById('categorySelect').value;
        const keyword = document.getElementById('newKeyword').value.trim();

        if (!category) {
            if (typeof showToast === 'function') {
                showToast('请选择分类', 'error');
            } else {
                alert('请选择分类');
            }
            return;
        }

        if (!keyword) {
            if (typeof showToast === 'function') {
                showToast('请输入关键词', 'error');
            } else {
                alert('请输入关键词');
            }
            return;
        }

        // 确保分类存在且具有正确的数据结构
        if (!this.keywordsData[category]) {
            this.keywordsData[category] = {
                enabled: true,
                keywords: []
            };
        }

        // 确保 keywords 数组存在
        if (!Array.isArray(this.keywordsData[category].keywords)) {
            this.keywordsData[category].keywords = [];
        }

        // 检查关键词是否已存在
        if (this.keywordsData[category].keywords.some(k => k && k.text === keyword)) {
            if (typeof showToast === 'function') {
                showToast('关键词已存在', 'error');
            } else {
                alert('关键词已存在');
            }
            return;
        }

        // 添加新关键词
        this.keywordsData[category].keywords.push({
            text: keyword,
            enabled: true
        });

        await this.saveKeywords();
        document.getElementById('newKeyword').value = '';
        this.updateKeywordsList();
        
        if (typeof showToast === 'function') {
            showToast('关键词添加成功');
        } else {
            alert('关键词添加成功');
        }
    }

    // 删除关键词
    async deleteKeyword(category, keyword) {
        if (!confirm(`确定要删除关键词"${keyword}"吗？`)) return;

        const index = this.keywordsData[category].keywords.findIndex(k => k && k.text === keyword);
        if (index !== -1) {
            this.keywordsData[category].keywords.splice(index, 1);
            await this.saveKeywords();
            this.updateKeywordsList();
            if (typeof showToast === 'function') {
                showToast('关键词删除成功');
            } else {
                alert('关键词删除成功');
            }
        }
    }

    // 切换分类启用状态
    async toggleCategory(category) {
        if (this.keywordsData[category]) {
            this.keywordsData[category].enabled = !this.keywordsData[category].enabled;
            await this.saveKeywords();
            this.updateKeywordsList();
        }
    }

    // 切换关键词启用状态
    async toggleKeyword(category, keyword) {
        const keywordObj = this.keywordsData[category].keywords.find(k => k && k.text === keyword);
        if (keywordObj) {
            keywordObj.enabled = !keywordObj.enabled;
            await this.saveKeywords();
            this.updateKeywordsList();
        }
    }

    // 保存关键词数据
    async saveKeywords() {
        try {
            const response = await fetch('/resources/keywords.json', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.keywordsData)
            });

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            return true;
        } catch (error) {
            console.error('保存关键词失败:', error);
            if (typeof showToast === 'function') {
                showToast('保存关键词失败: ' + error.message, 'error');
            } else {
                alert('保存关键词失败: ' + error.message);
            }
            return false;
        }
    }

    // 更新统计信息
    updateStats() {
        const totalKeywordsElement = document.getElementById('totalKeywords');
        if (totalKeywordsElement) {
            let total = 0;
            Object.values(this.keywordsData).forEach(data => {
                total += data.keywords.length;
            });
            totalKeywordsElement.textContent = total;
        }
    }
}

// 创建全局实例
window.keywordManager = new KeywordManager();

// 图片预览管理器
class ImagePreview {
    constructor() {
        this.modal = null;
        this.modalImage = null;
        this.initModal();
    }

    initModal() {
        // 创建模态框（如果不存在）
        if (!document.getElementById('imagePreviewModal')) {
            const modalHtml = `
                <div class="modal fade" id="imagePreviewModal" tabindex="-1" aria-labelledby="imagePreviewModalLabel" aria-hidden="true">
                    <div class="modal-dialog modal-lg modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="imagePreviewModalLabel">图片预览</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body text-center">
                                <img id="previewImage" class="img-fluid" src="" alt="预览图片">
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalHtml);
        }

        // 初始化 Bootstrap 模态框
        this.modal = new bootstrap.Modal(document.getElementById('imagePreviewModal'));
        this.modalImage = document.getElementById('previewImage');
    }

    // 显示图片预览
    showPreview(imageUrl) {
        if (!imageUrl) {
            console.error('未提供图片URL');
            return;
        }

        if (this.modalImage) {
            this.modalImage.src = imageUrl;
            this.modal.show();
        } else {
            console.error('预览模态框未正确初始化');
        }
    }

    // 关闭预览
    closePreview() {
        if (this.modal) {
            this.modal.hide();
        }
    }
}

// 创建全局实例
window.imagePreview = new ImagePreview();

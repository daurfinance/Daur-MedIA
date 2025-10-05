// Daur MedIA Video Generation Interface
class VideoApp {
    constructor() {
        this.currentLang = 'ru';
        this.translations = {
            ru: {
                'hero.title': 'Создавайте видео с помощью ИИ',
                'hero.subtitle': 'Превратите ваши идеи в потрясающие видео с помощью передовой технологии HunyuanVideo от Tencent',
                'form.prompt.label': 'Описание видео',
                'form.prompt.placeholder': 'Например: Кот идет по траве, реалистичный стиль',
                'form.width.label': 'Ширина',
                'form.height.label': 'Высота',
                'form.steps.label': 'Шаги',
                'form.generate': 'Создать видео',
                'tasks.title': 'Мои задачи',
                'status.title': 'Статус системы',
                'notification.success': 'Задача успешно создана!',
                'notification.error': 'Произошла ошибка',
                'task.pending': 'Ожидание',
                'task.processing': 'Обработка',
                'task.completed': 'Завершено',
                'task.failed': 'Ошибка'
            },
            en: {
                'hero.title': 'Create Videos with AI',
                'hero.subtitle': 'Transform your ideas into stunning videos using advanced HunyuanVideo technology from Tencent',
                'form.prompt.label': 'Video Description',
                'form.prompt.placeholder': 'Example: A cat walks on the grass, realistic style',
                'form.width.label': 'Width',
                'form.height.label': 'Height',
                'form.steps.label': 'Steps',
                'form.generate': 'Generate Video',
                'tasks.title': 'My Tasks',
                'status.title': 'System Status',
                'notification.success': 'Task created successfully!',
                'notification.error': 'An error occurred',
                'task.pending': 'Pending',
                'task.processing': 'Processing',
                'task.completed': 'Completed',
                'task.failed': 'Failed'
            }
        };
        
        this.init();
    }

    init() {
        // Initialize Lucide icons
        lucide.createIcons();
        
        // Bind events
        this.bindEvents();
        
        // Load initial data
        this.loadTasks();
        
        // Set up auto-refresh
        setInterval(() => this.loadTasks(), 5000);
    }

    bindEvents() {
        // Form submission
        document.getElementById('videoForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.generateVideo();
        });

        // Language toggle
        document.getElementById('langToggle').addEventListener('click', () => {
            this.toggleLanguage();
        });

        // Status button
        document.getElementById('statusBtn').addEventListener('click', () => {
            this.showStatusModal();
        });

        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadTasks();
        });

        // Close status modal
        document.getElementById('closeStatusModal').addEventListener('click', () => {
            this.hideStatusModal();
        });

        // Close modal on backdrop click
        document.getElementById('statusModal').addEventListener('click', (e) => {
            if (e.target.id === 'statusModal') {
                this.hideStatusModal();
            }
        });
    }

    async generateVideo() {
        const form = document.getElementById('videoForm');
        const formData = new FormData(form);
        const generateBtn = document.getElementById('generateBtn');
        
        // Disable button and show loading
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i data-lucide="loader" class="w-5 h-5 animate-spin"></i><span>Создание...</span>';
        lucide.createIcons();

        try {
            const response = await fetch('/api/video/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: formData.get('prompt'),
                    video_width: parseInt(formData.get('video_width')),
                    video_height: parseInt(formData.get('video_height')),
                    infer_steps: parseInt(formData.get('infer_steps'))
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification(this.t('notification.success'), 'success');
                form.reset();
                // Reset form to default values
                document.getElementById('video_width').value = '1280';
                document.getElementById('video_height').value = '720';
                document.getElementById('infer_steps').value = '50';
                this.loadTasks();
            } else {
                this.showNotification(result.error || this.t('notification.error'), 'error');
            }
        } catch (error) {
            console.error('Error generating video:', error);
            this.showNotification(this.t('notification.error'), 'error');
        } finally {
            // Re-enable button
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i data-lucide="play" class="w-5 h-5"></i><span>' + this.t('form.generate') + '</span>';
            lucide.createIcons();
        }
    }

    async loadTasks() {
        try {
            const response = await fetch('/api/video/tasks');
            const result = await response.json();

            if (result.tasks) {
                this.renderTasks(result.tasks);
            }
        } catch (error) {
            console.error('Error loading tasks:', error);
        }
    }

    renderTasks(tasks) {
        const tasksList = document.getElementById('tasksList');
        
        if (tasks.length === 0) {
            tasksList.innerHTML = '<p class="text-white text-opacity-60 text-center py-8">Пока нет задач</p>';
            return;
        }

        tasksList.innerHTML = tasks.map(task => `
            <div class="bg-white bg-opacity-10 rounded-lg p-6 border border-white border-opacity-20">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex-1">
                        <h4 class="text-white font-medium mb-2">Задача #${task.id}</h4>
                        <p class="text-white text-opacity-80 text-sm mb-3">${task.prompt}</p>
                        <div class="flex items-center space-x-4 text-sm text-white text-opacity-60">
                            <span>${task.video_width}x${task.video_height}</span>
                            <span>${task.infer_steps} шагов</span>
                            <span>${new Date(task.created_at).toLocaleString()}</span>
                        </div>
                    </div>
                    <div class="flex items-center space-x-3">
                        <span class="px-3 py-1 rounded-full text-xs font-medium status-${task.status}">
                            ${this.t('task.' + task.status)}
                        </span>
                        ${task.status === 'completed' ? `
                            <button onclick="app.downloadVideo(${task.id})" class="glass-effect px-3 py-1 rounded text-white text-sm hover:bg-white hover:bg-opacity-20 transition-all">
                                <i data-lucide="download" class="w-4 h-4"></i>
                            </button>
                        ` : ''}
                    </div>
                </div>
                ${task.status === 'processing' ? `
                    <div class="w-full bg-white bg-opacity-20 rounded-full h-2">
                        <div class="bg-white h-2 rounded-full animate-pulse-slow" style="width: 60%"></div>
                    </div>
                ` : ''}
                ${task.error_message ? `
                    <div class="mt-3 p-3 bg-red-500 bg-opacity-20 rounded text-red-200 text-sm">
                        ${task.error_message}
                    </div>
                ` : ''}
            </div>
        `).join('');

        // Re-initialize icons
        lucide.createIcons();
    }

    async downloadVideo(taskId) {
        try {
            const response = await fetch(`/api/video/download/${taskId}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `video_${taskId}.mp4`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Ошибка скачивания', 'error');
            }
        } catch (error) {
            console.error('Error downloading video:', error);
            this.showNotification('Ошибка скачивания', 'error');
        }
    }

    async showStatusModal() {
        const modal = document.getElementById('statusModal');
        const content = document.getElementById('statusContent');
        
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        
        try {
            const response = await fetch('/api/video/api_status');
            const status = await response.json();
            
            content.innerHTML = `
                <div class="space-y-4">
                    <div class="flex justify-between">
                        <span>API Status:</span>
                        <span class="${status.initialized ? 'text-green-400' : 'text-red-400'}">
                            ${status.initialized ? 'Активен' : 'Неактивен'}
                        </span>
                    </div>
                    <div class="flex justify-between">
                        <span>Всего задач:</span>
                        <span>${status.total_tasks || 0}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>В ожидании:</span>
                        <span>${status.pending_tasks || 0}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Обрабатывается:</span>
                        <span>${status.processing_tasks || 0}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Завершено:</span>
                        <span>${status.completed_tasks || 0}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Ошибки:</span>
                        <span>${status.failed_tasks || 0}</span>
                    </div>
                </div>
            `;
        } catch (error) {
            content.innerHTML = '<p class="text-red-400">Ошибка загрузки статуса</p>';
        }
    }

    hideStatusModal() {
        const modal = document.getElementById('statusModal');
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    toggleLanguage() {
        this.currentLang = this.currentLang === 'ru' ? 'en' : 'ru';
        document.getElementById('langText').textContent = this.currentLang === 'ru' ? 'EN' : 'RU';
        this.updateTranslations();
    }

    updateTranslations() {
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            element.textContent = this.t(key);
        });

        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.t(key);
        });
    }

    t(key) {
        return this.translations[this.currentLang][key] || key;
    }

    showNotification(message, type = 'success') {
        const notification = document.getElementById('notification');
        const text = document.getElementById('notificationText');
        const icon = notification.querySelector('i');
        
        text.textContent = message;
        
        // Update icon based on type
        if (type === 'error') {
            icon.setAttribute('data-lucide', 'x-circle');
            notification.classList.add('bg-red-500');
            notification.classList.remove('bg-green-500');
        } else {
            icon.setAttribute('data-lucide', 'check-circle');
            notification.classList.add('bg-green-500');
            notification.classList.remove('bg-red-500');
        }
        
        lucide.createIcons();
        
        // Show notification
        notification.classList.remove('translate-x-full');
        
        // Hide after 3 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
        }, 3000);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VideoApp();
});

// Daur MedIA - AI Video Generation Platform
// JavaScript для улучшенного веб-интерфейса

class DaurMediaApp {
    constructor() {
        this.isInitialized = false;
        this.currentTab = 'generation';
        this.autoRefreshInterval = null;
        this.performanceChart = null;
        this.performanceData = [];
        
        this.init();
    }

    init() {
        // Инициализация Lucide иконок
        lucide.createIcons();
        
        // Привязка событий
        this.bindEvents();
        
        // Проверка статуса при загрузке
        this.checkStatus();
        
        // Загрузка задач
        this.loadTasks();
        
        // Настройка автообновления
        this.setupAutoRefresh();
        
        // Инициализация графика производительности
        this.initPerformanceChart();
        
        // Загрузка настроек
        this.loadSettings();
    }

    bindEvents() {
        // Основные кнопки
        document.getElementById('initBtn').addEventListener('click', () => this.initializeModel());
        document.getElementById('videoForm').addEventListener('submit', (e) => this.generateVideo(e));
        document.getElementById('refreshBtn').addEventListener('click', () => this.loadTasks());
        
        // Навигация по вкладкам
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });
        
        // Шаблоны промптов
        document.querySelectorAll('.template-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const prompt = e.currentTarget.dataset.prompt;
                document.getElementById('prompt').value = prompt;
                this.showNotification('Шаблон применен', 'Промпт загружен в форму');
            });
        });
        
        // Случайный сид
        document.getElementById('randomSeed').addEventListener('click', () => {
            const randomSeed = Math.floor(Math.random() * 2147483647);
            document.getElementById('seed').value = randomSeed;
        });
        
        // CFG Scale slider
        const cfgSlider = document.getElementById('cfg_scale');
        const cfgValue = document.getElementById('cfgValue');
        cfgSlider.addEventListener('input', (e) => {
            cfgValue.textContent = e.target.value;
        });
        
        // Кнопки тестирования
        document.getElementById('testCPU').addEventListener('click', () => this.runTest('cpu'));
        document.getElementById('testMemory').addEventListener('click', () => this.runTest('memory'));
        document.getElementById('testGPU').addEventListener('click', () => this.runTest('gpu'));
        document.getElementById('testQuickGeneration').addEventListener('click', () => this.runTest('quick_generation'));
        document.getElementById('testBatchGeneration').addEventListener('click', () => this.runTest('batch_generation'));
        document.getElementById('testModelLoad').addEventListener('click', () => this.runTest('model_load'));
        
        // Кнопки управления задачами
        document.getElementById('clearCompletedBtn').addEventListener('click', () => this.clearCompletedTasks());
        
        // Настройки
        document.getElementById('autoRefresh').addEventListener('change', (e) => this.updateAutoRefresh(e.target.value));
        document.getElementById('exportTasks').addEventListener('click', () => this.exportTasks());
        document.getElementById('clearAllTasks').addEventListener('click', () => this.clearAllTasks());
        document.getElementById('resetSettings').addEventListener('click', () => this.resetSettings());
    }

    async checkStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            
            this.updateStatusIndicator(status.initialized);
            this.updateSystemStats(status);
            this.isInitialized = status.initialized;
        } catch (error) {
            console.error('Ошибка проверки статуса:', error);
            this.showNotification('Ошибка', 'Не удалось проверить статус системы', 'error');
        }
    }

    updateStatusIndicator(initialized) {
        const indicator = document.getElementById('statusIndicator');
        const dot = indicator.querySelector('div');
        const text = indicator.querySelector('span');
        const generateBtn = document.getElementById('generateBtn');
        
        if (initialized) {
            dot.className = 'w-3 h-3 bg-green-500 rounded-full';
            text.textContent = 'Daur MedIA готов';
            generateBtn.disabled = false;
        } else {
            dot.className = 'w-3 h-3 bg-red-500 rounded-full animate-pulse';
            text.textContent = 'Не инициализирован';
            generateBtn.disabled = true;
        }
    }

    updateSystemStats(stats) {
        // Обновление статистики в header
        if (stats.cpu_percent !== undefined) {
            document.getElementById('cpuUsage').textContent = `${Math.round(stats.cpu_percent)}%`;
        }
        if (stats.memory_percent !== undefined) {
            document.getElementById('memUsage').textContent = `${Math.round(stats.memory_percent)}%`;
        }
        if (stats.gpu_info) {
            document.getElementById('gpuStatus').textContent = stats.gpu_info === 'N/A' ? 'N/A' : 'OK';
        }
        
        // Обновление метрик в мониторинге
        if (document.getElementById('cpuMetric')) {
            document.getElementById('cpuMetric').textContent = `${Math.round(stats.cpu_percent || 0)}%`;
            document.getElementById('memMetric').textContent = `${Math.round(stats.memory_percent || 0)}%`;
            document.getElementById('gpuMetric').textContent = stats.gpu_info || 'N/A';
        }
        
        // Добавление данных в график
        if (this.performanceChart && stats.cpu_percent !== undefined) {
            this.addPerformanceData(stats.cpu_percent, stats.memory_percent || 0);
        }
    }

    async initializeModel() {
        const btn = document.getElementById('initBtn');
        const originalText = btn.innerHTML;
        
        btn.disabled = true;
        btn.innerHTML = '<i data-lucide="loader" class="w-4 h-4 mr-2 animate-spin"></i>Инициализация...';
        lucide.createIcons();
        
        this.showLoadingModal('Инициализация Daur MedIA', 'Загрузка модели HunyuanVideo...');
        
        try {
            const response = await fetch('/api/initialize', { method: 'POST' });
            const result = await response.json();
            
            this.hideLoadingModal();
            
            if (result.success) {
                this.showNotification('Успех!', 'Daur MedIA успешно инициализирован', 'success');
                this.isInitialized = true;
                this.updateStatusIndicator(true);
            } else {
                this.showNotification('Ошибка', result.error || 'Ошибка инициализации', 'error');
            }
        } catch (error) {
            this.hideLoadingModal();
            this.showNotification('Ошибка', 'Ошибка подключения к серверу', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
            lucide.createIcons();
        }
    }

    async generateVideo(e) {
        e.preventDefault();
        
        if (!this.isInitialized) {
            this.showNotification('Ошибка', 'Сначала инициализируйте Daur MedIA', 'error');
            return;
        }
        
        const formData = new FormData(e.target);
        const data = {
            prompt: formData.get('prompt'),
            video_width: parseInt(formData.get('video_width')),
            video_height: parseInt(formData.get('video_height')),
            video_length: parseInt(formData.get('video_length')),
            infer_steps: parseInt(formData.get('infer_steps')),
            cfg_scale: parseFloat(formData.get('cfg_scale'))
        };
        
        if (formData.get('seed')) {
            data.seed = parseInt(formData.get('seed'));
        }
        
        const btn = document.getElementById('generateBtn');
        const originalText = btn.innerHTML;
        
        btn.disabled = true;
        btn.innerHTML = '<i data-lucide="loader" class="w-5 h-5 animate-spin"></i><span>Создание видео...</span>';
        lucide.createIcons();
        
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Задача создана!', 'Генерация видео началась в Daur MedIA', 'success');
                this.loadTasks();
                
                // Переключение на вкладку задач
                this.switchTab('tasks');
            } else {
                this.showNotification('Ошибка', result.error || 'Ошибка создания задачи', 'error');
            }
        } catch (error) {
            this.showNotification('Ошибка', 'Ошибка отправки запроса', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
            lucide.createIcons();
        }
    }

    async loadTasks() {
        try {
            const response = await fetch('/api/tasks');
            const result = await response.json();
            
            this.renderTasks(result.tasks || []);
            
            // Обновление счетчика задач
            const activeTasks = (result.tasks || []).filter(task => 
                task.status === 'pending' || task.status === 'processing'
            ).length;
            
            if (document.getElementById('tasksMetric')) {
                document.getElementById('tasksMetric').textContent = activeTasks;
            }
        } catch (error) {
            console.error('Ошибка загрузки задач:', error);
        }
    }

    renderTasks(tasks) {
        const tasksList = document.getElementById('tasksList');
        
        if (tasks.length === 0) {
            tasksList.innerHTML = `
                <div class="glass-effect rounded-lg p-8 text-center">
                    <i data-lucide="inbox" class="w-16 h-16 text-white text-opacity-50 mx-auto mb-4"></i>
                    <p class="text-white text-opacity-60">Пока нет задач в Daur MedIA</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }
        
        tasksList.innerHTML = tasks.map(task => `
            <div class="glass-effect rounded-lg p-6 border border-white border-opacity-20 hover:bg-white hover:bg-opacity-5 transition-all">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex-1">
                        <div class="flex items-center space-x-2 mb-2">
                            <h4 class="text-white font-medium">Задача ${task.id.substring(0, 8)}</h4>
                            <span class="text-xs text-white text-opacity-50">Daur MedIA</span>
                        </div>
                        <p class="text-white text-opacity-80 text-sm mb-3 leading-relaxed">${task.prompt}</p>
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-white text-opacity-60">
                            <span><i data-lucide="maximize" class="w-3 h-3 inline mr-1"></i>${task.video_width}x${task.video_height}</span>
                            <span><i data-lucide="clock" class="w-3 h-3 inline mr-1"></i>${task.video_length} кадров</span>
                            <span><i data-lucide="zap" class="w-3 h-3 inline mr-1"></i>${task.infer_steps} шагов</span>
                            <span><i data-lucide="calendar" class="w-3 h-3 inline mr-1"></i>${new Date(task.created_at).toLocaleString()}</span>
                        </div>
                        ${task.seed ? `<div class="mt-2 text-xs text-white text-opacity-60"><i data-lucide="shuffle" class="w-3 h-3 inline mr-1"></i>Сид: ${task.seed}</div>` : ''}
                    </div>
                    <div class="flex items-center space-x-3 ml-4">
                        <span class="px-3 py-1 rounded-full text-xs font-medium status-${task.status}">
                            ${this.getStatusText(task.status)}
                        </span>
                        ${task.status === 'completed' ? `
                            <button onclick="app.downloadVideo('${task.id}')" class="glass-effect px-3 py-2 rounded text-white text-sm hover:bg-white hover:bg-opacity-20 transition-all" title="Скачать видео">
                                <i data-lucide="download" class="w-4 h-4"></i>
                            </button>
                        ` : ''}
                        <button onclick="app.deleteTask('${task.id}')" class="glass-effect px-3 py-2 rounded text-white text-sm hover:bg-red-500 hover:bg-opacity-20 transition-all" title="Удалить задачу">
                            <i data-lucide="trash-2" class="w-4 h-4"></i>
                        </button>
                    </div>
                </div>
                ${task.status === 'processing' ? `
                    <div class="w-full bg-white bg-opacity-20 rounded-full h-2 mb-2">
                        <div class="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full animate-pulse-slow" style="width: 60%"></div>
                    </div>
                    <p class="text-white text-opacity-60 text-sm">Генерация видео в процессе...</p>
                ` : ''}
                ${task.error ? `
                    <div class="mt-3 p-3 bg-red-500 bg-opacity-20 rounded text-red-200 text-sm">
                        <i data-lucide="alert-circle" class="w-4 h-4 inline mr-2"></i>
                        ${task.error}
                    </div>
                ` : ''}
            </div>
        `).join('');
        
        lucide.createIcons();
    }

    getStatusText(status) {
        const statusMap = {
            'pending': 'Ожидание',
            'processing': 'Обработка',
            'completed': 'Завершено',
            'failed': 'Ошибка',
            'testing': 'Тестирование'
        };
        return statusMap[status] || status;
    }

    async downloadVideo(taskId) {
        try {
            const response = await fetch(`/api/download/${taskId}`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `daur_media_${taskId}.mp4`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showNotification('Успех!', 'Видео скачано', 'success');
            } else {
                this.showNotification('Ошибка', 'Не удалось скачать видео', 'error');
            }
        } catch (error) {
            this.showNotification('Ошибка', 'Ошибка скачивания видео', 'error');
        }
    }

    async runTest(testType) {
        const testResults = document.getElementById('testResults');
        
        try {
            const response = await fetch(`/api/test/${testType}`, { method: 'POST' });
            const result = await response.json();
            
            const timestamp = new Date().toLocaleTimeString();
            const resultElement = document.createElement('div');
            resultElement.className = `p-3 rounded-lg mb-2 ${result.success ? 'bg-green-500 bg-opacity-20' : 'bg-red-500 bg-opacity-20'}`;
            
            if (result.success) {
                resultElement.innerHTML = `
                    <div class="flex items-center justify-between">
                        <span><i data-lucide="check-circle" class="w-4 h-4 inline mr-2"></i>${result.test}</span>
                        <span class="text-sm opacity-75">${timestamp}</span>
                    </div>
                    <div class="text-sm mt-1 opacity-80">
                        ${result.duration ? `Время: ${result.duration}` : ''}
                        ${result.result ? `Результат: ${result.result}` : ''}
                        ${result.device ? `Устройство: ${result.device}` : ''}
                        ${result.memory ? `Память: ${result.memory}` : ''}
                        ${result.task_id ? `ID задачи: ${result.task_id}` : ''}
                    </div>
                `;
            } else {
                resultElement.innerHTML = `
                    <div class="flex items-center justify-between">
                        <span><i data-lucide="x-circle" class="w-4 h-4 inline mr-2"></i>${result.test}</span>
                        <span class="text-sm opacity-75">${timestamp}</span>
                    </div>
                    <div class="text-sm mt-1 opacity-80">Ошибка: ${result.error}</div>
                `;
            }
            
            testResults.insertBefore(resultElement, testResults.firstChild);
            lucide.createIcons();
            
            // Ограничиваем количество результатов
            while (testResults.children.length > 10) {
                testResults.removeChild(testResults.lastChild);
            }
            
        } catch (error) {
            this.showNotification('Ошибка', `Ошибка выполнения теста: ${testType}`, 'error');
        }
    }

    switchTab(tabName) {
        // Обновление кнопок навигации
        document.querySelectorAll('.tab-button').forEach(button => {
            if (button.dataset.tab === tabName) {
                button.className = 'tab-button tab-active px-6 py-3 rounded-md transition-all';
            } else {
                button.className = 'tab-button tab-inactive px-6 py-3 rounded-md transition-all';
            }
        });
        
        // Скрытие всех вкладок
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });
        
        // Показ выбранной вкладки
        const targetTab = document.getElementById(`${tabName}-tab`);
        if (targetTab) {
            targetTab.classList.remove('hidden');
        }
        
        this.currentTab = tabName;
        
        // Специальные действия для вкладок
        if (tabName === 'monitoring') {
            this.updateSystemStats({});
        }
    }

    setupAutoRefresh() {
        const interval = parseInt(localStorage.getItem('autoRefreshInterval') || '5');
        
        if (interval > 0) {
            this.autoRefreshInterval = setInterval(() => {
                this.loadTasks();
                this.checkStatus();
            }, interval * 1000);
        }
    }

    updateAutoRefresh(interval) {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
        
        localStorage.setItem('autoRefreshInterval', interval);
        
        if (interval > 0) {
            this.autoRefreshInterval = setInterval(() => {
                this.loadTasks();
                this.checkStatus();
            }, interval * 1000);
        }
    }

    initPerformanceChart() {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;
        
        this.performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU %',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Memory %',
                    data: [],
                    borderColor: 'rgb(16, 185, 129)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: {
                            color: 'white'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: 'white'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            color: 'white'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }

    addPerformanceData(cpu, memory) {
        if (!this.performanceChart) return;
        
        const now = new Date().toLocaleTimeString();
        
        this.performanceChart.data.labels.push(now);
        this.performanceChart.data.datasets[0].data.push(cpu);
        this.performanceChart.data.datasets[1].data.push(memory);
        
        // Ограничиваем количество точек
        if (this.performanceChart.data.labels.length > 20) {
            this.performanceChart.data.labels.shift();
            this.performanceChart.data.datasets[0].data.shift();
            this.performanceChart.data.datasets[1].data.shift();
        }
        
        this.performanceChart.update('none');
    }

    showNotification(title, message, type = 'success') {
        const notification = document.getElementById('notification');
        const titleElement = document.getElementById('notificationTitle');
        const textElement = document.getElementById('notificationText');
        const icon = notification.querySelector('i');
        
        titleElement.textContent = title;
        textElement.textContent = message;
        
        // Обновление иконки и цвета
        if (type === 'error') {
            icon.setAttribute('data-lucide', 'x-circle');
            notification.classList.remove('bg-green-500', 'bg-blue-500');
            notification.classList.add('bg-red-500');
        } else if (type === 'warning') {
            icon.setAttribute('data-lucide', 'alert-triangle');
            notification.classList.remove('bg-green-500', 'bg-red-500');
            notification.classList.add('bg-yellow-500');
        } else {
            icon.setAttribute('data-lucide', 'check-circle');
            notification.classList.remove('bg-red-500', 'bg-yellow-500');
            notification.classList.add('bg-green-500');
        }
        
        lucide.createIcons();
        
        // Показ уведомления
        notification.classList.remove('translate-x-full');
        
        // Скрытие через 4 секунды
        setTimeout(() => {
            notification.classList.add('translate-x-full');
        }, 4000);
    }

    showLoadingModal(title, text) {
        const modal = document.getElementById('loadingModal');
        const titleElement = document.getElementById('loadingTitle');
        const textElement = document.getElementById('loadingText');
        
        titleElement.textContent = title;
        textElement.textContent = text;
        
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    hideLoadingModal() {
        const modal = document.getElementById('loadingModal');
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    loadSettings() {
        // Загрузка сохраненных настроек
        const autoRefresh = localStorage.getItem('autoRefreshInterval') || '5';
        const maxTasks = localStorage.getItem('maxTasks') || '50';
        
        if (document.getElementById('autoRefresh')) {
            document.getElementById('autoRefresh').value = autoRefresh;
        }
        if (document.getElementById('maxTasks')) {
            document.getElementById('maxTasks').value = maxTasks;
        }
    }

    async clearCompletedTasks() {
        // Здесь можно добавить API для очистки завершенных задач
        this.showNotification('Информация', 'Функция будет добавлена в следующем обновлении', 'warning');
    }

    async exportTasks() {
        try {
            const response = await fetch('/api/tasks');
            const result = await response.json();
            
            const dataStr = JSON.stringify(result.tasks, null, 2);
            const dataBlob = new Blob([dataStr], {type: 'application/json'});
            
            const url = window.URL.createObjectURL(dataBlob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `daur_media_tasks_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.showNotification('Успех!', 'Задачи экспортированы', 'success');
        } catch (error) {
            this.showNotification('Ошибка', 'Не удалось экспортировать задачи', 'error');
        }
    }

    async clearAllTasks() {
        if (confirm('Вы уверены, что хотите удалить все задачи? Это действие нельзя отменить.')) {
            // Здесь можно добавить API для очистки всех задач
            this.showNotification('Информация', 'Функция будет добавлена в следующем обновлении', 'warning');
        }
    }

    resetSettings() {
        if (confirm('Сбросить все настройки к значениям по умолчанию?')) {
            localStorage.clear();
            location.reload();
        }
    }

    async deleteTask(taskId) {
        if (confirm('Удалить эту задачу?')) {
            // Здесь можно добавить API для удаления задачи
            this.showNotification('Информация', 'Функция будет добавлена в следующем обновлении', 'warning');
        }
    }
}

// Инициализация приложения при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    window.app = new DaurMediaApp();
});

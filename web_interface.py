#!/usr/bin/env python3
"""
Daur MedIA - AI Video Generation Platform
Локальный веб-сервер для генерации видео с помощью HunyuanVideo
"""

import os
import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, send_file
from werkzeug.utils import secure_filename
import uuid

from hunyuan_video_interface import HunyuanVideoGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'daur-media-secret-key'

# Глобальные переменные
generator = None
tasks = {}
task_lock = threading.Lock()

# HTML шаблон интерфейса
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daur MedIA - AI Video Generation Platform</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        body {
            font-family: 'Inter', sans-serif;
        }
        
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .glass-effect {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .animate-pulse-slow {
            animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        .robot-animation {
            animation: float 6s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }
        
        .status-pending { @apply bg-yellow-100 text-yellow-800; }
        .status-processing { @apply bg-blue-100 text-blue-800; }
        .status-completed { @apply bg-green-100 text-green-800; }
        .status-failed { @apply bg-red-100 text-red-800; }
    </style>
</head>
<body class="min-h-screen gradient-bg">
    <!-- Header -->
    <header class="glass-effect">
        <div class="container mx-auto px-6 py-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center robot-animation">
                        <i data-lucide="video" class="w-6 h-6 text-purple-600"></i>
                    </div>
                    <h1 class="text-2xl font-bold text-white">Daur MedIA</h1>
                    <span class="text-sm text-white opacity-75">AI Video Generation Platform</span>
                </div>
                <div class="flex items-center space-x-4">
                    <div id="statusIndicator" class="flex items-center space-x-2">
                        <div class="w-3 h-3 bg-red-500 rounded-full"></div>
                        <span class="text-white text-sm">Не инициализирован</span>
                    </div>
                    <button id="initBtn" class="glass-effect px-4 py-2 rounded-lg text-white hover:bg-white hover:bg-opacity-20 transition-all">
                        Инициализировать
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="container mx-auto px-6 py-12">
        <!-- Hero Section -->
        <div class="text-center mb-12">
            <h2 class="text-5xl font-bold text-white mb-6">
                Daur MedIA - Создавайте видео с ИИ
            </h2>
            <p class="text-xl text-white text-opacity-80 max-w-2xl mx-auto">
                Мощная платформа для генерации видео с помощью искусственного интеллекта. Локальная обработка, полный контроль, профессиональные результаты.
            </p>
        </div>

        <!-- Video Generation Form -->
        <div class="max-w-4xl mx-auto">
            <div class="glass-effect rounded-2xl p-8 mb-8">
                <form id="videoForm" class="space-y-6">
                    <div>
                        <label for="prompt" class="block text-white font-medium mb-3">
                            Описание видео
                        </label>
                        <textarea 
                            id="prompt" 
                            name="prompt" 
                            rows="4" 
                            class="w-full px-4 py-3 rounded-lg bg-white bg-opacity-10 border border-white border-opacity-20 text-white placeholder-white placeholder-opacity-60 focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50"
                            placeholder="Например: A cat walking on grass, realistic style"
                            required
                        ></textarea>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                        <div>
                            <label for="video_width" class="block text-white font-medium mb-2">
                                Ширина
                            </label>
                            <input 
                                type="number" 
                                id="video_width" 
                                name="video_width" 
                                value="1280" 
                                min="256" 
                                max="1920"
                                step="64"
                                class="w-full px-4 py-2 rounded-lg bg-white bg-opacity-10 border border-white border-opacity-20 text-white focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50"
                            >
                        </div>
                        <div>
                            <label for="video_height" class="block text-white font-medium mb-2">
                                Высота
                            </label>
                            <input 
                                type="number" 
                                id="video_height" 
                                name="video_height" 
                                value="720" 
                                min="256" 
                                max="1080"
                                step="64"
                                class="w-full px-4 py-2 rounded-lg bg-white bg-opacity-10 border border-white border-opacity-20 text-white focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50"
                            >
                        </div>
                        <div>
                            <label for="video_length" class="block text-white font-medium mb-2">
                                Длина (кадры)
                            </label>
                            <input 
                                type="number" 
                                id="video_length" 
                                name="video_length" 
                                value="129" 
                                min="65" 
                                max="257"
                                step="64"
                                class="w-full px-4 py-2 rounded-lg bg-white bg-opacity-10 border border-white border-opacity-20 text-white focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50"
                            >
                        </div>
                        <div>
                            <label for="infer_steps" class="block text-white font-medium mb-2">
                                Шаги
                            </label>
                            <input 
                                type="number" 
                                id="infer_steps" 
                                name="infer_steps" 
                                value="50" 
                                min="10" 
                                max="100"
                                class="w-full px-4 py-2 rounded-lg bg-white bg-opacity-10 border border-white border-opacity-20 text-white focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50"
                            >
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label for="seed" class="block text-white font-medium mb-2">
                                Сид (опционально)
                            </label>
                            <input 
                                type="number" 
                                id="seed" 
                                name="seed" 
                                placeholder="Случайный сид"
                                class="w-full px-4 py-2 rounded-lg bg-white bg-opacity-10 border border-white border-opacity-20 text-white placeholder-white placeholder-opacity-60 focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50"
                            >
                        </div>
                        <div>
                            <label for="cfg_scale" class="block text-white font-medium mb-2">
                                CFG Scale
                            </label>
                            <input 
                                type="number" 
                                id="cfg_scale" 
                                name="cfg_scale" 
                                value="6.0" 
                                min="1.0" 
                                max="20.0"
                                step="0.1"
                                class="w-full px-4 py-2 rounded-lg bg-white bg-opacity-10 border border-white border-opacity-20 text-white focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50"
                            >
                        </div>
                    </div>

                    <button 
                        type="submit" 
                        id="generateBtn"
                        class="w-full bg-white bg-opacity-20 hover:bg-opacity-30 text-white font-semibold py-4 px-8 rounded-lg transition-all duration-300 flex items-center justify-center space-x-3 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <i data-lucide="play" class="w-5 h-5"></i>
                        <span>Создать видео</span>
                    </button>
                </form>
            </div>

            <!-- Tasks List -->
            <div class="glass-effect rounded-2xl p-8">
                <div class="flex items-center justify-between mb-6">
                    <h3 class="text-2xl font-bold text-white">Задачи генерации</h3>
                    <button 
                        id="refreshBtn"
                        class="glass-effect px-4 py-2 rounded-lg text-white hover:bg-white hover:bg-opacity-20 transition-all"
                    >
                        <i data-lucide="refresh-cw" class="w-5 h-5"></i>
                    </button>
                </div>
                <div id="tasksList" class="space-y-4">
                    <p class="text-white text-opacity-60 text-center py-8">Пока нет задач</p>
                </div>
            </div>
        </div>
    </main>

    <!-- Notification -->
    <div id="notification" class="fixed top-4 right-4 glass-effect rounded-lg p-4 text-white transform translate-x-full transition-transform duration-300 z-50">
        <div class="flex items-center space-x-3">
            <i data-lucide="check-circle" class="w-5 h-5"></i>
            <span id="notificationText"></span>
        </div>
    </div>

    <script>
        // Инициализация Lucide иконок
        lucide.createIcons();
        
        let isInitialized = false;
        
        // Проверка статуса при загрузке
        checkStatus();
        
        // Обработчики событий
        document.getElementById('initBtn').addEventListener('click', initializeModel);
        document.getElementById('videoForm').addEventListener('submit', generateVideo);
        document.getElementById('refreshBtn').addEventListener('click', loadTasks);
        
        // Автообновление задач
        setInterval(loadTasks, 5000);
        
        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                updateStatusIndicator(status.initialized);
                isInitialized = status.initialized;
            } catch (error) {
                console.error('Ошибка проверки статуса:', error);
            }
        }
        
        function updateStatusIndicator(initialized) {
            const indicator = document.getElementById('statusIndicator');
            const dot = indicator.querySelector('div');
            const text = indicator.querySelector('span');
            
            if (initialized) {
                dot.className = 'w-3 h-3 bg-green-500 rounded-full';
                text.textContent = 'Готов к работе';
                document.getElementById('generateBtn').disabled = false;
            } else {
                dot.className = 'w-3 h-3 bg-red-500 rounded-full';
                text.textContent = 'Не инициализирован';
                document.getElementById('generateBtn').disabled = true;
            }
        }
        
        async function initializeModel() {
            const btn = document.getElementById('initBtn');
            btn.disabled = true;
            btn.textContent = 'Инициализация...';
            
            try {
                const response = await fetch('/api/initialize', { method: 'POST' });
                const result = await response.json();
                
                if (result.success) {
                    showNotification('Модель успешно инициализирована!', 'success');
                    isInitialized = true;
                    updateStatusIndicator(true);
                } else {
                    showNotification(result.error || 'Ошибка инициализации', 'error');
                }
            } catch (error) {
                showNotification('Ошибка инициализации', 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = 'Инициализировать';
            }
        }
        
        async function generateVideo(e) {
            e.preventDefault();
            
            if (!isInitialized) {
                showNotification('Сначала инициализируйте модель', 'error');
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
            btn.disabled = true;
            btn.innerHTML = '<i data-lucide="loader" class="w-5 h-5 animate-spin"></i><span>Создание...</span>';
            lucide.createIcons();
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showNotification('Задача создана! Генерация началась...', 'success');
                    loadTasks();
                } else {
                    showNotification(result.error || 'Ошибка создания задачи', 'error');
                }
            } catch (error) {
                showNotification('Ошибка отправки запроса', 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i data-lucide="play" class="w-5 h-5"></i><span>Создать видео</span>';
                lucide.createIcons();
            }
        }
        
        async function loadTasks() {
            try {
                const response = await fetch('/api/tasks');
                const result = await response.json();
                renderTasks(result.tasks || []);
            } catch (error) {
                console.error('Ошибка загрузки задач:', error);
            }
        }
        
        function renderTasks(tasks) {
            const tasksList = document.getElementById('tasksList');
            
            if (tasks.length === 0) {
                tasksList.innerHTML = '<p class="text-white text-opacity-60 text-center py-8">Пока нет задач</p>';
                return;
            }
            
            tasksList.innerHTML = tasks.map(task => `
                <div class="bg-white bg-opacity-10 rounded-lg p-6 border border-white border-opacity-20">
                    <div class="flex items-start justify-between mb-4">
                        <div class="flex-1">
                            <h4 class="text-white font-medium mb-2">Задача ${task.id}</h4>
                            <p class="text-white text-opacity-80 text-sm mb-3">${task.prompt}</p>
                            <div class="flex items-center space-x-4 text-sm text-white text-opacity-60">
                                <span>${task.video_width}x${task.video_height}</span>
                                <span>${task.video_length} кадров</span>
                                <span>${task.infer_steps} шагов</span>
                                ${task.seed ? `<span>Сид: ${task.seed}</span>` : ''}
                            </div>
                        </div>
                        <div class="flex items-center space-x-3">
                            <span class="px-3 py-1 rounded-full text-xs font-medium status-${task.status}">
                                ${getStatusText(task.status)}
                            </span>
                            ${task.status === 'completed' ? `
                                <button onclick="downloadVideo('${task.id}')" class="glass-effect px-3 py-1 rounded text-white text-sm hover:bg-white hover:bg-opacity-20 transition-all">
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
                    ${task.error ? `
                        <div class="mt-3 p-3 bg-red-500 bg-opacity-20 rounded text-red-200 text-sm">
                            ${task.error}
                        </div>
                    ` : ''}
                </div>
            `).join('');
            
            lucide.createIcons();
        }
        
        function getStatusText(status) {
            const statusMap = {
                'pending': 'Ожидание',
                'processing': 'Обработка',
                'completed': 'Завершено',
                'failed': 'Ошибка'
            };
            return statusMap[status] || status;
        }
        
        async function downloadVideo(taskId) {
            try {
                const response = await fetch(`/api/download/${taskId}`);
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
                    showNotification('Ошибка скачивания видео', 'error');
                }
            } catch (error) {
                showNotification('Ошибка скачивания видео', 'error');
            }
        }
        
        function showNotification(message, type = 'success') {
            const notification = document.getElementById('notification');
            const text = document.getElementById('notificationText');
            const icon = notification.querySelector('i');
            
            text.textContent = message;
            
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
            notification.classList.remove('translate-x-full');
            
            setTimeout(() => {
                notification.classList.add('translate-x-full');
            }, 3000);
        }
    </script>
</body>
</html>
"""

def process_video_task(task_id, task_data):
    """Обработка задачи генерации видео в отдельном потоке"""
    global generator, tasks
    
    with task_lock:
        if task_id not in tasks:
            return
        tasks[task_id]['status'] = 'processing'
        tasks[task_id]['started_at'] = datetime.now().isoformat()
    
    try:
        # Генерация видео
        result = generator.generate_video(
            prompt=task_data['prompt'],
            video_size=(task_data['video_height'], task_data['video_width']),
            video_length=task_data['video_length'],
            infer_steps=task_data['infer_steps'],
            seed=task_data.get('seed'),
            embedded_cfg_scale=task_data.get('cfg_scale', 6.0),
            save_path="./generated_videos",
            filename=f"video_{task_id}.mp4"
        )
        
        with task_lock:
            if result['success']:
                tasks[task_id]['status'] = 'completed'
                tasks[task_id]['output_path'] = result['output_path']
                tasks[task_id]['seed'] = result['seed']
            else:
                tasks[task_id]['status'] = 'failed'
                tasks[task_id]['error'] = result['error']
            
            tasks[task_id]['completed_at'] = datetime.now().isoformat()
    
    except Exception as e:
        with task_lock:
            tasks[task_id]['status'] = 'failed'
            tasks[task_id]['error'] = str(e)
            tasks[task_id]['completed_at'] = datetime.now().isoformat()

@app.route('/')
def index():
    """Главная страница"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def get_status():
    """Получение статуса модели"""
    global generator
    
    if generator is None:
        generator = HunyuanVideoGenerator()
    
    info = generator.get_model_info()
    return jsonify(info)

@app.route('/api/initialize', methods=['POST'])
def initialize_model():
    """Инициализация модели"""
    global generator
    
    try:
        if generator is None:
            generator = HunyuanVideoGenerator()
        
        success = generator.initialize()
        
        return jsonify({
            'success': success,
            'message': 'Модель инициализирована' if success else 'Ошибка инициализации'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate', methods=['POST'])
def generate_video():
    """Создание задачи генерации видео"""
    global generator, tasks
    
    if generator is None or not generator.initialized:
        return jsonify({
            'success': False,
            'error': 'Модель не инициализирована'
        }), 400
    
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({
                'success': False,
                'error': 'Требуется поле prompt'
            }), 400
        
        # Создание уникального ID задачи
        task_id = str(uuid.uuid4())
        
        # Сохранение задачи
        task_data = {
            'id': task_id,
            'prompt': data['prompt'],
            'video_width': data.get('video_width', 1280),
            'video_height': data.get('video_height', 720),
            'video_length': data.get('video_length', 129),
            'infer_steps': data.get('infer_steps', 50),
            'cfg_scale': data.get('cfg_scale', 6.0),
            'seed': data.get('seed'),
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        with task_lock:
            tasks[task_id] = task_data
        
        # Запуск обработки в отдельном потоке
        thread = threading.Thread(target=process_video_task, args=(task_id, task_data))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Задача создана и поставлена в очередь'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tasks')
def get_tasks():
    """Получение списка задач"""
    global tasks
    
    with task_lock:
        task_list = list(tasks.values())
    
    # Сортировка по времени создания (новые сначала)
    task_list.sort(key=lambda x: x['created_at'], reverse=True)
    
    return jsonify({
        'tasks': task_list
    })

@app.route('/api/download/<task_id>')
def download_video(task_id):
    """Скачивание сгенерированного видео"""
    global tasks
    
    with task_lock:
        if task_id not in tasks:
            return jsonify({'error': 'Задача не найдена'}), 404
        
        task = tasks[task_id]
    
    if task['status'] != 'completed':
        return jsonify({'error': 'Видео еще не готово'}), 400
    
    if 'output_path' not in task or not os.path.exists(task['output_path']):
        return jsonify({'error': 'Файл не найден'}), 404
    
    return send_file(
        task['output_path'],
        as_attachment=True,
        download_name=f"video_{task_id}.mp4"
    )

if __name__ == '__main__':
    # Создание директории для результатов
    os.makedirs('./generated_videos', exist_ok=True)
    
    print("🚀 Запуск Daur MedIA HunyuanVideo Generator")
    print("📱 Откройте http://localhost:5000 в браузере")
    print("⚠️  Убедитесь, что у вас установлены все зависимости HunyuanVideo")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

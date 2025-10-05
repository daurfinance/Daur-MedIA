#!/usr/bin/env python3
"""
Daur MedIA - AI Video Generation Platform
Улучшенный веб-интерфейс с функциями тестирования и мониторинга
"""

import os
import json
import threading
import time
import uuid
import psutil
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Условный импорт для демонстрации
try:
    from hunyuan_video_interface import HunyuanVideoGenerator
except ImportError:
    # Заглушка для демонстрации без установленных зависимостей
    class HunyuanVideoGenerator:
        def __init__(self):
            self.initialized = False
        
        def initialize(self):
            return True
        
        def get_model_info(self):
            return {
                'initialized': False,
                'model_name': 'HunyuanVideo (Demo Mode)',
                'device': 'CPU',
                'memory_usage': 0
            }
        
        def generate_video(self, **kwargs):
            import time
            time.sleep(2)  # Имитация обработки
            return {
                'success': True,
                'output_path': './demo_video.mp4',
                'seed': kwargs.get('seed', 12345)
            }

app = Flask(__name__)
app.config['SECRET_KEY'] = 'daur-media-secret-key-2025'

# Глобальные переменные
generator = None
tasks = {}
task_lock = threading.Lock()
system_stats = {}

# HTML шаблон улучшенного интерфейса
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daur MedIA - AI Video Generation Platform</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
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
        
        .glass-dark {
            background: rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .animate-pulse-slow {
            animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        .robot-animation {
            animation: float 6s ease-in-out infinite;
        }
        
        .glow-effect {
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }
        
        .status-pending { @apply bg-yellow-100 text-yellow-800; }
        .status-processing { @apply bg-blue-100 text-blue-800; }
        .status-completed { @apply bg-green-100 text-green-800; }
        .status-failed { @apply bg-red-100 text-red-800; }
        
        .tab-active { @apply bg-white bg-opacity-20 text-white; }
        .tab-inactive { @apply bg-transparent text-white text-opacity-70 hover:text-white hover:bg-white hover:bg-opacity-10; }
        
        .metric-card {
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        }
    </style>
</head>
<body class="min-h-screen gradient-bg">
    <!-- Header -->
    <header class="glass-effect sticky top-0 z-50">
        <div class="container mx-auto px-6 py-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4">
                    <div class="w-12 h-12 bg-white rounded-xl flex items-center justify-center robot-animation glow-effect">
                        <i data-lucide="video" class="w-7 h-7 text-purple-600"></i>
                    </div>
                    <div>
                        <h1 class="text-3xl font-bold text-white">Daur MedIA</h1>
                        <p class="text-sm text-white opacity-75">AI Video Generation Platform</p>
                    </div>
                </div>
                <div class="flex items-center space-x-4">
                    <div id="systemStats" class="hidden md:flex items-center space-x-4 text-white text-sm">
                        <div class="flex items-center space-x-1">
                            <i data-lucide="cpu" class="w-4 h-4"></i>
                            <span id="cpuUsage">0%</span>
                        </div>
                        <div class="flex items-center space-x-1">
                            <i data-lucide="hard-drive" class="w-4 h-4"></i>
                            <span id="memUsage">0%</span>
                        </div>
                        <div class="flex items-center space-x-1">
                            <i data-lucide="zap" class="w-4 h-4"></i>
                            <span id="gpuStatus">N/A</span>
                        </div>
                    </div>
                    <div id="statusIndicator" class="flex items-center space-x-2">
                        <div class="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                        <span class="text-white text-sm">Не инициализирован</span>
                    </div>
                    <button id="initBtn" class="glass-effect px-4 py-2 rounded-lg text-white hover:bg-white hover:bg-opacity-20 transition-all">
                        <i data-lucide="power" class="w-4 h-4 mr-2"></i>
                        Инициализировать
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- Navigation Tabs -->
    <nav class="container mx-auto px-6 py-4">
        <div class="flex space-x-1 glass-effect rounded-lg p-1">
            <button class="tab-button tab-active px-6 py-3 rounded-md transition-all" data-tab="generation">
                <i data-lucide="video" class="w-4 h-4 mr-2"></i>
                Генерация видео
            </button>
            <button class="tab-button tab-inactive px-6 py-3 rounded-md transition-all" data-tab="tasks">
                <i data-lucide="list" class="w-4 h-4 mr-2"></i>
                Мои задачи
            </button>
            <button class="tab-button tab-inactive px-6 py-3 rounded-md transition-all" data-tab="testing">
                <i data-lucide="flask" class="w-4 h-4 mr-2"></i>
                Тестирование
            </button>
            <button class="tab-button tab-inactive px-6 py-3 rounded-md transition-all" data-tab="monitoring">
                <i data-lucide="activity" class="w-4 h-4 mr-2"></i>
                Мониторинг
            </button>
            <button class="tab-button tab-inactive px-6 py-3 rounded-md transition-all" data-tab="settings">
                <i data-lucide="settings" class="w-4 h-4 mr-2"></i>
                Настройки
            </button>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="container mx-auto px-6 pb-12">
        <!-- Generation Tab -->
        <div id="generation-tab" class="tab-content">
            <!-- Hero Section -->
            <div class="text-center mb-12">
                <h2 class="text-5xl font-bold text-white mb-6">
                    Создавайте потрясающие видео с ИИ
                </h2>
                <p class="text-xl text-white text-opacity-80 max-w-3xl mx-auto">
                    Daur MedIA использует передовые технологии искусственного интеллекта для создания высококачественных видео по вашим текстовым описаниям. Полный контроль, локальная обработка, профессиональные результаты.
                </p>
            </div>

            <!-- Quick Start Templates -->
            <div class="mb-8">
                <h3 class="text-2xl font-bold text-white mb-4">🚀 Быстрый старт</h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <button class="template-btn glass-effect p-4 rounded-lg text-left hover:bg-white hover:bg-opacity-20 transition-all" 
                            data-prompt="A majestic eagle soaring through mountain peaks, cinematic style">
                        <h4 class="text-white font-medium mb-2">🦅 Природа</h4>
                        <p class="text-white text-opacity-70 text-sm">Орел в горах</p>
                    </button>
                    <button class="template-btn glass-effect p-4 rounded-lg text-left hover:bg-white hover:bg-opacity-20 transition-all"
                            data-prompt="Futuristic city skyline at night with neon lights, cyberpunk style">
                        <h4 class="text-white font-medium mb-2">🌃 Киберпанк</h4>
                        <p class="text-white text-opacity-70 text-sm">Футуристический город</p>
                    </button>
                    <button class="template-btn glass-effect p-4 rounded-lg text-left hover:bg-white hover:bg-opacity-20 transition-all"
                            data-prompt="Time-lapse of a flower blooming in spring garden, macro photography">
                        <h4 class="text-white font-medium mb-2">🌸 Таймлапс</h4>
                        <p class="text-white text-opacity-70 text-sm">Цветение цветка</p>
                    </button>
                </div>
            </div>

            <!-- Video Generation Form -->
            <div class="glass-effect rounded-2xl p-8 mb-8">
                <form id="videoForm" class="space-y-6">
                    <div>
                        <label for="prompt" class="block text-white font-medium mb-3">
                            <i data-lucide="edit-3" class="w-4 h-4 inline mr-2"></i>
                            Описание видео
                        </label>
                        <textarea 
                            id="prompt" 
                            name="prompt" 
                            rows="4" 
                            class="w-full px-4 py-3 rounded-lg bg-white bg-opacity-10 border border-white border-opacity-20 text-white placeholder-white placeholder-opacity-60 focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50 resize-none"
                            placeholder="Опишите видео, которое хотите создать... (на английском языке для лучших результатов)"
                            required
                        ></textarea>
                        <div class="mt-2 text-white text-opacity-60 text-sm">
                            💡 Совет: Используйте детальные описания с указанием стиля (cinematic, artistic, realistic)
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <div>
                            <label for="video_width" class="block text-white font-medium mb-2">
                                <i data-lucide="maximize" class="w-4 h-4 inline mr-2"></i>
                                Ширина
                            </label>
                            <select id="video_width" name="video_width" class="w-full px-4 py-2 rounded-lg bg-white bg-opacity-10 border border-white border-opacity-20 text-white focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50">
                                <option value="1280">1280px (HD)</option>
                                <option value="1920">1920px (Full HD)</option>
                                <option value="720">720px (SD)</option>
                            </select>
                        </div>
                        <div>
                            <label for="video_height" class="block text-white font-medium mb-2">
                                <i data-lucide="minimize" class="w-4 h-4 inline mr-2"></i>
                                Высота
                            </label>
                            <select id="video_height" name="video_height" class="w-full px-4 py-2 rounded-lg bg-white bg-opacity-10 border border-white border-opacity-20 text-white focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50">
                                <option value="720">720px (16:9)</option>
                                <option value="1080">1080px (16:9)</option>
                                <option value="1280">1280px (1:1)</option>
                                <option value="1920">1920px (9:16)</option>
                            </select>
                        </div>
                        <div>
                            <label for="video_length" class="block text-white font-medium mb-2">
                                <i data-lucide="clock" class="w-4 h-4 inline mr-2"></i>
                                Длительность
                            </label>
                            <select id="video_length" name="video_length" class="w-full px-4 py-2 rounded-lg bg-white bg-opacity-10 border border-white border-opacity-20 text-white focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50">
                                <option value="65">2.7 сек (65 кадров)</option>
                                <option value="129">5.4 сек (129 кадров)</option>
                                <option value="193">8.0 сек (193 кадров)</option>
                                <option value="257">10.7 сек (257 кадров)</option>
                            </select>
                        </div>
                        <div>
                            <label for="infer_steps" class="block text-white font-medium mb-2">
                                <i data-lucide="zap" class="w-4 h-4 inline mr-2"></i>
                                Качество
                            </label>
                            <select id="infer_steps" name="infer_steps" class="w-full px-4 py-2 rounded-lg bg-white bg-opacity-10 border border-white border-opacity-20 text-white focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50">
                                <option value="20">Быстро (20 шагов)</option>
                                <option value="30">Средне (30 шагов)</option>
                                <option value="50">Высокое (50 шагов)</option>
                                <option value="80">Максимум (80 шагов)</option>
                            </select>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label for="seed" class="block text-white font-medium mb-2">
                                <i data-lucide="shuffle" class="w-4 h-4 inline mr-2"></i>
                                Сид (для воспроизводимости)
                            </label>
                            <div class="flex space-x-2">
                                <input 
                                    type="number" 
                                    id="seed" 
                                    name="seed" 
                                    placeholder="Оставьте пустым для случайного"
                                    class="flex-1 px-4 py-2 rounded-lg bg-white bg-opacity-10 border border-white border-opacity-20 text-white placeholder-white placeholder-opacity-60 focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50"
                                >
                                <button type="button" id="randomSeed" class="px-4 py-2 glass-effect rounded-lg text-white hover:bg-white hover:bg-opacity-20 transition-all">
                                    <i data-lucide="dice-6" class="w-4 h-4"></i>
                                </button>
                            </div>
                        </div>
                        <div>
                            <label for="cfg_scale" class="block text-white font-medium mb-2">
                                <i data-lucide="sliders" class="w-4 h-4 inline mr-2"></i>
                                CFG Scale (точность следования промпту)
                            </label>
                            <input 
                                type="range" 
                                id="cfg_scale" 
                                name="cfg_scale" 
                                min="1" 
                                max="20" 
                                step="0.5" 
                                value="6.0"
                                class="w-full"
                            >
                            <div class="flex justify-between text-white text-opacity-60 text-sm mt-1">
                                <span>Свободно (1)</span>
                                <span id="cfgValue">6.0</span>
                                <span>Точно (20)</span>
                            </div>
                        </div>
                    </div>

                    <button 
                        type="submit" 
                        id="generateBtn"
                        class="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold py-4 px-8 rounded-lg transition-all duration-300 flex items-center justify-center space-x-3 disabled:opacity-50 disabled:cursor-not-allowed glow-effect"
                    >
                        <i data-lucide="play" class="w-5 h-5"></i>
                        <span>Создать видео</span>
                    </button>
                </form>
            </div>
        </div>

        <!-- Tasks Tab -->
        <div id="tasks-tab" class="tab-content hidden">
            <div class="flex items-center justify-between mb-6">
                <h3 class="text-3xl font-bold text-white">Мои задачи</h3>
                <div class="flex space-x-2">
                    <button id="refreshBtn" class="glass-effect px-4 py-2 rounded-lg text-white hover:bg-white hover:bg-opacity-20 transition-all">
                        <i data-lucide="refresh-cw" class="w-4 h-4 mr-2"></i>
                        Обновить
                    </button>
                    <button id="clearCompletedBtn" class="glass-effect px-4 py-2 rounded-lg text-white hover:bg-white hover:bg-opacity-20 transition-all">
                        <i data-lucide="trash-2" class="w-4 h-4 mr-2"></i>
                        Очистить завершенные
                    </button>
                </div>
            </div>
            <div id="tasksList" class="space-y-4">
                <div class="glass-effect rounded-lg p-8 text-center">
                    <i data-lucide="inbox" class="w-16 h-16 text-white text-opacity-50 mx-auto mb-4"></i>
                    <p class="text-white text-opacity-60">Пока нет задач</p>
                </div>
            </div>
        </div>

        <!-- Testing Tab -->
        <div id="testing-tab" class="tab-content hidden">
            <h3 class="text-3xl font-bold text-white mb-6">Тестирование системы</h3>
            
            <!-- System Tests -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <div class="glass-effect rounded-lg p-6">
                    <h4 class="text-xl font-bold text-white mb-4">
                        <i data-lucide="cpu" class="w-5 h-5 inline mr-2"></i>
                        Тест производительности
                    </h4>
                    <div class="space-y-4">
                        <button id="testCPU" class="w-full glass-dark px-4 py-3 rounded-lg text-white hover:bg-white hover:bg-opacity-10 transition-all">
                            <i data-lucide="zap" class="w-4 h-4 mr-2"></i>
                            Тест CPU
                        </button>
                        <button id="testMemory" class="w-full glass-dark px-4 py-3 rounded-lg text-white hover:bg-white hover:bg-opacity-10 transition-all">
                            <i data-lucide="hard-drive" class="w-4 h-4 mr-2"></i>
                            Тест памяти
                        </button>
                        <button id="testGPU" class="w-full glass-dark px-4 py-3 rounded-lg text-white hover:bg-white hover:bg-opacity-10 transition-all">
                            <i data-lucide="monitor" class="w-4 h-4 mr-2"></i>
                            Тест GPU
                        </button>
                    </div>
                </div>
                
                <div class="glass-effect rounded-lg p-6">
                    <h4 class="text-xl font-bold text-white mb-4">
                        <i data-lucide="flask" class="w-5 h-5 inline mr-2"></i>
                        Тест модели
                    </h4>
                    <div class="space-y-4">
                        <button id="testQuickGeneration" class="w-full glass-dark px-4 py-3 rounded-lg text-white hover:bg-white hover:bg-opacity-10 transition-all">
                            <i data-lucide="play" class="w-4 h-4 mr-2"></i>
                            Быстрая генерация (тест)
                        </button>
                        <button id="testBatchGeneration" class="w-full glass-dark px-4 py-3 rounded-lg text-white hover:bg-white hover:bg-opacity-10 transition-all">
                            <i data-lucide="layers" class="w-4 h-4 mr-2"></i>
                            Пакетная генерация (тест)
                        </button>
                        <button id="testModelLoad" class="w-full glass-dark px-4 py-3 rounded-lg text-white hover:bg-white hover:bg-opacity-10 transition-all">
                            <i data-lucide="download" class="w-4 h-4 mr-2"></i>
                            Тест загрузки модели
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Test Results -->
            <div class="glass-effect rounded-lg p-6">
                <h4 class="text-xl font-bold text-white mb-4">
                    <i data-lucide="clipboard-list" class="w-5 h-5 inline mr-2"></i>
                    Результаты тестов
                </h4>
                <div id="testResults" class="space-y-2 text-white text-opacity-80">
                    <p>Запустите тесты для просмотра результатов</p>
                </div>
            </div>
        </div>

        <!-- Monitoring Tab -->
        <div id="monitoring-tab" class="tab-content hidden">
            <h3 class="text-3xl font-bold text-white mb-6">Мониторинг системы</h3>
            
            <!-- System Metrics -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div class="glass-effect rounded-lg p-6 metric-card">
                    <div class="flex items-center justify-between mb-4">
                        <h4 class="text-white font-medium">CPU</h4>
                        <i data-lucide="cpu" class="w-5 h-5 text-blue-400"></i>
                    </div>
                    <div class="text-2xl font-bold text-white" id="cpuMetric">0%</div>
                    <div class="text-white text-opacity-60 text-sm">Использование</div>
                </div>
                
                <div class="glass-effect rounded-lg p-6 metric-card">
                    <div class="flex items-center justify-between mb-4">
                        <h4 class="text-white font-medium">Память</h4>
                        <i data-lucide="hard-drive" class="w-5 h-5 text-green-400"></i>
                    </div>
                    <div class="text-2xl font-bold text-white" id="memMetric">0%</div>
                    <div class="text-white text-opacity-60 text-sm">Использование</div>
                </div>
                
                <div class="glass-effect rounded-lg p-6 metric-card">
                    <div class="flex items-center justify-between mb-4">
                        <h4 class="text-white font-medium">GPU</h4>
                        <i data-lucide="zap" class="w-5 h-5 text-yellow-400"></i>
                    </div>
                    <div class="text-2xl font-bold text-white" id="gpuMetric">N/A</div>
                    <div class="text-white text-opacity-60 text-sm">Статус</div>
                </div>
                
                <div class="glass-effect rounded-lg p-6 metric-card">
                    <div class="flex items-center justify-between mb-4">
                        <h4 class="text-white font-medium">Задачи</h4>
                        <i data-lucide="list" class="w-5 h-5 text-purple-400"></i>
                    </div>
                    <div class="text-2xl font-bold text-white" id="tasksMetric">0</div>
                    <div class="text-white text-opacity-60 text-sm">Активных</div>
                </div>
            </div>
            
            <!-- Performance Chart -->
            <div class="glass-effect rounded-lg p-6">
                <h4 class="text-xl font-bold text-white mb-4">
                    <i data-lucide="trending-up" class="w-5 h-5 inline mr-2"></i>
                    График производительности
                </h4>
                <canvas id="performanceChart" width="400" height="200"></canvas>
            </div>
        </div>

        <!-- Settings Tab -->
        <div id="settings-tab" class="tab-content hidden">
            <h3 class="text-3xl font-bold text-white mb-6">Настройки</h3>
            
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="glass-effect rounded-lg p-6">
                    <h4 class="text-xl font-bold text-white mb-4">
                        <i data-lucide="settings" class="w-5 h-5 inline mr-2"></i>
                        Общие настройки
                    </h4>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-white font-medium mb-2">Автообновление задач</label>
                            <select id="autoRefresh" class="w-full px-4 py-2 rounded-lg bg-white bg-opacity-10 border border-white border-opacity-20 text-white">
                                <option value="5">Каждые 5 секунд</option>
                                <option value="10">Каждые 10 секунд</option>
                                <option value="30">Каждые 30 секунд</option>
                                <option value="0">Отключено</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-white font-medium mb-2">Максимум задач в истории</label>
                            <input type="number" id="maxTasks" value="50" min="10" max="1000" 
                                   class="w-full px-4 py-2 rounded-lg bg-white bg-opacity-10 border border-white border-opacity-20 text-white">
                        </div>
                    </div>
                </div>
                
                <div class="glass-effect rounded-lg p-6">
                    <h4 class="text-xl font-bold text-white mb-4">
                        <i data-lucide="download" class="w-5 h-5 inline mr-2"></i>
                        Управление данными
                    </h4>
                    <div class="space-y-4">
                        <button id="exportTasks" class="w-full glass-dark px-4 py-3 rounded-lg text-white hover:bg-white hover:bg-opacity-10 transition-all">
                            <i data-lucide="download" class="w-4 h-4 mr-2"></i>
                            Экспорт задач
                        </button>
                        <button id="clearAllTasks" class="w-full glass-dark px-4 py-3 rounded-lg text-white hover:bg-white hover:bg-opacity-10 transition-all">
                            <i data-lucide="trash-2" class="w-4 h-4 mr-2"></i>
                            Очистить все задачи
                        </button>
                        <button id="resetSettings" class="w-full glass-dark px-4 py-3 rounded-lg text-white hover:bg-white hover:bg-opacity-10 transition-all">
                            <i data-lucide="refresh-ccw" class="w-4 h-4 mr-2"></i>
                            Сбросить настройки
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <!-- Notification -->
    <div id="notification" class="fixed top-4 right-4 glass-effect rounded-lg p-4 text-white transform translate-x-full transition-transform duration-300 z-50 max-w-sm">
        <div class="flex items-start space-x-3">
            <i data-lucide="check-circle" class="w-5 h-5 mt-0.5 flex-shrink-0"></i>
            <div>
                <div id="notificationTitle" class="font-medium"></div>
                <div id="notificationText" class="text-sm text-white text-opacity-80"></div>
            </div>
        </div>
    </div>

    <!-- Loading Modal -->
    <div id="loadingModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50">
        <div class="glass-effect rounded-2xl p-8 max-w-md w-full mx-4 text-center">
            <div class="animate-spin w-12 h-12 border-4 border-white border-opacity-20 border-t-white rounded-full mx-auto mb-4"></div>
            <h3 class="text-xl font-bold text-white mb-2" id="loadingTitle">Загрузка...</h3>
            <p class="text-white text-opacity-80" id="loadingText">Пожалуйста, подождите</p>
        </div>
    </div>

    <script>
        // Встроенный JavaScript для демонстрации
        document.addEventListener('DOMContentLoaded', function() {
            // Инициализация Lucide иконок
            lucide.createIcons();
            
            // Обработка переключения вкладок
            document.querySelectorAll('.tab-button').forEach(button => {
                button.addEventListener('click', function() {
                    const tabName = this.dataset.tab;
                    
                    // Обновление кнопок
                    document.querySelectorAll('.tab-button').forEach(btn => {
                        btn.className = 'tab-button tab-inactive px-6 py-3 rounded-md transition-all';
                    });
                    this.className = 'tab-button tab-active px-6 py-3 rounded-md transition-all';
                    
                    // Скрытие всех вкладок
                    document.querySelectorAll('.tab-content').forEach(content => {
                        content.classList.add('hidden');
                    });
                    
                    // Показ выбранной вкладки
                    const targetTab = document.getElementById(tabName + '-tab');
                    if (targetTab) {
                        targetTab.classList.remove('hidden');
                    }
                });
            });
            
            // Обработка инициализации
            document.getElementById('initBtn').addEventListener('click', async function() {
                const btn = this;
                const originalText = btn.innerHTML;
                
                btn.disabled = true;
                btn.innerHTML = '<i data-lucide="loader" class="w-4 h-4 mr-2 animate-spin"></i>Инициализация...';
                lucide.createIcons();
                
                try {
                    const response = await fetch('/api/initialize', { method: 'POST' });
                    const result = await response.json();
                    
                    if (result.success) {
                        showNotification('Успех!', 'Daur MedIA инициализирован', 'success');
                        updateStatusIndicator(true);
                    } else {
                        showNotification('Ошибка', result.error || 'Ошибка инициализации', 'error');
                    }
                } catch (error) {
                    showNotification('Ошибка', 'Ошибка подключения', 'error');
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                    lucide.createIcons();
                }
            });
            
            // Функция показа уведомлений
            function showNotification(title, message, type = 'success') {
                const notification = document.getElementById('notification');
                const titleElement = document.getElementById('notificationTitle');
                const textElement = document.getElementById('notificationText');
                
                titleElement.textContent = title;
                textElement.textContent = message;
                
                notification.classList.remove('translate-x-full');
                setTimeout(() => {
                    notification.classList.add('translate-x-full');
                }, 4000);
            }
            
            // Функция обновления статуса
            function updateStatusIndicator(initialized) {
                const indicator = document.getElementById('statusIndicator');
                const dot = indicator.querySelector('div');
                const text = indicator.querySelector('span');
                
                if (initialized) {
                    dot.className = 'w-3 h-3 bg-green-500 rounded-full';
                    text.textContent = 'Daur MedIA готов';
                } else {
                    dot.className = 'w-3 h-3 bg-red-500 rounded-full animate-pulse';
                    text.textContent = 'Не инициализирован';
                }
            }
            
            // Проверка статуса при загрузке
            checkStatus();
            
            async function checkStatus() {
                try {
                    const response = await fetch('/api/status');
                    const status = await response.json();
                    updateStatusIndicator(status.initialized);
                } catch (error) {
                    console.error('Ошибка проверки статуса:', error);
                }
            }
        });
    </script>
</body>
</html>
"""

def update_system_stats():
    """Обновление системной статистики"""
    global system_stats
    
    try:
        # CPU и память
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # GPU информация (если доступна)
        gpu_info = "N/A"
        try:
            import torch
            if torch.cuda.is_available():
                gpu_info = f"CUDA {torch.cuda.get_device_name(0)}"
        except:
            pass
        
        system_stats = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used': memory.used // (1024**3),  # GB
            'memory_total': memory.total // (1024**3),  # GB
            'gpu_info': gpu_info,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Ошибка обновления статистики: {e}")

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
            filename=f"daur_media_{task_id}.mp4"
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
    """Получение статуса модели и системы"""
    global generator
    
    if generator is None:
        generator = HunyuanVideoGenerator()
    
    info = generator.get_model_info()
    
    # Добавляем системную статистику
    update_system_stats()
    info.update(system_stats)
    
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
            'message': 'Модель Daur MedIA инициализирована' if success else 'Ошибка инициализации'
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
            'error': 'Модель Daur MedIA не инициализирована'
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
            'created_at': datetime.now().isoformat(),
            'platform': 'Daur MedIA'
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
            'message': 'Задача создана в Daur MedIA'
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
        'tasks': task_list,
        'total': len(task_list),
        'platform': 'Daur MedIA'
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
        download_name=f"daur_media_{task_id}.mp4"
    )

@app.route('/api/test/<test_type>', methods=['POST'])
def run_test(test_type):
    """Запуск различных тестов системы"""
    try:
        if test_type == 'cpu':
            # Тест CPU
            import time
            start_time = time.time()
            # Простой CPU тест
            result = sum(i*i for i in range(100000))
            end_time = time.time()
            
            return jsonify({
                'success': True,
                'test': 'CPU Performance',
                'duration': f"{end_time - start_time:.3f}s",
                'result': f"Вычислено: {result}"
            })
        
        elif test_type == 'memory':
            # Тест памяти
            memory = psutil.virtual_memory()
            return jsonify({
                'success': True,
                'test': 'Memory Test',
                'total': f"{memory.total // (1024**3)} GB",
                'available': f"{memory.available // (1024**3)} GB",
                'percent': f"{memory.percent}%"
            })
        
        elif test_type == 'gpu':
            # Тест GPU
            try:
                import torch
                if torch.cuda.is_available():
                    device_name = torch.cuda.get_device_name(0)
                    memory_total = torch.cuda.get_device_properties(0).total_memory // (1024**3)
                    return jsonify({
                        'success': True,
                        'test': 'GPU Test',
                        'device': device_name,
                        'memory': f"{memory_total} GB",
                        'cuda_version': torch.version.cuda
                    })
                else:
                    return jsonify({
                        'success': False,
                        'test': 'GPU Test',
                        'error': 'CUDA не доступна'
                    })
            except ImportError:
                return jsonify({
                    'success': False,
                    'test': 'GPU Test',
                    'error': 'PyTorch не установлен'
                })
        
        elif test_type == 'quick_generation':
            # Быстрый тест генерации
            if generator is None or not generator.initialized:
                return jsonify({
                    'success': False,
                    'test': 'Quick Generation Test',
                    'error': 'Модель не инициализирована'
                })
            
            # Создаем тестовую задачу
            test_prompt = "A simple test video, minimal quality"
            task_id = str(uuid.uuid4())
            
            task_data = {
                'id': task_id,
                'prompt': test_prompt,
                'video_width': 720,
                'video_height': 480,
                'video_length': 65,  # Минимальная длина
                'infer_steps': 10,   # Минимальные шаги
                'cfg_scale': 6.0,
                'status': 'testing',
                'created_at': datetime.now().isoformat()
            }
            
            with task_lock:
                tasks[task_id] = task_data
            
            return jsonify({
                'success': True,
                'test': 'Quick Generation Test',
                'task_id': task_id,
                'message': 'Тестовая задача создана'
            })
        
        else:
            return jsonify({
                'success': False,
                'error': f'Неизвестный тип теста: {test_type}'
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/system_stats')
def get_system_stats():
    """Получение системной статистики"""
    update_system_stats()
    return jsonify(system_stats)

if __name__ == '__main__':
    # Создание директории для результатов
    os.makedirs('./generated_videos', exist_ok=True)
    
    print("🚀 Запуск Daur MedIA - AI Video Generation Platform")
    print("📱 Откройте http://localhost:5000 в браузере")
    print("⚠️  Убедитесь, что у вас установлены все зависимости")
    
    # Запуск обновления статистики в отдельном потоке
    def stats_updater():
        while True:
            update_system_stats()
            time.sleep(5)
    
    stats_thread = threading.Thread(target=stats_updater)
    stats_thread.daemon = True
    stats_thread.start()
    
    app.run(host='0.0.0.0', port=5000, debug=True)

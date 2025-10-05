"""
API маршруты для генерации видео
"""

import os
import sys
import threading
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from src.models.video_task import db, VideoTask, TaskStatus

# Импорт HunyuanVideo API
from src.hunyuan_api import HunyuanVideoAPI

video_bp = Blueprint('video', __name__)

# Глобальный экземпляр API
hunyuan_api = None

def initialize_hunyuan_api():
    """Инициализация HunyuanVideo API"""
    global hunyuan_api
    if hunyuan_api is None:
        hunyuan_api = HunyuanVideoAPI()
        hunyuan_api.initialize()

def process_video_task(task_id):
    """Обработка задачи генерации видео в отдельном потоке"""
    global hunyuan_api
    
    # Получаем задачу из базы данных
    task = VideoTask.query.get(task_id)
    if not task:
        return
    
    try:
        # Обновляем статус на "обработка"
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.utcnow()
        db.session.commit()
        
        # Инициализируем API если нужно
        if hunyuan_api is None:
            initialize_hunyuan_api()
        
        # Генерируем видео
        result = hunyuan_api.generate_video(
            prompt=task.prompt,
            video_size=(task.video_height, task.video_width),
            video_length=task.video_length,
            infer_steps=task.infer_steps,
            seed=task.seed,
            save_path="/home/ubuntu/Daur-MedIA/generated_videos"
        )
        
        if result.get('success'):
            # Успешная генерация
            task.status = TaskStatus.COMPLETED
            task.output_path = result['output_path']
            task.generation_time = result.get('generation_time')
            task.seed = result.get('seed')
        else:
            # Ошибка генерации
            task.status = TaskStatus.FAILED
            task.error_message = result.get('error', 'Неизвестная ошибка')
        
        task.completed_at = datetime.utcnow()
        db.session.commit()
        
    except Exception as e:
        # Обработка исключений
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        task.completed_at = datetime.utcnow()
        db.session.commit()

@video_bp.route('/generate', methods=['POST'])
def generate_video():
    """Создание новой задачи генерации видео"""
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Требуется поле prompt'}), 400
        
        # Создаем новую задачу
        task = VideoTask(
            prompt=data['prompt'],
            video_width=data.get('video_width', 1280),
            video_height=data.get('video_height', 720),
            video_length=data.get('video_length', 129),
            infer_steps=data.get('infer_steps', 50),
            seed=data.get('seed'),
            client_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        db.session.add(task)
        db.session.commit()
        
        # Запускаем обработку в отдельном потоке
        thread = threading.Thread(target=process_video_task, args=(task.id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'message': 'Задача создана и поставлена в очередь'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_bp.route('/status/<int:task_id>', methods=['GET'])
def get_task_status(task_id):
    """Получение статуса задачи"""
    try:
        task = VideoTask.query.get(task_id)
        if not task:
            return jsonify({'error': 'Задача не найдена'}), 404
        
        return jsonify(task.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_bp.route('/tasks', methods=['GET'])
def get_all_tasks():
    """Получение списка всех задач"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        tasks = VideoTask.query.order_by(VideoTask.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'tasks': [task.to_dict() for task in tasks.items],
            'total': tasks.total,
            'pages': tasks.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_bp.route('/download/<int:task_id>', methods=['GET'])
def download_video(task_id):
    """Скачивание сгенерированного видео"""
    try:
        task = VideoTask.query.get(task_id)
        if not task:
            return jsonify({'error': 'Задача не найдена'}), 404
        
        if task.status != TaskStatus.COMPLETED:
            return jsonify({'error': 'Видео еще не готово'}), 400
        
        if not task.output_path or not os.path.exists(task.output_path):
            return jsonify({'error': 'Файл не найден'}), 404
        
        return send_file(
            task.output_path,
            as_attachment=True,
            download_name=f'video_{task.id}.mp4'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_bp.route('/api_status', methods=['GET'])
def get_api_status():
    """Получение статуса HunyuanVideo API"""
    try:
        global hunyuan_api
        
        if hunyuan_api is None:
            initialize_hunyuan_api()
        
        status = hunyuan_api.get_status()
        
        # Добавляем статистику задач
        total_tasks = VideoTask.query.count()
        pending_tasks = VideoTask.query.filter_by(status=TaskStatus.PENDING).count()
        processing_tasks = VideoTask.query.filter_by(status=TaskStatus.PROCESSING).count()
        completed_tasks = VideoTask.query.filter_by(status=TaskStatus.COMPLETED).count()
        failed_tasks = VideoTask.query.filter_by(status=TaskStatus.FAILED).count()
        
        status.update({
            'total_tasks': total_tasks,
            'pending_tasks': pending_tasks,
            'processing_tasks': processing_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks
        })
        
        return jsonify(status), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

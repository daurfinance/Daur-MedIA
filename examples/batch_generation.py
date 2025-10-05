#!/usr/bin/env python3
"""
Пример пакетной генерации видео с различными параметрами
"""

import sys
import os
import json
from datetime import datetime

# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hunyuan_video_interface import HunyuanVideoGenerator

def main():
    """Пример пакетной генерации видео"""
    
    # Создание генератора
    print("🚀 Создание HunyuanVideo генератора...")
    generator = HunyuanVideoGenerator()
    
    # Инициализация модели
    print("⚙️ Инициализация модели...")
    if not generator.initialize():
        print("❌ Ошибка инициализации модели")
        return
    
    print("✅ Модель успешно инициализирована!")
    
    # Конфигурация для пакетной генерации
    batch_config = [
        {
            "prompt": "A majestic eagle soaring through mountain peaks",
            "video_size": (720, 1280),
            "video_length": 129,
            "infer_steps": 50,
            "cfg_scale": 6.0
        },
        {
            "prompt": "Underwater coral reef with colorful fish swimming",
            "video_size": (720, 1280),
            "video_length": 129,
            "infer_steps": 40,
            "cfg_scale": 7.0
        },
        {
            "prompt": "Time-lapse of a flower blooming in spring garden",
            "video_size": (720, 1280),
            "video_length": 193,  # Более длинное видео
            "infer_steps": 60,
            "cfg_scale": 5.5
        },
        {
            "prompt": "Futuristic city skyline at night with neon lights",
            "video_size": (1080, 1920),  # Вертикальное видео
            "video_length": 129,
            "infer_steps": 45,
            "cfg_scale": 6.5
        }
    ]
    
    # Создание директории для результатов
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"./examples/batch_output_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    
    # Генерация видео для каждой конфигурации
    for i, config in enumerate(batch_config, 1):
        print(f"\n🎬 Генерация видео {i}/{len(batch_config)}")
        print(f"📝 Промпт: '{config['prompt']}'")
        print(f"📐 Размер: {config['video_size']}")
        print(f"⏱️ Длина: {config['video_length']} кадров")
        print(f"🔧 Шаги: {config['infer_steps']}")
        
        result = generator.generate_video(
            prompt=config["prompt"],
            video_size=config["video_size"],
            video_length=config["video_length"],
            infer_steps=config["infer_steps"],
            embedded_cfg_scale=config["cfg_scale"],
            save_path=output_dir,
            filename=f"batch_video_{i:02d}.mp4"
        )
        
        # Добавляем конфигурацию к результату
        result["config"] = config
        result["video_number"] = i
        results.append(result)
        
        if result["success"]:
            print(f"✅ Видео успешно создано: {result['output_path']}")
            print(f"🎲 Использованный сид: {result['seed']}")
        else:
            print(f"❌ Ошибка генерации: {result['error']}")
    
    # Сохранение отчета о генерации
    report_path = os.path.join(output_dir, "generation_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "total_videos": len(batch_config),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Отчет о генерации сохранен: {report_path}")
    
    # Статистика
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    print(f"\n🎉 Пакетная генерация завершена!")
    print(f"✅ Успешно: {successful}")
    print(f"❌ Ошибок: {failed}")
    print(f"📁 Результаты сохранены в: {output_dir}")

if __name__ == "__main__":
    main()

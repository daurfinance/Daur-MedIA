#!/usr/bin/env python3
"""
Пример базового использования Daur MedIA HunyuanVideo Generator
"""

import sys
import os

# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hunyuan_video_interface import HunyuanVideoGenerator

def main():
    """Пример базового использования генератора видео"""
    
    # Создание генератора
    print("🚀 Создание HunyuanVideo генератора...")
    generator = HunyuanVideoGenerator()
    
    # Инициализация модели
    print("⚙️ Инициализация модели...")
    if not generator.initialize():
        print("❌ Ошибка инициализации модели")
        return
    
    print("✅ Модель успешно инициализирована!")
    
    # Параметры генерации
    prompts = [
        "A cat walking on grass, realistic style",
        "A beautiful sunset over the ocean, cinematic",
        "A person dancing in the rain, artistic style"
    ]
    
    # Генерация видео для каждого промпта
    for i, prompt in enumerate(prompts, 1):
        print(f"\n🎬 Генерация видео {i}/{len(prompts)}: '{prompt}'")
        
        result = generator.generate_video(
            prompt=prompt,
            video_size=(720, 1280),  # HD разрешение
            video_length=129,        # ~5 секунд при 24 FPS
            infer_steps=30,          # Быстрая генерация
            save_path="./examples/output",
            filename=f"example_{i}.mp4"
        )
        
        if result["success"]:
            print(f"✅ Видео успешно создано: {result['output_path']}")
            print(f"🎲 Использованный сид: {result['seed']}")
        else:
            print(f"❌ Ошибка генерации: {result['error']}")
    
    print("\n🎉 Генерация завершена!")

if __name__ == "__main__":
    main()

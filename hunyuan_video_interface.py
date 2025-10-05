#!/usr/bin/env python3
"""
Daur MedIA - HunyuanVideo Interface
Полноценная интеграция с HunyuanVideo для генерации видео без сторонних API
"""

import os
import sys
import torch
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Добавляем путь к HunyuanVideo
sys.path.insert(0, '/home/ubuntu/HunyuanVideo')

try:
    from hyvideo.utils.file_utils import save_videos_grid
    from hyvideo.config import parse_args
    from hyvideo.inference import HunyuanVideoSampler
    HUNYUAN_AVAILABLE = True
except ImportError as e:
    print(f"HunyuanVideo не доступен: {e}")
    HUNYUAN_AVAILABLE = False

class HunyuanVideoGenerator:
    """Класс для генерации видео с помощью HunyuanVideo"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Инициализация генератора
        
        Args:
            model_path: Путь к модели (опционально)
        """
        self.model_path = model_path
        self.sampler = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.initialized = False
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def initialize(self) -> bool:
        """
        Инициализация модели HunyuanVideo
        
        Returns:
            bool: True если инициализация успешна
        """
        if not HUNYUAN_AVAILABLE:
            self.logger.error("HunyuanVideo не доступен")
            return False
            
        try:
            # Настройки по умолчанию для HunyuanVideo
            args = argparse.Namespace(
                video_size=(720, 1280),
                video_length=129,
                infer_steps=50,
                prompt="",
                seed=None,
                cfg_scale=1.0,
                embedded_cfg_scale=6.0,
                reproduce=True,
                batch_size=1,
                save_path="./results",
                name="test",
                model_base=self.model_path or "Tencent-Hunyuan/HunyuanVideo",
                dit_weight=None,
                vae_weight=None,
                text_encoder_weight=None,
                text_encoder_2_weight=None,
                tokenizer=None,
                tokenizer_2=None,
                flow_reverse=True,
                use_cpu_offload=False,
                save_memory=False,
                ulysses_degree=1,
                ring_degree=1,
                disable_autocast=False
            )
            
            # Инициализация семплера
            self.sampler = HunyuanVideoSampler.from_pretrained(
                args.model_base, 
                args=args
            )
            
            self.initialized = True
            self.logger.info(f"HunyuanVideo инициализирован на устройстве: {self.device}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации HunyuanVideo: {e}")
            return False
    
    def generate_video(
        self,
        prompt: str,
        video_size: tuple = (720, 1280),
        video_length: int = 129,
        infer_steps: int = 50,
        seed: Optional[int] = None,
        cfg_scale: float = 1.0,
        embedded_cfg_scale: float = 6.0,
        save_path: str = "./results",
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Генерация видео по текстовому описанию
        
        Args:
            prompt: Текстовое описание видео
            video_size: Размер видео (высота, ширина)
            video_length: Длина видео в кадрах
            infer_steps: Количество шагов инференса
            seed: Сид для воспроизводимости
            cfg_scale: Масштаб CFG
            embedded_cfg_scale: Встроенный масштаб CFG
            save_path: Путь для сохранения
            filename: Имя файла (опционально)
            
        Returns:
            Dict с результатами генерации
        """
        if not self.initialized:
            if not self.initialize():
                return {
                    "success": False,
                    "error": "Не удалось инициализировать HunyuanVideo"
                }
        
        try:
            # Создаем директорию для сохранения
            os.makedirs(save_path, exist_ok=True)
            
            # Настройка параметров генерации
            if seed is None:
                seed = torch.randint(0, 2**32 - 1, (1,)).item()
            
            # Генерация видео
            self.logger.info(f"Начинаем генерацию видео: '{prompt}'")
            self.logger.info(f"Параметры: размер={video_size}, длина={video_length}, шаги={infer_steps}")
            
            # Подготовка входных данных
            height, width = video_size
            
            # Генерация с помощью HunyuanVideo
            outputs = self.sampler.predict(
                prompt=prompt,
                height=height,
                width=width,
                video_length=video_length,
                seed=seed,
                infer_steps=infer_steps,
                guidance_scale=cfg_scale,
                embedded_guidance_scale=embedded_cfg_scale,
                batch_size=1,
                num_videos_per_prompt=1
            )
            
            # Сохранение результата
            if filename is None:
                filename = f"video_{seed}.mp4"
            
            output_path = os.path.join(save_path, filename)
            
            # Сохранение видео
            save_videos_grid(outputs, output_path, fps=24)
            
            self.logger.info(f"Видео успешно сохранено: {output_path}")
            
            return {
                "success": True,
                "output_path": output_path,
                "seed": seed,
                "prompt": prompt,
                "video_size": video_size,
                "video_length": video_length,
                "infer_steps": infer_steps
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации видео: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Получение информации о модели
        
        Returns:
            Dict с информацией о модели
        """
        return {
            "initialized": self.initialized,
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
            "hunyuan_available": HUNYUAN_AVAILABLE,
            "model_path": self.model_path
        }

def main():
    """Основная функция для тестирования"""
    parser = argparse.ArgumentParser(description="Daur MedIA HunyuanVideo Generator")
    parser.add_argument("--prompt", type=str, required=True, help="Текстовое описание видео")
    parser.add_argument("--output", type=str, default="./output", help="Директория для сохранения")
    parser.add_argument("--width", type=int, default=1280, help="Ширина видео")
    parser.add_argument("--height", type=int, default=720, help="Высота видео")
    parser.add_argument("--length", type=int, default=129, help="Длина видео в кадрах")
    parser.add_argument("--steps", type=int, default=50, help="Количество шагов инференса")
    parser.add_argument("--seed", type=int, default=None, help="Сид для воспроизводимости")
    
    args = parser.parse_args()
    
    # Создание генератора
    generator = HunyuanVideoGenerator()
    
    # Генерация видео
    result = generator.generate_video(
        prompt=args.prompt,
        video_size=(args.height, args.width),
        video_length=args.length,
        infer_steps=args.steps,
        seed=args.seed,
        save_path=args.output
    )
    
    if result["success"]:
        print(f"✅ Видео успешно создано: {result['output_path']}")
        print(f"🎲 Использованный сид: {result['seed']}")
    else:
        print(f"❌ Ошибка: {result['error']}")

if __name__ == "__main__":
    main()

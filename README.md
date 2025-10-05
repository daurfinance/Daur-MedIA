# Daur MedIA - HunyuanVideo Generator

![Daur MedIA Logo](https://img.shields.io/badge/Daur%20MedIA-HunyuanVideo%20Generator-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8%2B-green?style=for-the-badge&logo=python)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-red?style=for-the-badge&logo=pytorch)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

Локальный веб-интерфейс для генерации видео с помощью модели **HunyuanVideo** от Tencent. Полностью автономное решение без использования сторонних API.

## 🎯 Особенности

- **🚀 Локальная генерация** - Работает полностью на вашем оборудовании
- **🎨 Современный интерфейс** - Красивый веб-интерфейс с поддержкой темной темы
- **⚡ Асинхронная обработка** - Множественные задачи генерации одновременно
- **📱 Адаптивный дизайн** - Работает на всех устройствах
- **🔧 Гибкие настройки** - Полный контроль над параметрами генерации
- **📊 Отслеживание прогресса** - Мониторинг статуса всех задач
- **💾 Автоматическое сохранение** - Все видео сохраняются локально

## 🛠️ Установка

### Системные требования

- **Python 3.8+**
- **CUDA 11.8+** (рекомендуется для GPU ускорения)
- **16GB+ RAM** (рекомендуется 32GB)
- **10GB+ свободного места** для моделей

### 1. Клонирование репозитория

```bash
git clone https://github.com/daurfinance/Daur-MedIA.git
cd Daur-MedIA
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\\Scripts\\activate  # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Установка HunyuanVideo

```bash
git clone https://github.com/Tencent-Hunyuan/HunyuanVideo.git
cd HunyuanVideo
pip install -e .
cd ..
```

### 5. Скачивание моделей

Модели будут автоматически загружены при первом запуске, или вы можете загрузить их заранее:

```bash
# Автоматическая загрузка через Hugging Face Hub
python -c "from huggingface_hub import snapshot_download; snapshot_download('Tencent-Hunyuan/HunyuanVideo')"
```

## 🚀 Запуск

### Веб-интерфейс

```bash
python web_interface.py
```

Откройте браузер и перейдите по адресу: `http://localhost:5000`

### Командная строка

```bash
python hunyuan_video_interface.py --prompt "A cat walking on grass, realistic style" --output ./results
```

## 📖 Использование

### Веб-интерфейс

1. **Инициализация модели**
   - Нажмите кнопку "Инициализировать" в правом верхнем углу
   - Дождитесь загрузки модели (может занять несколько минут)

2. **Создание видео**
   - Введите описание видео на английском языке
   - Настройте параметры (размер, длина, количество шагов)
   - Нажмите "Создать видео"

3. **Отслеживание прогресса**
   - Следите за статусом в разделе "Задачи генерации"
   - Скачайте готовое видео по завершении

### Параметры генерации

| Параметр | Описание | Диапазон | По умолчанию |
|----------|----------|----------|--------------|
| **Prompt** | Текстовое описание видео | - | - |
| **Width** | Ширина видео в пикселях | 256-1920 | 1280 |
| **Height** | Высота видео в пикселях | 256-1080 | 720 |
| **Length** | Длина видео в кадрах | 65-257 | 129 |
| **Steps** | Количество шагов инференса | 10-100 | 50 |
| **Seed** | Сид для воспроизводимости | 0-2³²-1 | Случайный |
| **CFG Scale** | Масштаб классификатора | 1.0-20.0 | 6.0 |

### Примеры промптов

```
A cat walking on grass, realistic style
A beautiful sunset over the ocean, cinematic
A person dancing in the rain, artistic style
A car driving through a forest, aerial view
A flower blooming in time-lapse, macro photography
```

## 🔧 Конфигурация

### Настройка GPU

Для использования GPU убедитесь, что установлена правильная версия PyTorch:

```bash
# Для CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Для CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Оптимизация памяти

Для систем с ограниченной памятью добавьте в `hunyuan_video_interface.py`:

```python
# Включение CPU offload
args.use_cpu_offload = True

# Экономия памяти
args.save_memory = True
```

## 📁 Структура проекта

```
Daur-MedIA/
├── hunyuan_video_interface.py  # Основной интерфейс для HunyuanVideo
├── web_interface.py           # Веб-сервер Flask
├── requirements.txt           # Зависимости Python
├── README.md                 # Документация
├── LICENSE                   # Лицензия
├── generated_videos/         # Папка для сохранения видео
├── docs/                     # Документация и скриншоты
│   └── screenshots/
└── examples/                 # Примеры использования
    ├── basic_usage.py
    └── batch_generation.py
```

## 🐛 Устранение неполадок

### Ошибки CUDA

```bash
# Проверка доступности CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Проверка версии CUDA
nvidia-smi
```

### Ошибки памяти

- Уменьшите размер видео
- Уменьшите количество шагов
- Включите `use_cpu_offload`
- Закройте другие приложения

### Медленная генерация

- Убедитесь, что используется GPU
- Проверьте температуру GPU
- Уменьшите количество шагов для тестирования

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта! Пожалуйста:

1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

## 🙏 Благодарности

- **Tencent** за модель HunyuanVideo
- **Hugging Face** за инфраструктуру моделей
- **PyTorch** за фреймворк машинного обучения
- **Flask** за веб-фреймворк

## 📞 Поддержка

- **Issues**: [GitHub Issues](https://github.com/daurfinance/Daur-MedIA/issues)
- **Discussions**: [GitHub Discussions](https://github.com/daurfinance/Daur-MedIA/discussions)
- **Email**: support@daurfinance.com

## 🔗 Полезные ссылки

- [HunyuanVideo Official Repository](https://github.com/Tencent-Hunyuan/HunyuanVideo)
- [Hugging Face Model Hub](https://huggingface.co/Tencent-Hunyuan/HunyuanVideo)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

**Создано с ❤️ командой Daur Finance**

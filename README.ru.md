# Image Metadata Viewer

[English](README.md) | [Русский](README.ru.md)

Простое приложение для просмотра метаданных изображений с поддержкой отображения параметров генерации AI-изображений.

## Возможности

- Просмотр метаданных изображений (EXIF, параметры генерации AI и др.)
- Поддержка отображения параметров генерации Stable Diffusion
- Группировка параметров по категориям
- Копирование значений в буфер обмена
- Экспорт метаданных в различные форматы (TXT, CSV, JSON)
- Тёмная тема интерфейса
- Drag & Drop поддержка
- История открытых файлов

## Требования

- Python 3.8+
- PyQt6
- Pillow
- pyperclip

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/image-metadata-viewer.git
cd image-metadata-viewer
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Использование

Запустите приложение:
```bash
python imadata2.py
```

Или перетащите изображение в окно приложения.

## Поддерживаемые форматы

- JPEG/JPG
- PNG
- GIF
- BMP
- TIFF
- WebP

## Лицензия

MIT License. См. файл [LICENSE](LICENSE) для подробностей. 
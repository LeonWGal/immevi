# Image Metadata Viewer

[English](README.md) | [Русский](README.ru.md)

A simple application for viewing image metadata with support for AI image generation parameters display.

https://imgur.com/a/f47ORbk

## Features

- View image metadata (EXIF, AI generation parameters, etc.)
- Support for Stable Diffusion generation parameters display
- Parameter grouping by categories
- Copy values to clipboard
- Export metadata in various formats (TXT, CSV, JSON)
- Dark theme interface
- Drag & Drop support
- Recent files history

## Requirements

- Python 3.8+
- PyQt6
- Pillow
- pyperclip

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/image-metadata-viewer.git
cd image-metadata-viewer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python imadata2.py
```

Or drag and drop an image into the application window.

## Supported Formats

- JPEG/JPG
- PNG
- GIF
- BMP
- TIFF
- WebP

## License

MIT License. See [LICENSE](LICENSE) file for details. 

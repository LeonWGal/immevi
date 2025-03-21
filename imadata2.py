import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                            QWidget, QTableWidget, QTableWidgetItem, QPushButton, 
                            QHBoxLayout, QFileDialog, QHeaderView, QSplitter,
                            QDialog, QDialogButtonBox, QTextEdit, QLineEdit,
                            QScrollArea, QFrame, QGridLayout, QToolBar, QStatusBar,
                            QToolButton, QMenu, QSizePolicy)
from PyQt6.QtCore import Qt, QSize, QPoint, QSettings, QTimer, QUrl
from PyQt6.QtGui import (QDragEnterEvent, QDropEvent, QIcon, QPixmap, QColor, 
                         QPalette, QFont, QAction, QDesktopServices)
import PIL.Image
from PIL.ExifTags import TAGS
import pyperclip

class ClickableLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def mousePressEvent(self, event):
        # Правильно найти родительский ImageMetadataViewer через иерархию
        parent = self.parent()
        while parent and not isinstance(parent, ImageMetadataViewer):
            parent = parent.parent()
        
        if parent:
            parent.show_full_image()

class MetadataTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, 2, parent)
        self.setHorizontalHeaderLabels(["Property", "Value"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Включаем перенос текста
        self.setWordWrap(True)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        self.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: none;
                border-radius: 6px;
                gridline-color: #3a3a3a;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #e0e0e0;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #3a3a3a;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
            }
        """)
        
        # Подключаем обработчик двойного клика
        self.cellDoubleClicked.connect(self.copy_cell_content)
    
    def copy_cell_content(self, row, column):
        """Копирует содержимое ячейки в буфер обмена при двойном клике."""
        # Проверяем, не является ли строка заголовком категории
        if self.columnSpan(row, 0) == 2:
            return  # Это заголовок категории, ничего не делаем
            
        item = self.item(row, column)
        if item:
            pyperclip.copy(item.text())
            # Получаем родительское окно для отображения уведомления
            parent = self.parent()
            while parent and not isinstance(parent, ImageMetadataViewer):
                parent = parent.parent()
            if parent:
                parent.status_message.showMessage("Value copied to clipboard")

class ImageViewer(QScrollArea):
    def __init__(self, metadata_viewer):
        super().__init__()
        self.metadata_viewer = metadata_viewer
        self.setWidgetResizable(True)
        self.setMinimumWidth(300)
        self.setStyleSheet("background-color: #1a1a1a; border: none; border-radius: 6px;")
        
        self.image_label = ClickableLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #1a1a1a; border-radius: 6px;")
        
        self.setWidget(self.image_label)
        
    def set_image(self, pixmap):
        self.image_label.setPixmap(pixmap)
        
    def clear(self):
        self.image_label.clear()

class SearchBox(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Filter metadata...")
        self.setStyleSheet("""
            QLineEdit {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
        """)
        
        # Add clear button
        self.setClearButtonEnabled(True)

class DropArea(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Drop image here or click to browse")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #555555;
                border-radius: 6px;
                padding: 12px;
                color: #cccccc;
                font-size: 15px;
                background-color: #2a2a2a;
            }
            QLabel:hover {
                background-color: #333333;
                border-color: #777777;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.setMinimumHeight(60)
        self.setMaximumHeight(60)

class ActionButton(QPushButton):
    def __init__(self, text, icon_name=None, parent=None):
        super().__init__(text, parent)
        if icon_name:
            # Используем встроенные иконки Qt вместо файлов
            self.setIcon(self.get_icon(icon_name))
        
        self.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: normal;
                min-width: 110px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #444444;
            }
            QPushButton:disabled {
                background-color: #252525;
                color: #777777;
            }
        """)
    
    def get_icon(self, name):
        # Получаем стандартные иконки Qt вместо файлов
        if name == "copy":
            return QApplication.style().standardIcon(QApplication.style().StandardPixmap.SP_DialogSaveButton)
        elif name == "copy-all":
            return QApplication.style().standardIcon(QApplication.style().StandardPixmap.SP_DialogApplyButton)
        elif name == "export":
            return QApplication.style().standardIcon(QApplication.style().StandardPixmap.SP_FileIcon)
        elif name == "open":
            return QApplication.style().standardIcon(QApplication.style().StandardPixmap.SP_DialogOpenButton)
        elif name == "recent":
            return QApplication.style().standardIcon(QApplication.style().StandardPixmap.SP_FileDialogListView)
        return QIcon()

class PrimaryButton(ActionButton):
    def __init__(self, text, icon_name=None, parent=None):
        super().__init__(text, icon_name, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: normal;
                min-width: 110px;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
            QPushButton:pressed {
                background-color: #006cbe;
            }
            QPushButton:disabled {
                background-color: #25476a;
                color: #a0a0a0;
            }
        """)

class StatusMessage(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("color: #aaaaaa; font-size: 13px; padding: 2px 10px;")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.clear)
        
    def showMessage(self, message, timeout=5000):
        self.setText(message)
        if timeout > 0:
            self.timer.start(timeout)

class FullImageDialog(QDialog):
    def __init__(self, pixmap, filename, file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Image Preview - {filename}")
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Scroll area для изображения
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setPixmap(pixmap)
        
        scroll_area.setWidget(image_label)
        layout.addWidget(scroll_area)
        
        # Кнопки внизу
        button_layout = QHBoxLayout()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
        """)
        
        open_button = QPushButton("Open in Default Viewer")
        open_button.clicked.connect(lambda: self.open_in_external(file_path))
        open_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(open_button)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def open_in_external(self, file_path):
        if os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

class ImageMetadataViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Metadata Viewer")
        self.setAcceptDrops(True)
        self.resize(1100, 700)
        self.setMinimumSize(800, 500)
        
        # Загружаем настройки
        self.settings = QSettings("MetadataViewer", "ImageMetadataViewer")
        self.restore_geometry()
        
        # Список недавних файлов
        self.recent_files = self.settings.value("recentFiles", [])
        if not isinstance(self.recent_files, list):
            self.recent_files = []
        
        # Устанавливаем темную тему
        self.set_dark_theme()
        
        # Создаем центральный виджет и основной макет
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # Создаем тулбар
        self.create_toolbar()
        
        # Область для перетаскивания
        self.drop_area = DropArea()
        self.drop_area.mousePressEvent = lambda e: self.browse_files()
        main_layout.addWidget(self.drop_area)
        
        # Создаем разделенный контейнер
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #555555;
            }
        """)
        
        # Левая панель с просмотром изображения
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        
        # Виджет просмотра изображения
        self.image_viewer = ImageViewer(self)
        left_layout.addWidget(self.image_viewer)
        
        # Добавляем базовую информацию о файле
        self.file_info_widget = QFrame()
        self.file_info_widget.setFrameShape(QFrame.Shape.StyledPanel)
        self.file_info_widget.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-radius: 6px;
                padding: 8px;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)
        
        self.file_info_layout = QGridLayout(self.file_info_widget)
        self.file_info_widget.setVisible(False)
        self.file_info_layout.setContentsMargins(10, 10, 10, 10)
        self.file_info_layout.setSpacing(5)
        
        # Поля с базовой информацией будем добавлять динамически
        left_layout.addWidget(self.file_info_widget)
        
        splitter.addWidget(left_container)
        
        # Правая панель с метаданными
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        
        # Поиск метаданных
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        
        self.search_input = SearchBox()
        self.search_input.textChanged.connect(self.filter_metadata)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        right_layout.addLayout(search_layout)
        
        # Таблица метаданных
        self.metadata_table = MetadataTableWidget()
        self.metadata_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.metadata_table.customContextMenuRequested.connect(self.show_context_menu)
        right_layout.addWidget(self.metadata_table)
        
        splitter.addWidget(right_container)
        
        # Устанавливаем начальное соотношение сторон сплиттера (40% для левой панели, 60% для правой)
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
        
        # Панель с кнопками
        button_layout = QHBoxLayout()
        
        self.copy_selected_button = ActionButton("Copy Selected", "copy")
        self.copy_selected_button.clicked.connect(self.copy_selected)
        self.copy_all_button = ActionButton("Copy All", "copy-all")
        self.copy_all_button.clicked.connect(self.copy_all)
        self.export_button = ActionButton("Export", "export")
        self.export_button.clicked.connect(self.export_metadata)
        
        button_layout.addWidget(self.copy_selected_button)
        button_layout.addWidget(self.copy_all_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        
        self.open_folder_button = ActionButton("Open Folder", "open")
        self.open_folder_button.clicked.connect(self.open_containing_folder)
        button_layout.addWidget(self.open_folder_button)
        
        main_layout.addLayout(button_layout)
        
        # Устанавливаем центральный виджет
        self.setCentralWidget(central_widget)
        
        # Создаем статусбар
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("QStatusBar { background-color: #252525; color: #aaaaaa; }")
        self.status_message = StatusMessage("Ready to process images")
        self.status_bar.addWidget(self.status_message, 1)
        self.setStatusBar(self.status_bar)
        
        # Инициализируем текущий путь к изображению
        self.current_image_path = None
        self.metadata_dict = {}
        self.original_pixmap = None
        
        # Деактивируем кнопки, пока не загружено изображение
        self.update_button_states(False)
        
        # Добавляем таймер для автоматического растягивания ячеек
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.adjust_table_rows)
    
    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #252525;
                border: none;
                spacing: 5px;
                padding: 2px 5px;
            }
            QToolButton {
                color: #e0e0e0;
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 5px;
                margin: 2px;
            }
            QToolButton:hover {
                background-color: #3a3a3a;
            }
            QToolButton:pressed {
                background-color: #444444;
            }
            QToolButton:checked {
                background-color: #0078d4;
            }
        """)
        
        # Действия для тулбара
        open_action = QAction("Open", self)
        open_action.setToolTip("Open an image file")
        open_action.setIcon(ActionButton.get_icon(None, "open"))
        open_action.triggered.connect(self.browse_files)
        
        # Меню для недавно открытых файлов
        self.recent_menu = QMenu(self)
        self.recent_menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #555555;
            }
            QMenu::item {
                padding: 5px 20px 5px 20px;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
        """)
        
        # Обновим меню недавно открытых файлов
        self.update_recent_menu()
        
        # Кнопка для недавних файлов
        recent_button = QToolButton()
        recent_button.setText("Recent")
        recent_button.setToolTip("Recently opened files")
        recent_button.setIcon(ActionButton.get_icon(None, "recent"))
        recent_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        recent_button.setMenu(self.recent_menu)
        
        export_action = QAction("Export", self)
        export_action.setToolTip("Export metadata to file")
        export_action.setIcon(ActionButton.get_icon(None, "export"))
        export_action.triggered.connect(self.export_metadata)
        
        # Добавляем кнопки в тулбар
        toolbar.addAction(open_action)
        toolbar.addWidget(recent_button)
        toolbar.addSeparator()
        toolbar.addAction(export_action)
        
        self.addToolBar(toolbar)
    
    def update_recent_menu(self):
        """Обновляет меню недавно открытых файлов."""
        self.recent_menu.clear()
        
        if not self.recent_files:
            no_recent = QAction("No recent files", self)
            no_recent.setEnabled(False)
            self.recent_menu.addAction(no_recent)
        else:
            for file_path in self.recent_files:
                if os.path.exists(file_path):
                    action = QAction(os.path.basename(file_path), self)
                    action.setStatusTip(file_path)
                    action.triggered.connect(lambda checked=False, path=file_path: self.process_image(path))
                    self.recent_menu.addAction(action)
            
            # Добавляем разделитель и пункт "Очистить историю"
            if len(self.recent_files) > 0:
                self.recent_menu.addSeparator()
                clear_action = QAction("Clear Recent Files", self)
                clear_action.triggered.connect(self.clear_recent_files)
                self.recent_menu.addAction(clear_action)
    
    def add_to_recent_files(self, file_path):
        """Добавляет файл в список недавно открытых."""
        # Удаляем файл из списка, если он уже есть
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        
        # Добавляем файл в начало списка
        self.recent_files.insert(0, file_path)
        
        # Ограничиваем список 10 элементами
        self.recent_files = self.recent_files[:10]
        
        # Сохраняем список в настройках
        self.settings.setValue("recentFiles", self.recent_files)
        
        # Обновляем меню
        self.update_recent_menu()
    
    def clear_recent_files(self):
        """Очищает список недавно открытых файлов."""
        self.recent_files = []
        self.settings.setValue("recentFiles", self.recent_files)
        self.update_recent_menu()
        self.status_message.showMessage("Recent files list cleared")
    
    def set_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(40, 40, 40))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(224, 224, 224))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(224, 224, 224))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(224, 224, 224))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(224, 224, 224))
        dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(0, 130, 200))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 212))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        self.setPalette(dark_palette)
        
        # Устанавливаем стили для всего приложения
        QApplication.setStyle("Fusion")
        QApplication.instance().setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background-color: #2a2a2a;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #5a5a5a;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6a6a6a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background-color: #2a2a2a;
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #5a5a5a;
                min-width: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #6a6a6a;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                width: 0px;
            }
            QToolTip {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #555555;
                padding: 5px;
            }
        """)
    
    def restore_geometry(self):
        # Восстановление размеров и позиции окна
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Центрируем окно на экране по умолчанию
            screen_geometry = QApplication.primaryScreen().geometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)
    
    def update_button_states(self, has_data):
        """Обновляет состояние кнопок в зависимости от наличия данных."""
        self.copy_selected_button.setEnabled(has_data)
        self.copy_all_button.setEnabled(has_data)
        self.export_button.setEnabled(has_data)
        self.open_folder_button.setEnabled(has_data)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')):
                    self.drop_area.setStyleSheet("""
                        QLabel {
                            border: 2px dashed #0078d4;
                            border-radius: 6px;
                            padding: 12px;
                            color: #ffffff;
                            font-size: 15px;
                            background-color: rgba(0, 120, 212, 0.1);
                        }
                    """)
                    event.acceptProposedAction()
                    return
        
        event.ignore()
    
    def dragLeaveEvent(self, event):
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #555555;
                border-radius: 6px;
                padding: 12px;
                color: #cccccc;
                font-size: 15px;
                background-color: #2a2a2a;
            }
            QLabel:hover {
                background-color: #333333;
                border-color: #777777;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #555555;
                border-radius: 6px;
                padding: 12px;
                color: #cccccc;
                font-size: 15px;
                background-color: #2a2a2a;
            }
            QLabel:hover {
                background-color: #333333;
                border-color: #777777;
            }
        """)
        
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')):
                    self.process_image(file_path)
                    break  # Process only the first valid image
        
        event.acceptProposedAction()
    
    def browse_files(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, 
            "Select Image", 
            "", 
            "Image Files (*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp)"
        )
        
        if file_path:
            self.process_image(file_path)
    
    def process_image(self, file_path):
        self.current_image_path = file_path
        self.status_message.showMessage(f"Processing: {os.path.basename(file_path)}")
        
        # Display image preview
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            # Scale maintaining aspect ratio
            self.original_pixmap = pixmap
            max_width = self.image_viewer.width() - 20
            max_height = self.image_viewer.height() - 20
            
            scaled_pixmap = pixmap.scaled(
                max_width, max_height,
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.image_viewer.set_image(scaled_pixmap)
            
            # Extract and display metadata
            self.extract_metadata(file_path)
            
            # Update drop area with filename
            filename = os.path.basename(file_path)
            self.drop_area.setText(filename)
            self.drop_area.setToolTip(file_path)
            
            # Обновляем заголовок окна
            self.setWindowTitle(f"{filename} - Image Metadata Viewer")
            
            # Обновляем состояние кнопок
            self.update_button_states(True)
            
            # Добавляем файл в недавние
            self.add_to_recent_files(file_path)
            
        else:
            self.status_message.showMessage(f"Error: Could not load image {os.path.basename(file_path)}")
    
    def update_file_info_widget(self, file_info_data):
        """Обновляет виджет с базовой информацией о файле."""
        # Очищаем существующие виджеты
        for i in reversed(range(self.file_info_layout.count())):
            item = self.file_info_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        # Добавляем новую информацию
        row = 0
        for key, value in file_info_data.items():
            label_key = QLabel(f"{key}:")
            label_key.setStyleSheet("color: #aaaaaa; font-weight: normal;")
            
            label_value = QLabel(str(value))
            label_value.setStyleSheet("color: #e0e0e0; font-weight: normal;")
            label_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            label_value.setWordWrap(True)
            
            self.file_info_layout.addWidget(label_key, row, 0)
            self.file_info_layout.addWidget(label_value, row, 1)
            row += 1
        
        self.file_info_widget.setVisible(True)
    
    def extract_metadata(self, file_path):
        # Clear previous metadata
        self.metadata_table.setRowCount(0)
        self.metadata_dict = {}
        self.search_input.clear()
        
        # Категории параметров
        parameters = {
            "Prompt": [],           # Основной промпт и теги
            "Negative prompt": [],  # Негативный промпт
            "Seed": [],            # Сид генерации
            "Model Info": {},      # Информация о модели
            "Generation Parameters": {},  # Параметры генерации
            "Other Parameters": {}  # Прочие параметры
        }
        
        # Остальные категории метаданных
        categories = {
            "File Info": {},
            "Image Properties": {},
            "Camera Info": {},
            "GPS Data": {},
            "Other EXIF": {},
            "Other Metadata": {}
        }
        
        try:
            # Базовая информация о файле
            file_info = os.stat(file_path)
            file_size_b = file_info.st_size
            file_size_kb = file_size_b / 1024
            file_size_mb = file_size_kb / 1024
            
            if file_size_mb >= 1:
                file_size_str = f"{file_size_mb:.2f} MB ({file_size_b:,} bytes)"
            else:
                file_size_str = f"{file_size_kb:.2f} KB ({file_size_b:,} bytes)"
            
            categories["File Info"] = {
                "Filename": os.path.basename(file_path),
                "Directory": os.path.dirname(file_path),
                "File size": file_size_str,
                "Created": datetime.fromtimestamp(file_info.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "Modified": datetime.fromtimestamp(file_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "Last accessed": datetime.fromtimestamp(file_info.st_atime).strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            # Обновляем виджет с информацией о файле
            self.update_file_info_widget({
                "Filename": os.path.basename(file_path),
                "Size": file_size_str,
                "Modified": datetime.fromtimestamp(file_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Извлекаем метаданные изображения
            with PIL.Image.open(file_path) as img:
                # Get image dimensions
                width, height = img.size
                categories["Image Properties"]["Dimensions"] = f"{width} × {height} pixels"
                categories["Image Properties"]["Format"] = img.format or "Unknown"
                categories["Image Properties"]["Mode"] = img.mode
                
                # Get metadata and parse parameters
                for key, value in img.info.items():
                    if isinstance(value, bytes):
                        formatted_value = f"<binary data: {len(value)} bytes>"
                    else:
                        formatted_value = str(value)
                        
                        # Парсим параметры
                        if "parameters" in key.lower():
                            lines = formatted_value.split("\n")
                            current_category = None
                            prompt_lines = []
                            negative_prompt_lines = []
                            tipo_params = []
                            
                            for line in lines:
                                line = line.strip()
                                if not line:
                                    continue
                                    
                                # Определяем категорию параметра
                                if line.startswith("Negative prompt:"):
                                    current_category = "Negative prompt"
                                    negative_prompt_lines.append(line[15:].strip())
                                elif "Steps:" in line and "Schedule type:" in line:
                                    current_category = "Generation Parameters"
                                    params = line.split(",")
                                    for param in params:
                                        if ":" in param:
                                            k, v = param.split(":", 1)
                                            parameters[current_category][k.strip()] = v.strip()
                                elif line.startswith("Seed:"):
                                    current_category = "Seed"
                                    parameters[current_category].append(line.strip())
                                elif any(x in line for x in ["Model hash:", "Model:"]):
                                    current_category = "Model Info"
                                    params = line.split(",")
                                    for param in params:
                                        if ":" in param:
                                            k, v = param.split(":", 1)
                                            parameters[current_category][k.strip()] = v.strip()
                                elif "TIPO" in line.upper() or line.upper().startswith("TIPO"):
                                    current_category = "Other Parameters"
                                    tipo_params.append(line.strip())
                                elif line.upper().startswith("ADETAILER"):
                                    current_category = "Other Parameters"
                                    if "ADetailer" not in parameters[current_category]:
                                        parameters[current_category]["ADetailer"] = []
                                    parameters[current_category]["ADetailer"].append(line.strip())
                                elif not any(line.startswith(x) for x in ["Steps:", "Negative prompt:", "Seed:", "Model:"]):
                                    # Это основной промпт
                                    if current_category != "Prompt":
                                        current_category = "Prompt"
                                    prompt_lines.append(line.strip())
                            
                            # Добавляем собранные параметры
                            if prompt_lines:
                                # Убираем начальные двоеточия из значения
                                prompt_text = "\n".join(prompt_lines)
                                while prompt_text.startswith(":"):
                                    prompt_text = prompt_text[1:].strip()
                                parameters["Prompt"] = [prompt_text]
                            if negative_prompt_lines:
                                # Убираем начальные двоеточия из значения
                                neg_prompt_text = "\n".join(negative_prompt_lines)
                                while neg_prompt_text.startswith(":"):
                                    neg_prompt_text = neg_prompt_text[1:].strip()
                                parameters["Negative prompt"] = [neg_prompt_text]
                            if tipo_params:
                                # Группируем все параметры TIPO в одну ячейку
                                parameters["Other Parameters"]["TIPO Parameters"] = "\n".join(tipo_params)
                        else:
                            categories["Other Metadata"][key] = formatted_value
                
                # Get EXIF data if available
                try:
                    exif_data = img.getexif()
                    if exif_data:
                        for tag_id in exif_data:
                            tag = TAGS.get(tag_id, tag_id)
                            data = exif_data.get(tag_id)
                            
                            if isinstance(data, bytes):
                                formatted_data = f"<binary data: {len(data)} bytes>"
                            else:
                                formatted_data = str(data)
                            
                            if tag.lower() in ["make", "model", "lens", "exposuretime", "fnumber", 
                                              "isospeedratings", "focallength", "flash", "software",
                                              "exposureprogram", "shutterspeedvalue", "aperture",
                                              "exposuremode", "whitebalance", "meteringmode"]:
                                categories["Camera Info"][tag] = formatted_data
                            elif "gps" in tag.lower():
                                categories["GPS Data"][tag] = formatted_data
                            else:
                                categories["Other EXIF"][tag] = formatted_data
                except Exception as e:
                    categories["Other Metadata"]["EXIF Error"] = str(e)
        
        except Exception as e:
            self.status_message.showMessage(f"Error: {str(e)}")
            categories["Other Metadata"]["Error"] = f"Failed to extract metadata: {str(e)}"
        
        # Сохраняем словарь метаданных для экспорта
        self.metadata_dict = {}
        
        # Сначала добавляем параметры
        if any(parameters[cat] for cat in parameters):
            # Добавляем заголовок Parameters
            cat_row = self.metadata_table.rowCount()
            self.metadata_table.insertRow(cat_row)
            cat_item = QTableWidgetItem("Parameters")
            cat_item.setBackground(QColor(45, 45, 60))
            cat_item.setForeground(QColor(230, 230, 230))
            cat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            cat_item.setFont(QFont(cat_item.font().family(), cat_item.font().pointSize(), QFont.Weight.Bold))
            self.metadata_table.setSpan(cat_row, 0, 1, 2)
            self.metadata_table.setItem(cat_row, 0, cat_item)
            
            # Добавляем категории параметров
            for category, items in parameters.items():
                if items:  # Если есть данные в категории
                    # Добавляем подзаголовок категории
                    cat_row = self.metadata_table.rowCount()
                    self.metadata_table.insertRow(cat_row)
                    cat_item = QTableWidgetItem(f"  {category}")  # Добавляем отступ для подкатегории
                    cat_item.setBackground(QColor(35, 35, 50))
                    cat_item.setForeground(QColor(200, 200, 200))
                    cat_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    cat_item.setFont(QFont(cat_item.font().family(), cat_item.font().pointSize(), QFont.Weight.Bold))
                    self.metadata_table.setSpan(cat_row, 0, 1, 2)
                    self.metadata_table.setItem(cat_row, 0, cat_item)
                    
                    # Добавляем значения
                    if isinstance(items, list):
                        # Для списков (Prompt, Negative prompt, Seed)
                        for value in items:
                            self.add_metadata_row("", value)
                    else:
                        # Для словарей (Model Info, Generation Parameters, Other Parameters)
                        for key, value in items.items():
                            self.add_metadata_row(key, value)
            
            self.metadata_dict["Parameters"] = parameters
        
        # Затем добавляем остальные категории
        for category, items in categories.items():
            if items:
                self.metadata_dict[category] = items
                
                # Добавляем заголовок категории
                cat_row = self.metadata_table.rowCount()
                self.metadata_table.insertRow(cat_row)
                cat_item = QTableWidgetItem(category)
                cat_item.setBackground(QColor(45, 45, 60))
                cat_item.setForeground(QColor(230, 230, 230))
                cat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cat_item.setFont(QFont(cat_item.font().family(), cat_item.font().pointSize(), QFont.Weight.Bold))
                self.metadata_table.setSpan(cat_row, 0, 1, 2)
                self.metadata_table.setItem(cat_row, 0, cat_item)
                
                # Добавляем элементы категории
                for key, value in items.items():
                    self.add_metadata_row(key, value)
        
        # Настраиваем высоту строк
        self.adjust_table_rows()
        
        self.status_message.showMessage(f"Loaded metadata for {os.path.basename(file_path)}")
    
    def adjust_table_rows(self):
        """Настраивает высоту строк в таблице."""
        self.metadata_table.resizeRowsToContents()
    
    def add_metadata_row(self, key, value):
        row = self.metadata_table.rowCount()
        self.metadata_table.insertRow(row)
        
        # Определяем, является ли это промптом
        is_prompt = key == "" and any(self.metadata_table.item(row-2, 0).text().strip() == f"  {x}" 
                                    for x in ["Prompt", "Negative prompt"] 
                                    if row > 1 and self.metadata_table.item(row-2, 0))
        
        if is_prompt:
            # Для промптов используем предыдущий заголовок как ключ
            key = self.metadata_table.item(row-2, 0).text().strip()
        
        key_item = QTableWidgetItem(str(key))
        value_item = QTableWidgetItem(str(value))
        
        # Make items read-only
        key_item.setFlags(key_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        # Устанавливаем подсказку для значений
        key_item.setToolTip(str(key))
        value_item.setToolTip(str(value))
        
        # Устанавливаем стили для ячеек
        if row % 2 == 0:
            key_item.setBackground(QColor(35, 35, 35))
            value_item.setBackground(QColor(35, 35, 35))
        
        self.metadata_table.setItem(row, 0, key_item)
        self.metadata_table.setItem(row, 1, value_item)
    
    def show_context_menu(self, position):
        """Показывает контекстное меню для таблицы метаданных."""
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #555555;
            }
            QMenu::item {
                padding: 5px 20px 5px 20px;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
        """)
        
        indexes = self.metadata_table.selectedIndexes()
        
        # Действия меню
        copy_action = menu.addAction("Copy Value")
        copy_row_action = menu.addAction("Copy Row")
        
        if not indexes:
            # Нет выбранных ячеек
            copy_action.setEnabled(False)
            copy_row_action.setEnabled(False)
        
        # Выполняем действие в зависимости от выбора
        action = menu.exec(self.metadata_table.mapToGlobal(position))
        
        if action == copy_action and indexes:
            # Копируем значение выбранной ячейки
            index = indexes[0]  # Берем первую выбранную ячейку
            value = self.metadata_table.item(index.row(), index.column()).text()
            pyperclip.copy(value)
            self.status_message.showMessage(f"Value copied to clipboard")
        
        elif action == copy_row_action and indexes:
            # Копируем все значения строки
            row = indexes[0].row()
            # Проверяем, является ли строка заголовком категории
            if self.metadata_table.columnSpan(row, 0) == 2:
                # Это заголовок категории
                value = self.metadata_table.item(row, 0).text()
                pyperclip.copy(value)
                self.status_message.showMessage(f"Category name copied to clipboard")
            else:
                # Обычная строка
                key = self.metadata_table.item(row, 0).text()
                value = self.metadata_table.item(row, 1).text()
                pyperclip.copy(f"{key}: {value}")
                self.status_message.showMessage(f"Row copied to clipboard")
    
    def show_full_image(self):
        """Показывает полное изображение в отдельном окне."""
        if self.current_image_path and self.original_pixmap:
            dialog = FullImageDialog(
                self.original_pixmap, 
                os.path.basename(self.current_image_path),
                self.current_image_path,
                self
            )
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #2d2d2d;
                }
                QLabel {
                    color: #e0e0e0;
                }
            """)
            dialog.exec()
    
    def open_containing_folder(self):
        """Открывает папку, содержащую текущее изображение."""
        if self.current_image_path and os.path.exists(self.current_image_path):
            folder_path = os.path.dirname(self.current_image_path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
            self.status_message.showMessage(f"Opening folder: {folder_path}")
        else:
            self.status_message.showMessage("No valid file path available")
    
    def filter_metadata(self, text):
        """Фильтрует метаданные по введенному тексту."""
        text = text.lower()
        
        # Если текст пустой, показываем все строки
        if not text:
            for row in range(self.metadata_table.rowCount()):
                self.metadata_table.setRowHidden(row, False)
            return
            
        # Словарь для отслеживания видимости категорий
        category_has_visible = {}
        current_category = None
        
        # Сначала скрываем все строки и находим строки, соответствующие фильтру
        for row in range(self.metadata_table.rowCount()):
            # Проверяем, является ли строка заголовком категории
            if self.metadata_table.columnSpan(row, 0) == 2:
                # Это заголовок категории
                current_category = row
                category_name = self.metadata_table.item(row, 0).text().lower()
                category_has_visible[current_category] = text in category_name
                self.metadata_table.setRowHidden(row, not category_has_visible[current_category])
            else:
                # Обычная строка с метаданными
                key = self.metadata_table.item(row, 0).text().lower()
                value = self.metadata_table.item(row, 1).text().lower() if self.metadata_table.item(row, 1) else ""
                
                row_visible = text in key or text in value
                self.metadata_table.setRowHidden(row, not row_visible)
                
                # Если строка видима, также делаем видимой её категорию
                if row_visible and current_category is not None:
                    category_has_visible[current_category] = True
        
        # Показываем заголовки категорий, в которых есть видимые элементы
        for cat_row, has_visible in category_has_visible.items():
            self.metadata_table.setRowHidden(cat_row, not has_visible)
    
    def copy_selected(self):
        """Копирует выбранные метаданные в буфер обмена."""
        selected_rows = set(index.row() for index in self.metadata_table.selectedIndexes())
        if not selected_rows:
            self.status_message.showMessage("No metadata selected to copy")
            return
        
        text = ""
        for row in sorted(selected_rows):
            # Skip category headers
            if self.metadata_table.columnSpan(row, 0) == 2:
                text += f"\n=== {self.metadata_table.item(row, 0).text()} ===\n"
            else:
                key = self.metadata_table.item(row, 0).text()
                value = self.metadata_table.item(row, 1).text()
                text += f"{key}: {value}\n"
        
        pyperclip.copy(text.strip())
        self.status_message.showMessage(f"Copied {len(selected_rows)} metadata entries to clipboard")
    
    def copy_all(self):
        """Копирует все метаданные в буфер обмена."""
        if self.metadata_table.rowCount() == 0:
            self.status_message.showMessage("No metadata available to copy")
            return
        
        text = ""
        current_category = ""
        
        for row in range(self.metadata_table.rowCount()):
            # Check if it's a category header
            if self.metadata_table.columnSpan(row, 0) == 2:
                # Add category header
                current_category = self.metadata_table.item(row, 0).text()
                text += f"\n=== {current_category} ===\n"
            else:
                key = self.metadata_table.item(row, 0).text()
                value = self.metadata_table.item(row, 1).text()
                text += f"{key}: {value}\n"
        
        pyperclip.copy(text.strip())
        self.status_message.showMessage("Copied all metadata to clipboard")
    
    def export_metadata(self):
        """Экспортирует метаданные в файл."""
        if not self.metadata_dict:
            self.status_message.showMessage("No metadata available to export")
            return
            
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setDefaultSuffix("txt")
        
        default_filename = f"{os.path.splitext(os.path.basename(self.current_image_path))[0]}_metadata"
        file_dialog.selectFile(default_filename)
        
        file_dialog.setNameFilter("Text Files (*.txt);;CSV Files (*.csv);;JSON Files (*.json)")
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                file_path = file_paths[0]
                
                try:
                    ext = os.path.splitext(file_path)[1].lower()
                    
                    if ext == '.txt' or not ext:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(f"Metadata for: {os.path.basename(self.current_image_path)}\n")
                            f.write(f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                            
                            for category, items in self.metadata_dict.items():
                                f.write(f"\n=== {category} ===\n")
                                for key, value in items.items():
                                    f.write(f"{key}: {value}\n")
                                    
                    elif ext == '.csv':
                        import csv
                        with open(file_path, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(["Category", "Property", "Value"])
                            
                            for category, items in self.metadata_dict.items():
                                for key, value in items.items():
                                    writer.writerow([category, key, value])
                                    
                    elif ext == '.json':
                        import json
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(self.metadata_dict, f, indent=4, ensure_ascii=False)
                            
                    self.status_message.showMessage(f"Metadata exported to {os.path.basename(file_path)}")
                    
                except Exception as e:
                    self.status_message.showMessage(f"Error exporting metadata: {str(e)}")
    
    def resizeEvent(self, event):
        """Обрабатывает изменение размера окна."""
        super().resizeEvent(event)
        
        # Update image preview if we have an image loaded
        if self.current_image_path and hasattr(self, 'original_pixmap') and self.original_pixmap:
            max_width = self.image_viewer.width() - 20
            max_height = self.image_viewer.height() - 20
            
            scaled_pixmap = self.original_pixmap.scaled(
                max_width, max_height,
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.image_viewer.set_image(scaled_pixmap)
            
        # Планируем обновление высоты строк в таблице
        self.resize_timer.start(100)
    
    def closeEvent(self, event):
        """Обрабатывает закрытие окна."""
        # Сохраняем размер и положение окна
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

def create_example_image():
    """Создает пример изображения для тестирования, если файл не существует"""
    example_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "example.jpg")
    if not os.path.exists(example_file):
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (800, 600), color=(73, 109, 137))
            d = ImageDraw.Draw(img)
            d.rectangle([200, 100, 600, 500], fill=(128, 128, 128), outline=(255, 255, 255))
            d.text((300, 250), "Image Metadata Viewer\nTest Image", fill=(255, 255, 0))
            img.save(example_file)
            print(f"Created example image: {example_file}")
        except Exception as e:
            print(f"Could not create example image: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for better dark theme support
    
    # Создаем тестовое изображение, если нужно
    create_example_image()
    
    window = ImageMetadataViewer()
    window.show()
    
    # Автоматически загружаем пример, если он существует и нет аргументов
    if len(sys.argv) == 1:
        example_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "example.jpg")
        if os.path.exists(example_file):
            QTimer.singleShot(100, lambda: window.process_image(example_file))
    elif len(sys.argv) > 1:
        # Если указан файл в аргументах - загружаем его
        file_path = sys.argv[1]
        if os.path.exists(file_path) and os.path.isfile(file_path):
            QTimer.singleShot(100, lambda: window.process_image(file_path))
    
    sys.exit(app.exec())
# detail_panel.py

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import os

class DetailPanel(QWidget):
    """
    DetailPanel displays a large image with file information and tag buttons.
    When a new image is set, it updates the display and tag states.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Основная вертикальная компоновка виджета
        self.layout = QVBoxLayout(self)
        # Создаём QScrollArea для изображения
        self.scroll_area = QScrollArea(self)
        self.image_label = QLabel(self)  # QLabel для отображения изображения
        self.image_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.image_label)  # помещаем label в scroll area
        self.layout.addWidget(self.scroll_area)

        # Панель для метаданных: имя файла и разрешение
        self.info_label = QLabel(self)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.info_label)

        # Панель тегов: горизонтальный или вертикальный лэйаут
        self.tags_layout = QVBoxLayout()
        self.layout.addLayout(self.tags_layout)

        self.tag_buttons = {}   # Словарь: tag_id -> QPushButton
        self.current_image = None  # Текущее выбранное ImageItem

    def set_tags_available(self, tags):
        """
        Инициализируем панель тегов. tags — список TagItem, содержащий tag.id и tag.name.
        Создаём кнопку для каждого тега.
        """
        for tag in tags:
            btn = QPushButton(tag.name, self)
            btn.setCheckable(True)
            # Стиль: фон зелёный, когда кнопка в состоянии checked:contentReference[oaicite:3]{index=3}.
            btn.setStyleSheet("QPushButton:checked { background-color: green; color: white; }")
            # При переключении тега вызываем метод handle_tag_toggle
            btn.toggled.connect(lambda checked, tid=tag.id: self.handle_tag_toggle(tid, checked))
            self.tags_layout.addWidget(btn)
            self.tag_buttons[tag.id] = btn

    def set_image(self, image_item):
        """
        Обновить виджет новым изображением.
        image_item должен иметь свойства: id, filepath, tags (список активных tag_id).
        """
        self.current_image = image_item
        # Загрузка изображения в QPixmap
        pixmap = QPixmap(image_item.filepath)
        if pixmap.isNull():
            # Если не удалось загрузить, устанавливаем сообщение
            self.image_label.setText("Cannot load image")
        else:
            self.image_label.setPixmap(pixmap)
        # Обновляем информацию о файле: имя и разрешение
        filename = os.path.basename(image_item.filepath)
        if not pixmap.isNull():
            resolution = f"{pixmap.width()} x {pixmap.height()}"
        else:
            resolution = ""
        self.info_label.setText(f"{filename}  {resolution}")

        # Обновляем состояние кнопок тегов согласно image_item.tags
        active_tags = set(getattr(image_item, 'tags', []))
        for tag_id, btn in self.tag_buttons.items():
            # блокируем сигнал, чтобы не вызывать handle_tag_toggle во время обновления
            btn.blockSignals(True)
            btn.setChecked(tag_id in active_tags)
            btn.blockSignals(False)

    def handle_tag_toggle(self, tag_id, checked):
        """
        Обработчик переключения тега. Сразу сохраняет изменение через set_tag().
        """
        if self.current_image is None:
            return
        image_id = self.current_image.id
        # Вызываем функцию сохранения (предполагается реализация вне этого класса)
        set_tag(image_id, tag_id, checked)

# Пример заглушки функции сохранения тега в БД (должна быть реализована отдельно)
def set_tag(image_id, tag_id, value):
    """
    Сохраняет изменение тега (tag_id) для изображения image_id в базу данных.
    """
    # Здесь код сохранения в БД
    print(f"Tag {tag_id} set to {value} for image {image_id}")

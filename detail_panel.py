# detail_panel.py

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QPushButton
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
import os

class DetailPanel(QWidget):
    """
    DetailPanel displays a large image with file information and tag buttons.
    Emits a signal when a tag is toggled.
    """

    # Signal emitted when a tag button is toggled: args are (image_id, tag_id, new_state)
    tag_changed = pyqtSignal(int, int, bool)

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

        self.info_label = QLabel(self)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.info_label)

        # Layout for tag buttons
        self.tags_layout = QVBoxLayout()
        self.layout.addLayout(self.tags_layout)

        # Store buttons and current image
        self.tag_buttons = {}   # tag_id -> QPushButton
        self.current_image = None  # The currently displayed ImageItem

    def set_tags_available(self, tags):
        """
        Инициализируем панель тегов. tags — список TagItem, содержащий tag.id и tag.name.
        Создаём кнопку для каждого тега.
        """
        # Clear existing buttons if any
        for btn in self.tag_buttons.values():
            btn.deleteLater()
        self.tag_buttons.clear()

        # Create new buttons
        for tag in tags:
            btn = QPushButton(tag.name, self)
            btn.setCheckable(True)
            # Style for checked state
            btn.setStyleSheet(
                "QPushButton { padding: 8px; font-size: 14px; }"
                "QPushButton:checked { background-color: #3399FF; color: white; }"
            )
            # Connect toggle to handler
            btn.toggled.connect(lambda checked, tid=tag.id: self._on_button_toggled(tid, checked))
            self.tags_layout.addWidget(btn)
            self.tag_buttons[tag.id] = btn

    def set_image(self, image_item):
        """
        Display a new ImageItem (with id, filepath, tags list).
        Loads image, updates info, and adjusts button states.
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
        resolution = f"{pixmap.width()} x {pixmap.height()}" if not pixmap.isNull() else ""
        self.info_label.setText(f"{filename}    {resolution}")

        # Update tag buttons according to image_item.tags
        active_tag_ids = set(image_item.tags)
        for tag_id, btn in self.tag_buttons.items():
            # Prevent signal while updating
            btn.blockSignals(True)
            btn.setChecked(tag_id in active_tag_ids)
            btn.blockSignals(False)

    def _on_button_toggled(self, tag_id, checked):
        """
        Internal handler for button toggle.
        Emits tag_changed signal with (image_id, tag_id, new_state).
        """
        if not self.current_image:
            return
        image_id = self.current_image.id
        # Emit signal for controller to handle DB update
        self.tag_changed.emit(image_id, tag_id, checked)

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
        # Main vertical layout
        self.layout = QVBoxLayout(self)
        # Scroll area for the image
        self.scroll_area = QScrollArea(self)
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.image_label)
        self.layout.addWidget(self.scroll_area)

        # Label for file info (name and resolution)
        self.info_label = QLabel(self)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.info_label)

        # Layout for tag buttons
        self.tags_layout = QVBoxLayout()
        self.layout.addLayout(self.tags_layout)

        # Store buttons and current image
        self.tag_buttons = {}   # tag_id -> QPushButton
        self.current_image = None  # The currently displayed ImageItem
        self._orig_pixmap = None


    def set_tags_available(self, tags):
        """
        Initialize tag buttons from a list of TagItem (with id and name).
        Buttons are checkable and styled to indicate active state.
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
                "QPushButton { padding: 8px; font-size: 14px; border:2px solid gray; border-radius:4px }"
                "QPushButton:checked { background-color: #3399FF; color: white; border: 2px solid #1a73e8;}"
                "QPushButton:hover { background-color: #dddddd;}"
                "QPushButton : pressed { background-color: #bbbbbb } "
                "QPushButton:checked:hover { background-color: #428AFF; }"
                "QPushButton:checked:pressed { background-color: #1a5fcc; }"
            )
            # Connect toggle to handler
            btn.toggled.connect(lambda checked, tid=tag.id: self._on_button_toggled(tid, checked))
            self.tags_layout.addWidget(btn)
            self.tag_buttons[tag.id] = btn

#TODO make async
    def set_image(self, image_item):
        """
        Display a new ImageItem (with id, filepath, tags list).
        Loads image, updates info, and adjusts button states.
        """
        self.current_image = image_item
        
        # Load pixmap
        pixmap = QPixmap(image_item.filepath)
        if pixmap.isNull():
            self._orig_pixmap = None
            self.image_label.setText("Cannot load image")
        else:
            self._orig_pixmap = pixmap
            self._update_pixmap_scaled()

        # Update file info
        filename = os.path.basename(image_item.filepath)
        resolution = f"{pixmap.width()} x {pixmap.height()}" if not pixmap.isNull() else ""
        self.info_label.setText(f"{filename}    {resolution}")

        # Update tag buttons according to image_item.tags
        active_tag_names = image_item.tags
        for tag_id, btn in self.tag_buttons.items():
            # Prevent signal while updating
            btn.blockSignals(True)
            btn.setChecked(btn.text() in active_tag_names)
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._orig_pixmap:
            self._update_pixmap_scaled()

    def _update_pixmap_scaled(self):
        viewport_size = self.scroll_area.viewport().size()
        scaled = self._orig_pixmap.scaled(
            viewport_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)

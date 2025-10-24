from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QSize

from database import ImageItem

class ImageGrid(QListWidget):

    def __init__(self, parent = None):
        super().__init__(parent)

        self.setViewMode(QListWidget.IconMode)

        self.setResizeMode(QListWidget.Adjust)

        self.setIconSize(QSize(128,128))
        self.setGridSize(QSize(150,150))

        self.setMovement(QListWidget.Static)

        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.itemSelectionChanged.connect(self._on_selection_changed)


    def set_images(self, images):
        self.clear()
        
        for image_item in images:
            item = QListWidgetItem()

            pixmap = QPixmap(image_item.filepath)
            if pixmap:
                item.setIcon(QIcon(pixmap.scaled(128,128, Qt.KeepAspectRatio, Qt.SmoothTransformation)))

            item.setText(", ".join(image_item.tags))
            item.setData(Qt.UserRole, image_item) #thence we store the ImageItem object in the widgetItem - Roles - are just additional stored data, User is for custom data

            self.addItem(item)

    def get_selected_images(self):
        return [item.data(Qt.UserRole) for item in self.selectedItems()]
    
    selection_changed = pyqtSignal(list)

    def _on_selection_changed(self):
        self.selection_changed.emit(self.get_selected_images())

"""
Module: image_table_view.py
Description: PyQt5 widget for displaying a list of images in a grid/table view,
             similar to Windows Explorer "thumbnail view".
             Contains ImageTableModel, ImageDelegate, and ImageTableView classes.
"""

from PyQt5.QtCore import Qt, QSize, QRect, QModelIndex, QAbstractTableModel
from PyQt5.QtGui import QPixmap, QPainter, QFontMetrics
from PyQt5.QtWidgets import (
    QTableView, QStyledItemDelegate, QHeaderView, QStyleOptionViewItem
)

try:
    from database import ImageItem
except ImportError:
    # Placeholder for ImageItem dataclass if database.py is not available.
    from dataclasses import dataclass
    @dataclass
    class ImageItem:
        filepath: str
        tags: list

class ImageTableModel(QAbstractTableModel):
    """
    Model for a table of images.
    Inherits QAbstractTableModel to provide data (images and tags) to a QTableView.
    """
    # Custom role to provide the ImageItem to delegates
    ImageRole = Qt.UserRole + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._images = []       # List[ImageItem]
        self._columns = 1       # Number of columns in the table

    def set_images(self, images):
        """
        Set the list of images (ImageItem) to display.
        Resets the model to update the view.
        """
        self.beginResetModel()
        self._images = images or []
        self.endResetModel()

    def set_columns(self, columns):
        """
        Set the number of columns in the table.
        Resets the model to update row/column count.
        """
        if columns < 1:
            columns = 1
        if columns != self._columns:
            self.beginResetModel()
            self._columns = columns
            self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """
        Return the number of rows based on number of images and columns.
        """
        if parent.isValid():
            return 0
        if not self._images:
            return 0
        rows = (len(self._images) + self._columns - 1) // self._columns
        return rows

    def columnCount(self, parent=QModelIndex()):
        """
        Return the current number of columns.
        """
        if parent.isValid():
            return 0
        return self._columns

    def data(self, index, role=Qt.DisplayRole):
        """
        Return data for the given index and role.
        Provide the ImageItem via custom ImageRole.
        """
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        pos = row * self._columns + col
        if pos >= len(self._images):
            return None

        image_item = self._images[pos]

        if role == self.ImageRole:
            # Return the entire ImageItem for delegate to use
            return image_item
        elif role == Qt.ToolTipRole:
            # Show tags in a tooltip
            return ", ".join(image_item.tags)
        return None

    def flags(self, index):
        """
        Set item flags: enable and selectable. No editing.
        """
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


class ImageDelegate(QStyledItemDelegate):
    """
    Delegate to draw each image cell: a scaled thumbnail and tags text.
    Inherits QStyledItemDelegate to customize painting of items.
    """
    IMAGE_SIZE = 128  # Thumbnail size

    def paint(self, painter, option, index):
        """
        Custom paint method: draws the thumbnail and tags text.
        """
        # Obtain the ImageItem for this cell
        image_item = index.model().data(index, ImageTableModel.ImageRole)
        if not image_item:
            return

        rect = option.rect
        painter.save()

        # Draw background (highlight if selected)
        if option.state & QStyleOptionViewItem.State_Selected:
            painter.fillRect(rect, option.palette.highlight())
            text_color = option.palette.highlightedText().color()
        else:
            painter.fillRect(rect, option.palette.base())
            text_color = option.palette.text().color()

        # Load and scale the image
        pixmap = QPixmap(image_item.filepath)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.IMAGE_SIZE, self.IMAGE_SIZE,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            # Center the image horizontally, place it near the top with small margin
            pix_x = rect.x() + (rect.width() - scaled_pixmap.width()) / 2
            pix_y = rect.y() + 2  # top margin
            painter.drawPixmap(pix_x, pix_y, scaled_pixmap)

        # Draw tags text at bottom of cell
        painter.setPen(text_color)
        font_metrics = painter.fontMetrics()
        tags_text = ", ".join(image_item.tags)
        # Determine text drawing area
        margin = 4
        text_height = font_metrics.height()
        text_rect = QRect(
            rect.x() + margin,
            rect.y() + rect.height() - text_height - margin,
            rect.width() - 2*margin,
            text_height
        )
        # Elide text if too long to fit
        elided_text = font_metrics.elidedText(tags_text, Qt.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_text)

        painter.restore()

    def sizeHint(self, option, index):
        """
        Provide size hint for each item: width = IMAGE_SIZE, height = IMAGE_SIZE + text height + margins.
        """
        font_metrics = QFontMetrics(option.font)
        text_height = font_metrics.height()
        margin = 8  # total vertical margin (above and below)
        width = self.IMAGE_SIZE + margin
        height = self.IMAGE_SIZE + text_height + margin
        return QSize(width, height)


class ImageTableView(QTableView):
    """
    Table view to display images using ImageTableModel and ImageDelegate.
    Automatically adjusts number of columns based on the widget width.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize model and delegate
        self._model = ImageTableModel(self)
        self.setModel(self._model)
        self._delegate = ImageDelegate(self)
        self.setItemDelegate(self._delegate)

        # Hide headers and grid for a clean thumbnail view
        self.horizontalHeader().hide()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.setShowGrid(False)

        # Enable selection (extended for multiple selections)
        self.setSelectionBehavior(QTableView.SelectItems)
        self.setSelectionMode(QTableView.ExtendedSelection)

    def set_images(self, images):
        """
        Public method to update the model with new images.
        """
        self._model.set_images(images)
        self._update_columns()

    def resizeEvent(self, event):
        """
        Reimplemented to adjust number of columns when view is resized.
        """
        super().resizeEvent(event)
        self._update_columns()

    def _update_columns(self):
        """
        Calculate and set the number of columns based on the current width.
        Ensures thumbnails fit without horizontal scrolling.
        """
        if not self._delegate:
            return
        width = self.viewport().width()
        if width <= 0:
            return
        # Use delegate size hint width (uniform for all items)
        option = QStyleOptionViewItem()
        delegate_size = self._delegate.sizeHint(option, QModelIndex())
        column_width = delegate_size.width()
        if column_width <= 0:
            return
        # Compute how many columns can fit in the current width
        columns = max(1, width // column_width)
        # Update model's column count
        self._model.set_columns(columns)
        # Update section size to match delegate
        self.horizontalHeader().setDefaultSectionSize(column_width)
        self.verticalHeader().setDefaultSectionSize(delegate_size.height())

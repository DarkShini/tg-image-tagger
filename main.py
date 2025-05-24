import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QSplitter
from PyQt5.QtCore import Qt, QSettings

from database import DatabaseManager
from image_table_view import ImageTableView
from detail_panel import DetailPanel
from controller import AppController

def main():
    app = QApplication(sys.argv)
    # Настройки приложения (имя организации и приложения — произвольное)
    settings = QSettings("MyCompany", "ImageTagger")

    # Инициализация компонентов
    db = DatabaseManager(db_path="image_tags.db")
    image_table = ImageTableView()
    detail_panel = DetailPanel()
    detail_panel.set_tags_available(db.get_all_tags())

    # Собираем главное окно
    window = QMainWindow()
    window.setWindowTitle("Image Tagger")
    splitter = QSplitter(Qt.Horizontal)
    splitter.addWidget(image_table)
    splitter.addWidget(detail_panel)
    window.setCentralWidget(splitter)

    # Контроллер связывает всё вместе
    controller = AppController(image_table, detail_panel, db, settings)
    controller.run()

    # Меню для добавления папки
    menubar = window.menuBar()
    file_menu = menubar.addMenu("File")
    add_folder_action = QAction("Add Folder...", window)
    file_menu.addAction(add_folder_action)

    def on_add_folder():
        folder = QFileDialog.getExistingDirectory(window, "Select Folder")
        if folder:
            # Сохраняем новый путь и добавляем файлы в БД
            controller.folders.append(folder)
            controller.save_folders_to_settings()
            db.add_folder(folder)
            # Перезагружаем список изображений
            controller.images = db.get_all_images()
            image_table.set_images(controller.images)

    add_folder_action.triggered.connect(on_add_folder)

    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

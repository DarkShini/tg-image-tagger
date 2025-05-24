from PyQt5.QtCore import QSettings
from image_table_view import ImageTableModel


class AppController:
    """
    Controller class to connect database, image table view, and detail panel in a PyQt5 application.
    """
    def __init__(self, image_table, detail_panel, database_manager, settings):
        """
        Initialize the AppController.

        Loads the database path, known tags, and previously opened folders.
        If folders are found, it retrieves all images from the database, otherwise it leaves the image list empty.
        
        Parameters:
        - image_table: instance of ImageTableView (the UI component showing images).
        - detail_panel: instance of DetailPanel (the UI component showing image details).
        - database_manager: instance or class of DatabaseManager for DB operations.
        - settings: QSettings instance for saving/loading application settings.
        """
        # References to UI components and helpers
        self.image_table = image_table
        self.detail_panel = detail_panel
        self.db_manager = database_manager
        self.settings = settings
        
        # Path to the image tags database file
        self.db_path = "image_tags.db"
        
        # Load all known tags from the database
        self.all_tags = self.db_manager.get_all_tags()
        
        # Load list of folders from application settings
        self.folders = self.load_folders_from_settings()
        
        # Load images from database only if folders exist (skip on first run)
        if self.folders:
            # Retrieve all images (or filter by tags if needed)
            self.images = self.db_manager.get_all_images()
        else:
            # No folders saved; first run with no images loaded
            self.images = []

    def load_folders_from_settings(self):
        """
        Load the list of previously opened folder paths from QSettings.
        
        Returns:
            A list of folder path strings, or an empty list if none are saved.
        """
        # Retrieve 'folders' value; default to empty list if key is missing
        folders = self.settings.value('folders', [])
        if not folders:
            # No folders found in settings
            return []
        # If stored as string (older versions), convert to single-element list
        if isinstance(folders, str):
            folders = [folders]
        return folders

    def save_folders_to_settings(self):
        """
        Save the current list of folder paths to application settings using QSettings.
        """
        # Store the folder list under key 'folders'
        self.settings.setValue('folders', self.folders)

    def on_image_selected(self, selected, deselected):
        """
        Slot connected to the image table's selectionChanged signal.
        Retrieves the selected image and updates the detail panel to display it.

        Parameters:
        - selected: QItemSelection of newly selected items.
        - deselected: QItemSelection of newly deselected items (unused).
        """

        indexes = selected.indexes()
        # If nothing is selected, do nothing
        if not indexes:
            return
        
        index = indexes[0]
        image = index.model().data(index, ImageTableModel.ImageRole)
        if image:
            self.detail_panel.set_image(image)


    def handle_tag_changed(self, image_id, tag_id, value):
        """
        Handler for when a tag is changed on an image.
        Updates the database and refreshes the detail panel.

        Parameters:
        - image_id: Identifier of the image being tagged.
        - tag_id: Identifier of the tag being changed.
        - value: The new value/state of the tag (e.g. True/False).
        """
        # Update the tag in the database for the given image
        self.db_manager.set_tag(image_id, tag_id, value)
        
        # Reload the updated image data from the database (to get new tag values)
        updated_image = self.db_manager.get_image(image_id)
        
        # Update the detail panel with the refreshed image data
        self.detail_panel.set_image(updated_image)

    def run(self):
        """
        Final setup after initialization, called from main.
        Populates the image table and connects signals between components.
        """
        # Populate the image table view with the loaded images
        self.image_table.set_images(self.images)
        
        # Connect the image selection change signal to its handler
        # This will update the detail panel when a new image is selected.
        self.image_table.selectionModel().selectionChanged.connect(self.on_image_selected)
        
        # Connect the detail panel's tag change signal to the handler
        # Assuming detail_panel has a signal 'tag_changed' with args (image_id, tag_id, value).
        self.detail_panel.tag_changed.connect(self.handle_tag_changed)

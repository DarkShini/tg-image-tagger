from PyQt5.QtCore import QSettings, QItemSelectionModel

class AppController:

    def __init__(self, image_grid, detail_panel, database_manager, settings):
        """
        Initialize the AppController.

        Loads the database path, known tags, and previously opened folders.
        If folders are found, it retrieves all images from the database, otherwise it leaves the image list empty.
     
        """
        # References to UI components and helpers
        self.image_grid = image_grid
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

#TODO potential async
    def on_image_selected(self, list):

        # If nothing is selected, do nothing
        if not list:
            return
        
        image = list[0]
        
        if image:
            self.detail_panel.set_image(image)

#TODO #TODO #TODO - ADAPT FOR IMAGE GIRD DDDDDDD
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
        if value:
            self.db_manager.set_tag(image_id, tag_id, True)
        else: 
            self.db_manager.set_tag(image_id, tag_id, False)
        
        # Reload the updated image data from the database (to get new tag values)
        updated_image = self.db_manager.get_image(image_id)

        # Обновим DetailPanel сразу (если хотим показать новые теги)
        #self.detail_panel.set_image(updated_image)

        # Найдём его в списке controller.images и заменим
        for idx,img in enumerate(self.images):
            if img.id == image_id:
                self.images[idx] = updated_image
                #self.image_grid.update_image(img)
                self.image_grid.update_image(img)
                break


    def select_previous_image(self):
        pass
    # def select_previous_image(self):
    #     idx_list = self.image_grid.list
    #     if not idx_list: 
    #         return
    #     current = idx_list[0]
    #     //prev = self.image_table.model().index(current.row() , current.column()- 1)
    #     if prev.isValid():
    #         self.image_table.selectionModel().select(prev, QItemSelectionModel.ClearAndSelect)
    #         self.on_image_selected(self.image_table.selectionModel().selection(), None)

    def select_next_image(self):
        pass
    # def select_next_image(self):
    #     idx_list = self.image_
    #     if not idx_list: 
    #         return
    #     current = idx_list[0]
    #     nxt = self.image_table.model().index(current.row() , current.column()+ 1)
    #     if nxt.isValid():
    #         self.image_table.selectionModel().select(nxt, QItemSelectionModel.ClearAndSelect)
    #         self.on_image_selected(self.image_table.selectionModel().selection(), None)

    def run(self):
        """
        Final setup after initialization, called from main.
        """
        self.image_grid.set_images(self.images)
        
        # Connect the image selection change signal to its handler
        # This will update the detail panel when a new image is selected.
        self.image_grid.selection_changed.connect(self.on_image_selected)
        
        # Connect the detail panel's tag change signal to the handler
        # Assuming detail_panel has a signal 'tag_changed' with args (image_id, tag_id, value).
        self.detail_panel.tag_changed.connect(self.handle_tag_changed)

import sqlite3
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class TagItem:
    id: int
    name: str

@dataclass
class ImageItem:
    id: int
    filepath: str
    width: int
    height: int
    tags: List[str]

@dataclass
class GroupItem:
    id: int
    name: str
    images: List[ImageItem]

def get_image_size(path: str) -> Tuple[int, int]:
    """
    Get image size (width, height) without external libraries.
    Supports JPEG, PNG, GIF, BMP formats.
    Returns (0, 0) if cannot determine.
    """
    try:
        with open(path, 'rb') as f:
            header = f.read(26)
    except Exception:
        return 0, 0

    # PNG: signature is 8 bytes
    if header[:8] == b'\211PNG\r\n\032\n':
        # IHDR chunk starts at byte 12
        if header[12:16] == b'IHDR':
            width = int.from_bytes(header[16:20], 'big')
            height = int.from_bytes(header[20:24], 'big')
            return width, height

    # JPEG: starts with 0xFFD8
    if header[:2] == b'\xff\xd8':
        try:
            with open(path, 'rb') as f:
                f.read(2)
                b = f.read(1)
                while b and b != b'\xFF':
                    b = f.read(1)
                while b == b'\xFF':
                    marker = f.read(1)
                    if not marker:
                        break
                    if 0xC0 <= marker[0] <= 0xC3:
                        f.read(3)  # skip length and precision
                        h = int.from_bytes(f.read(2), 'big')
                        w = int.from_bytes(f.read(2), 'big')
                        return w, h
                    else:
                        length = int.from_bytes(f.read(2), 'big')
                        f.read(length - 2)
                    b = f.read(1)
        except Exception:
            return 0, 0

    # GIF: first 6 bytes are signature, next 4 bytes are width and height (little-endian)
    if header[:6] in (b'GIF87a', b'GIF89a'):
        width = int.from_bytes(header[6:8], 'little')
        height = int.from_bytes(header[8:10], 'little')
        return width, height

    # BMP: starts with 'BM', width and height at offsets 18 and 22 (little-endian)
    if header[:2] == b'BM':
        width = int.from_bytes(header[18:22], 'little')
        height = int.from_bytes(header[22:26], 'little')
        return width, height

    return 0, 0

class DatabaseManager:
    def __init__(self, db_path: str = 'image_tags.db'):
        """
        Initialize the database manager and create tables if they do not exist.
        """
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = 1")
        self._initialize_db()

    def _initialize_db(self) -> None:
        """
        Create database tables: images, tags, image_tags, groups, group_images.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT UNIQUE,
                width INTEGER,
                height INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_tags (
                image_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (image_id, tag_id),
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_images (
                group_id INTEGER,
                image_id INTEGER,
                PRIMARY KEY (group_id, image_id),
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    def add_folder(self, path: str, extensions: Optional[List[str]] = None) -> None:
        """
        Add all image files from the specified folder to the database.
        Only files with extensions in the provided list are added.
        """
        if extensions is None:
            extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif']
        # Ensure folder path is absolute
        folder = os.path.abspath(path)
        if not os.path.isdir(folder):
            return
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isdir(file_path):
                continue
            ext = os.path.splitext(filename)[1].lower()
            if ext in extensions:
                self._add_image(file_path)

    def _add_image(self, file_path: str) -> None:
        """
        Add a single image to the database with its size.
        """
        abs_path = os.path.abspath(file_path)
        width, height = get_image_size(abs_path)
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO images (filepath, width, height) VALUES (?, ?, ?)",
                (abs_path, width, height)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error adding image {file_path}: {e}")

    def get_tags(self, image_id: int) -> List[str]:
        """
        Return a list of tag names associated with the given image ID.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT t.name
            FROM tags t
            JOIN image_tags it ON t.id = it.tag_id
            WHERE it.image_id = ?
        """, (image_id,))
        rows = cursor.fetchall()
        return [row[0] for row in rows]

    def set_tag(self, image_id: int, tag_id: int, value: bool) -> None:
        """
        Add or remove a tag from an image.
        If value is True, add the tag; if False, remove the tag.
        """
        cursor = self.conn.cursor()
        if value:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO image_tags (image_id, tag_id) VALUES (?, ?)",
                    (image_id, tag_id)
                )
                self.conn.commit()
            except sqlite3.Error as e:
                print(f"Error adding tag: {e}")
        else:
            cursor.execute(
                "DELETE FROM image_tags WHERE image_id = ? AND tag_id = ?",
                (image_id, tag_id)
            )
            self.conn.commit()

    def get_or_create_tag(self, name: str) -> TagItem:
        """
        Get a tag by name, or create it if it doesn't exist. Returns a TagItem.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM tags WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return TagItem(id=row[0], name=row[1])
        cursor.execute("INSERT INTO tags (name) VALUES (?)", (name,))
        self.conn.commit()
        return TagItem(id=cursor.lastrowid, name=name)

    def get_all_tags(self) -> List[TagItem]:
        """
        Return a list of all tags in the database.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM tags")
        rows = cursor.fetchall()
        return [TagItem(id=row[0], name=row[1]) for row in rows]

    def get_all_images(self) -> List[ImageItem]:
        """
        Return a list of all images, including their tags.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, filepath, width, height FROM images")
        images: List[ImageItem] = []
        for img_id, filepath, width, height in cursor.fetchall():
            tags = self.get_tags(img_id)
            images.append(ImageItem(id=img_id, filepath=filepath, width=width, height=height, tags=tags))
        return images

    def create_group(self, name: str) -> int:
        """
        Create a new group with the given name, or return existing group ID if name exists.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM groups WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor.execute("INSERT INTO groups (name) VALUES (?)", (name,))
        self.conn.commit()
        return cursor.lastrowid

    def add_to_group(self, group_id: int, image_id: int) -> None:
        """
        Add an image to a group if the group has fewer than 10 images.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM group_images WHERE group_id = ?",
            (group_id,)
        )
        count = cursor.fetchone()[0]
        if count >= 10:
            raise ValueError("Group already has 10 images (maximum reached).")
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO group_images (group_id, image_id) VALUES (?, ?)",
                (group_id, image_id)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error adding image to group: {e}")

    def remove_from_group(self, group_id: int, image_id: int) -> None:
        """
        Remove an image from a group.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM group_images WHERE group_id = ? AND image_id = ?",
            (group_id, image_id)
        )
        self.conn.commit()

    def get_group_images(self, group_id: int) -> List[ImageItem]:
        """
        Return a list of ImageItems belonging to the specified group.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT i.id, i.filepath, i.width, i.height
            FROM images i
            JOIN group_images gi ON i.id = gi.image_id
            WHERE gi.group_id = ?
        """, (group_id,))
        images: List[ImageItem] = []
        for img_id, filepath, width, height in cursor.fetchall():
            tags = self.get_tags(img_id)
            images.append(ImageItem(id=img_id, filepath=filepath, width=width, height=height, tags=tags))
        return images

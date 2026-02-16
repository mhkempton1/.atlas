import os
import glob
from typing import List, Optional
from core.config import settings

class OneDriveService:
    """
    Service for interacting with local OneDrive sync folder to load knowledge documents.
    """
    def __init__(self):
        self.root_path = settings.ONEDRIVE_ROOT_PATH

    def list_knowledge_files(self, folder_name: str) -> List[str]:
        """
        List all .md files in a specific knowledge folder.
        """
        folder_path = os.path.join(self.root_path, folder_name)
        if not os.path.exists(folder_path):
            print(f"OneDrive folder not found: {folder_path}")
            return []
        
        return glob.glob(os.path.join(folder_path, "**", "*.md"), recursive=True)

    def read_knowledge_file(self, file_path: str) -> Optional[str]:
        """
        Read content of a knowledge file.
        """
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading OneDrive file {file_path}: {e}")
            return None

onedrive_service = OneDriveService()

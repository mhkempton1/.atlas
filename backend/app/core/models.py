from pydantic import BaseModel, Field
from typing import List, Optional

# Mirroring Altimeter Schema in Atlas for Type Safety
class ExternalKeys(BaseModel):
    quickbooks_customer_id: Optional[str] = None
    quickbooks_project_id: Optional[str] = None
    exaktime_project_id: Optional[str] = None

class AltimeterProject(BaseModel):
    id: str
    name: str
    status: str
    keys: ExternalKeys
    
    def is_valid_for_atlas(self) -> bool:
        """
        Atlas needs specific binding keys to link emails.
        """
        return self.keys.quickbooks_project_id is not None

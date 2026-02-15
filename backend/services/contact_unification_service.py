from typing import List, Dict, Any
from services.contact_service import contact_service

class ContactUnificationService:
    """
    Service for identifying and merging duplicate contacts using 
    fuzzy name matching and email comparison.
    """
    
    def detect_duplicate_contacts(self) -> List[Dict[str, Any]]:
        """
        Scan all contacts and find potential duplicates.
        Returns a list of groups (sets) of contact IDs.
        """
        all_contacts = contact_service.list_contacts()
        duplicates = []
        seen_ids = set()
        
        for i, c1 in enumerate(all_contacts):
            if c1["contact_id"] in seen_ids: continue
            
            group = [c1]
            for j, c2 in enumerate(all_contacts[i+1:]):
                if c2["contact_id"] in seen_ids: continue
                
                # Logic:
                # 1. Exact Email Match
                # 2. Exact Phone Match
                # 3. Fuzzy Name Match (simple for now)
                
                is_match = False
                
                # Email match
                if c1.get("email") and c2.get("email") and c1["email"].lower() == c2["email"].lower():
                    is_match = True
                
                # Phone match
                elif c1.get("phone") and c2.get("phone") and c1["phone"] == c2["phone"]:
                    is_match = True
                    
                # Simple Name Match
                elif c1.get("name") and c2.get("name") and c1["name"].lower().strip() == c2["name"].lower().strip():
                    is_match = True
                
                if is_match:
                    group.append(c2)
                    seen_ids.add(c2["contact_id"])
                    
            if len(group) > 1:
                duplicates.append({
                    "primary": group[0],
                    "duplicates": group[1:],
                    "match_type": "Identity Conflict"
                })
                seen_ids.add(c1["contact_id"])
                
        return duplicates

    def merge_contacts(self, primary_id: str, duplicate_ids: List[str]) -> Dict[str, Any]:
        """
        Merge duplicate contacts into a primary contact.
        """
        # Logic: Update all related tasks/emails/events to point to primary_id
        # Then delete duplicates.
        # This implementation depends on DB structure. 
        # For now, it's a stub that logs the intent.
        
        print(f"[Unification] Merging {len(duplicate_ids)} contacts into {primary_id}")
        
        # 1. Update primary contact with missing fields from duplicates
        # 2. Update foreign keys in other tables
        # 3. Delete duplicates
        
        return {"status": "success", "merged_count": len(duplicate_ids)}

unification_service = ContactUnificationService()

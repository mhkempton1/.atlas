import os
import re
import shutil
import glob
import datetime
from typing import List, Dict, Optional, Tuple
from services.activity_service import activity_service
from database.database import get_db
from database.models import DocumentComment
from datetime import datetime as dt

class DocumentControlService:
    def __init__(self):
        self.root_path = r"c:\Users\mhkem\OneDrive\Documents\Davis Projects OneDrive"
        self.sections = ["GUIDELINES", "SKILLS", "TRAINING"]

    def _get_version(self, filename: str) -> str:
        """Extracts version from filename like file.LOCKED-v1.2.md"""
        match = re.search(r'v(\d+\.\d+)', filename)
        return match.group(1) if match else "1.0"

    def _increment_version(self, version: str) -> str:
        try:
            major, minor = map(int, version.split('.'))
            return f"{major}.{minor + 1}"
        except:
            return "1.1"

    def _path_component(self, path: str) -> str:
        return os.path.normpath(path)

    def _validate_path(self, path: str) -> str:
        """
        Security check to ensure path is within the allowed root directory.
        Prevents Path Traversal attacks.
        """
        abs_path = os.path.abspath(path)
        abs_root = os.path.abspath(self.root_path)

        # Check if abs_path starts with abs_root
        if not os.path.commonpath([abs_path, abs_root]) == abs_root:
            raise ValueError(f"Access denied: Path '{path}' is outside the allowed directory.")

        return abs_path

    # --- Draft Management ---

    def create_draft(self, title: str, content: str, section: str = "GUIDELINES") -> Dict[str, str]:
        """Creates a new draft file."""
        if section not in self.sections:
             raise ValueError(f"Invalid section: {section}")
             
        # Sanitize filename
        safe_title = re.sub(r'[^\w\s-]', '', title.lower()).strip().replace(' ', '-')
        filename = f"{safe_title}.DRAFT.md"
        
        draft_dir = os.path.join(self.root_path, section, "DRAFTS")
        os.makedirs(draft_dir, exist_ok=True)
        
        file_path = os.path.join(draft_dir, filename)
        
        if os.path.exists(file_path):
            raise FileExistsError("Draft with this title already exists")
            
        # Add basic frontmatter if missing
        if not content.startswith("---"):
            header = f"""---
document_state: DRAFT
created: {datetime.date.today()}
author: Atlas
---

# {title}

"""
            content = header + content
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return {"filename": filename, "path": file_path, "status": "created"}

    def save_draft(self, path: str, content: str) -> Dict[str, str]:
        """Updates an existing draft."""
        self._validate_path(path)

        if not os.path.exists(path):
            raise FileNotFoundError("Draft file not found")
            
        # Security check: Ensure we are editing a DRAFT
        if ".DRAFT.md" not in path:
            raise ValueError("Can only edit DRAFT files directly")
            
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return {"path": path, "status": "saved"}
        
    def delete_draft(self, path: str) -> Dict[str, str]:
        """Deletes a draft."""
        self._validate_path(path)

        if not os.path.exists(path):
             raise FileNotFoundError("Draft not found")
        
        if ".DRAFT.md" not in path:
             raise ValueError("Can only delete DRAFT files")
             
        os.remove(path)
        return {"path": path, "status": "deleted"}

    def get_document_content(self, path: str) -> str:
        """Reads document content"""
        self._validate_path(path)

        if not os.path.exists(path):
            return ""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    # --- Listing & Promotion ---

    def get_all_documents(self) -> Dict[str, List[Dict]]:
        """
        Scans DRAFTS, REVIEW, LOCKED, ARCHIVE folders in all managed sections.
        Returns grouped by state.
        """
        docs = {
            "draft": [],
            "review": [],
            "locked": [],
            "archive": []
        }

        for section in self.sections:
            base_dir = os.path.join(self.root_path, section)
            if not os.path.exists(base_dir):
                continue
            
            # Scan DRAFTS
            draft_dir = os.path.join(base_dir, "DRAFTS")
            if os.path.exists(draft_dir):
                for f in glob.glob(os.path.join(draft_dir, "*.DRAFT.md")):
                    docs["draft"].append({
                        "id": os.path.basename(f),
                        "filename": os.path.basename(f),
                        "path": f,
                        "section": section,
                        "state": "DRAFT",
                        "modified": os.path.getmtime(f)
                    })

            # Scan REVIEW
            review_dir = os.path.join(base_dir, "REVIEW")
            if os.path.exists(review_dir):
                for f in glob.glob(os.path.join(review_dir, "*.REVIEW-v*.md")):
                     docs["review"].append({
                        "id": os.path.basename(f),
                        "filename": os.path.basename(f),
                        "path": f,
                        "section": section,
                        "state": "REVIEW",
                        "version": self._get_version(os.path.basename(f)),
                        "modified": os.path.getmtime(f)
                    })

            # Scan LOCKED
            locked_dir = os.path.join(base_dir, "LOCKED")
            if os.path.exists(locked_dir):
                for f in glob.glob(os.path.join(locked_dir, "*.LOCKED-v*.md")):
                     docs["locked"].append({
                        "id": os.path.basename(f),
                        "filename": os.path.basename(f),
                        "path": f,
                        "section": section,
                        "state": "LOCKED",
                        "version": self._get_version(os.path.basename(f)),
                        "modified": os.path.getmtime(f)
                    })

        # Sort by Date
        for key in docs:
            docs[key].sort(key=lambda x: x['modified'], reverse=True)

        return docs

    def promote_to_review(self, draft_path: str) -> dict:
        self._validate_path(draft_path)

        if not os.path.exists(draft_path):
            raise FileNotFoundError("Draft file not found")
        
        dir_name = os.path.dirname(draft_path) # .../DRAFTS
        base_dir = os.path.dirname(dir_name)   # .../GUIDELINES
        filename = os.path.basename(draft_path)
        base_name = filename.replace('.DRAFT.md', '')

        # Determine Version (Check for existing LOCKED)
        version = "1.0"
        locked_dir = os.path.join(base_dir, "LOCKED")
        if os.path.exists(locked_dir):
            existing_locked = glob.glob(os.path.join(locked_dir, f"{base_name}.LOCKED-v*.md"))
            if existing_locked:
                # Find highest version
                versions = [self._get_version(os.path.basename(f)) for f in existing_locked]
                # Simple max logic (can be improved)
                highest = max(versions) 
                version = self._increment_version(highest)

        review_dir = os.path.join(base_dir, "REVIEW")
        os.makedirs(review_dir, exist_ok=True)
        
        new_filename = f"{base_name}.REVIEW-v{version}.md"
        review_path = os.path.join(review_dir, new_filename)

        # Copy and Add Metadata
        with open(draft_path, 'r', encoding='utf-8') as src:
            content = src.read()

        # Strip existing frontmatter if any
        content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

        header = f"""---
document_state: REVIEW
version: {version}
date: {datetime.date.today()}
approver: Pending
---

"""
        with open(review_path, 'w', encoding='utf-8') as dst:
            dst.write(header + content)

        activity_service.log_activity(
            type="doc",
            action="Promotion",
            target=filename,
            details=f"Document promoted from DRAFT to REVIEW: {filename}"
        )

        # Remove the draft file to prevent duplicates
        os.remove(draft_path)

        return {"status": "success", "new_path": review_path, "version": version}

    def lock_document(self, review_path: str, approver: str) -> dict:
        self._validate_path(review_path)

        if not os.path.exists(review_path):
            raise FileNotFoundError("Review file not found")

        dir_name = os.path.dirname(review_path) # .../REVIEW
        base_dir = os.path.dirname(dir_name)    # .../GUIDELINES
        filename = os.path.basename(review_path)
        
        # Extract version and base name
        # Ex: name.REVIEW-v1.1.md
        version = self._get_version(filename)
        base_name = re.sub(r'\.REVIEW-v.*\.md$', '', filename)

        locked_dir = os.path.join(base_dir, "LOCKED")
        archive_dir = os.path.join(base_dir, "ARCHIVE")
        os.makedirs(locked_dir, exist_ok=True)
        os.makedirs(archive_dir, exist_ok=True)

        new_filename = f"{base_name}.LOCKED-v{version}.md"
        locked_path = os.path.join(locked_dir, new_filename)

        # 1. Archive Old Locked Versions
        existing_locked = glob.glob(os.path.join(locked_dir, f"{base_name}.LOCKED-v*.md"))
        for old_file in existing_locked:
            old_ver = self._get_version(os.path.basename(old_file))
            archive_name = f"{base_name}.ARCHIVE-v{old_ver}-{datetime.date.today().strftime('%Y%m%d')}.md"
            shutil.move(old_file, os.path.join(archive_dir, archive_name))

        # 2. Create Locked File with Updated Metadata
        with open(review_path, 'r', encoding='utf-8') as src:
            content = src.read()
            
        # Update metadata
        content = re.sub(r'document_state: REVIEW', 'document_state: LOCKED', content)
        content = re.sub(r'approver: Pending', f'approver: {approver}', content)

        with open(locked_path, 'w', encoding='utf-8') as dst:
            dst.write(content)

        # 3. Delete Review File
        os.remove(review_path)

        activity_service.log_activity(
            type="doc",
            action="Lock",
            target=filename,
            details=f"Document locked as version {version} by {approver}: {filename}"
        )

        return {"status": "success", "new_path": locked_path}

    def import_to_review(self, source_path: str, section: str = "GUIDELINES") -> dict:
        """Copies an external document into the controlled REVIEW system."""
        if not os.path.exists(source_path):
            raise FileNotFoundError("Source document not found")
        
        filename = os.path.basename(source_path)
        base_name = filename.replace('.md', '').replace('.DRAFT', '')
        
        version = "1.0"
        review_dir = os.path.join(self.root_path, section, "REVIEW")
        os.makedirs(review_dir, exist_ok=True)
        
        new_filename = f"{base_name}.REVIEW-v{version}.md"
        review_path = os.path.join(review_dir, new_filename)
        
        with open(source_path, 'r', encoding='utf-8') as src:
            content = src.read()
            
        # Strip existing frontmatter
        content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
        
        header = f"""---
document_state: REVIEW
version: {version}
date: {datetime.date.today()}
approver: Pending
source_origin: {source_path}
---

"""
        with open(review_path, 'w', encoding='utf-8') as dst:
            dst.write(header + content)
            
        activity_service.log_activity(
            type="doc",
            action="Import & Promote",
            target=filename,
            details=f"Document imported from Knowledge Base and promoted to REVIEW: {filename}"
        )
        
        return {"status": "success", "new_path": review_path, "version": version}

    # --- Comment Management ---
    
    def add_comment(self, document_path: str, author: str, content: str, comment_type: str = "general") -> dict:
        """Add a comment to a document."""
        self._validate_path(document_path)

        db = next(get_db())
        try:
            comment = DocumentComment(
                document_path=document_path,
                author=author,
                content=content,
                comment_type=comment_type,
                is_resolved=False
            )
            db.add(comment)
            db.commit()
            db.refresh(comment)
            
            activity_service.log_activity(
                type="doc",
                action=f"Comment ({comment_type})",
                target=os.path.basename(document_path),
                details=f"{author} added {comment_type}: {content[:50]}..."
            )
            
            return {
                "status": "success",
                "comment_id": comment.comment_id,
                "created_at": comment.created_at.isoformat()
            }
        finally:
            db.close()
    
    def get_comments(self, document_path: str) -> List[Dict]:
        """Get all comments for a document."""
        self._validate_path(document_path)

        db = next(get_db())
        try:
            comments = db.query(DocumentComment).filter(
                DocumentComment.document_path == document_path
            ).order_by(DocumentComment.created_at.desc()).all()
            
            return [{
                "comment_id": c.comment_id,
                "author": c.author,
                "content": c.content,
                "comment_type": c.comment_type,
                "is_resolved": c.is_resolved,
                "resolved_by": c.resolved_by,
                "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
                "created_at": c.created_at.isoformat()
            } for c in comments]
        finally:
            db.close()
    
    def resolve_comment(self, comment_id: int, resolver: str) -> dict:
        """Mark a comment as resolved."""
        db = next(get_db())
        try:
            comment = db.query(DocumentComment).filter(
                DocumentComment.comment_id == comment_id
            ).first()
            
            if not comment:
                raise ValueError("Comment not found")
            
            comment.is_resolved = True
            comment.resolved_by = resolver
            comment.resolved_at = dt.now()
            db.commit()
            
            activity_service.log_activity(
                type="doc",
                action="Comment Resolved",
                target=os.path.basename(comment.document_path),
                details=f"{resolver} resolved {comment.comment_type} by {comment.author}"
            )
            
            return {"status": "success", "resolved_at": comment.resolved_at.isoformat()}
        finally:
            db.close()
    
    def get_review_summary(self, document_path: str) -> dict:
        """Get review summary showing unresolved issues count."""
        self._validate_path(document_path)

        db = next(get_db())
        try:
            total_comments = db.query(DocumentComment).filter(
                DocumentComment.document_path == document_path
            ).count()
            
            unresolved_issues = db.query(DocumentComment).filter(
                DocumentComment.document_path == document_path,
                DocumentComment.comment_type == "issue",
                DocumentComment.is_resolved == False
            ).count()
            
            unresolved_total = db.query(DocumentComment).filter(
                DocumentComment.document_path == document_path,
                DocumentComment.is_resolved == False
            ).count()
            
            return {
                "total_comments": total_comments,
                "unresolved_issues": unresolved_issues,
                "unresolved_total": unresolved_total,
                "can_sign_off": unresolved_issues == 0
            }
        finally:
            db.close()

    def demote_to_draft(self, review_path: str) -> dict:
        """Sends a document back to DRAFT status."""
        self._validate_path(review_path)

        if not os.path.exists(review_path):
             raise FileNotFoundError("Review file not found")

        # 1. Check for Comments (Constraint)
        db = next(get_db())
        try:
            comment_count = db.query(DocumentComment).filter(
                DocumentComment.document_path == review_path
            ).count()
            if comment_count == 0:
                raise ValueError("Cannot send back to Draft without comments explaining why.")
        finally:
            db.close()

        dir_name = os.path.dirname(review_path) # .../REVIEW
        base_dir = os.path.dirname(dir_name)    # .../GUIDELINES
        filename = os.path.basename(review_path)
        base_name = re.sub(r'\.REVIEW-v.*\.md$', '', filename)

        draft_dir = os.path.join(base_dir, "DRAFTS")
        os.makedirs(draft_dir, exist_ok=True)
        
        draft_filename = f"{base_name}.DRAFT.md"
        draft_path = os.path.join(draft_dir, draft_filename)

        # 2. Re-create Draft if it doesn't exist (using content from Review)
        # We always overwrite or ensure the draft reflects the review copy being rejected?
        # A safer bet is: if draft exists, keep it but maybe update it? 
        # For now, let's assume we are "Unlocking" for edit, so we overwrite the draft with the review content
        # so they can edit the version they submitted.
        
        with open(review_path, 'r', encoding='utf-8') as src:
            content = src.read()

        # Update metadata back to DRAFT
        content = re.sub(r'document_state: REVIEW', 'document_state: DRAFT', content)
        # Remove version/approver lines if we want simple draft, or keep them for history?
        # Let's clean it up to look like a draft.
        content = re.sub(r'version: .*\n', '', content)
        content = re.sub(r'approver: .*\n', '', content)
        content = re.sub(r'date: .*\n', f'created: {datetime.date.today()}\n', content)

        with open(draft_path, 'w', encoding='utf-8') as dst:
            dst.write(content)

        # 3. Delete Review File
        os.remove(review_path)

        activity_service.log_activity(
            type="doc",
            action="Demotion",
            target=filename,
            details=f"Document sent back to DRAFT: {filename}"
        )

        return {"status": "success", "new_path": draft_path}

document_control_service = DocumentControlService()

import os
import glob
import yaml
import re
import hashlib
from typing import List, Dict, Optional, Any
from datetime import datetime
from core.config import settings
from services.search_service import search_service
from integrations.onedrive_service import onedrive_service

class KnowledgeService:
    """
    Service to index, search, and retrieve knowledge documents 
    from Obsidian and OneDrive.
    """
    
    def __init__(self):
        self.sources = {
            "obsidian": settings.OBSIDIAN_KNOWLEDGE_PATH,
            "onedrive": settings.ONEDRIVE_ROOT_PATH
        }

    def _parse_frontmatter(self, content: str) -> Dict:
        """Extract YAML frontmatter from markdown content."""
        meta = {}
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if match:
            try:
                meta = yaml.safe_load(match.group(1))
            except Exception as e:
                print(f"YAML Parse Error: {e}")
        return meta if isinstance(meta, dict) else {}

    def _chunk_document(self, content: str) -> List[Dict[str, str]]:
        """Chunk document by H2 headers."""
        chunks = []
        parts = re.split(r'\n##\s+', content)
        intro = parts[0].strip()
        if intro:
            chunks.append({"header": "Introduction", "content": intro})
        for part in parts[1:]:
            lines = part.split('\n', 1)
            header = lines[0].strip()
            body = lines[1].strip() if len(lines) > 1 else ""
            if body:
                chunks.append({"header": header, "content": body})
        return chunks

    def load_skills_from_onedrive(self) -> Dict[str, Any]:
        """Load SKILLS documents from OneDrive, chunk them, and index in ChromaDB."""
        skills_folder = settings.ONEDRIVE_SKILLS_PATH
        files = onedrive_service.list_knowledge_files(skills_folder)
        all_chunks = []
        for file_path in files:
            content = onedrive_service.read_knowledge_file(file_path)
            if not content: continue
            filename = os.path.basename(file_path)
            meta = self._parse_frontmatter(content)
            title = meta.get('title') or filename.replace('.md', '')
            mtime = os.path.getmtime(file_path)
            chunks = self._chunk_document(content)
            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    "id": f"skill:{filename}:{i}",
                    "text": f"Skill: {title}\nSection: {chunk['header']}\n\n{chunk['content']}",
                    "metadata": {
                        "filename": filename,
                        "title": title,
                        "section_header": chunk['header'],
                        "category": "SKILL",
                        "last_modified": mtime,
                        "loaded_at": datetime.now().isoformat()
                    }
                })
        if all_chunks:
            search_service.skills_collection.upsert(
                ids=[c["id"] for c in all_chunks],
                documents=[c["text"] for c in all_chunks],
                metadatas=[c["metadata"] for c in all_chunks]
            )
        return {"status": "success", "indexed_chunks": len(all_chunks)}

    def load_guidelines_from_onedrive(self) -> Dict[str, Any]:
        """Load GUIDELINES documents from OneDrive and index."""
        folder = settings.ONEDRIVE_GUIDELINES_PATH
        files = onedrive_service.list_knowledge_files(folder)
        all_docs = []
        for file_path in files:
            content = onedrive_service.read_knowledge_file(file_path)
            if not content: continue
            filename = os.path.basename(file_path)
            meta = self._parse_frontmatter(content)
            mtime = os.path.getmtime(file_path)
            all_docs.append({
                "id": f"guideline:{filename}",
                "text": content,
                "metadata": {
                    "filename": filename,
                    "title": meta.get('title') or filename.replace('.md', ''),
                    "category": "GUIDELINE",
                    "last_modified": mtime,
                    "loaded_at": datetime.now().isoformat()
                }
            })
        if all_docs:
            search_service.guidelines_collection.upsert(
                ids=[d["id"] for d in all_docs],
                documents=[d["text"] for d in all_docs],
                metadatas=[d["metadata"] for d in all_docs]
            )
        return {"status": "success", "indexed_docs": len(all_docs)}

    def load_templates_from_onedrive(self) -> Dict[str, Any]:
        """Load TEMPLATES documents from OneDrive and index."""
        folder = settings.ONEDRIVE_TEMPLATES_PATH
        files = onedrive_service.list_knowledge_files(folder)
        all_docs = []
        for file_path in files:
            content = onedrive_service.read_knowledge_file(file_path)
            if not content: continue
            filename = os.path.basename(file_path)
            meta = self._parse_frontmatter(content)
            mtime = os.path.getmtime(file_path)
            all_docs.append({
                "id": f"template:{filename}",
                "text": content,
                "metadata": {
                    "filename": filename,
                    "title": meta.get('title') or filename.replace('.md', ''),
                    "category": "TEMPLATE",
                    "last_modified": mtime,
                    "loaded_at": datetime.now().isoformat()
                }
            })
        if all_docs:
            search_service.templates_collection.upsert(
                ids=[d["id"] for d in all_docs],
                documents=[d["text"] for d in all_docs],
                metadatas=[d["metadata"] for d in all_docs]
            )
        return {"status": "success", "indexed_docs": len(all_docs)}

    def search_knowledge(self, query: str, collection: str = "skills", top_k: int = 5) -> List[Dict[str, Any]]:
        """Semantic search across knowledge collections."""
        return search_service.search(query, collection_name=collection, n_results=top_k)

    def search_all_knowledge(self, query: str, top_k: int = 3) -> Dict[str, List[Dict]]:
        """Aggregated search across all collections."""
        return {
            "skills": self.search_knowledge(query, "skills", top_k),
            "guidelines": self.search_knowledge(query, "guidelines", top_k),
            "templates": self.search_knowledge(query, "templates", top_k),
            "general": self.search_knowledge(query, "knowledge", top_k)
        }

    def sync_knowledge(self) -> Dict[str, Any]:
        """Smart sync: only re-index changed files."""
        stats = {
            "skills": self.load_skills_from_onedrive(),
            "guidelines": self.load_guidelines_from_onedrive(),
            "templates": self.load_templates_from_onedrive()
        }
        return {"status": "success", "details": stats}

    # Legacy scan methods for Obsidian
    def _scan_directory(self, root_path: str, source_name: str) -> List[Dict]:
        results = []
        if not os.path.exists(root_path): return results
        for root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.endswith('.md'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, root_path)
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            raw_content = f.read()
                            meta = self._parse_frontmatter(raw_content)
                            title = meta.get('title')
                            if not title:
                                for line in raw_content.split('\n'):
                                    if line.startswith('# '):
                                        title = line.replace('# ', '').strip(); break
                            if not title: title = file.replace('.md', '')
                            category = meta.get('category') or rel_path.split(os.sep)[0]
                        results.append({
                            "id": f"{source_name}:{rel_path.replace(os.sep, '/')}",
                            "title": title,
                            "filename": file,
                            "path": rel_path.replace(os.sep, '/'),
                            "source": source_name,
                            "full_path": full_path,
                            "category": category,
                            "content": raw_content
                        })
                    except Exception as e: print(f"Error: {e}")
        return results

    def reindex_all(self):
        """Perform full reindex of all sources."""
        docs = self._scan_directory(self.sources["obsidian"], "Knowledge Base")
        search_service.index_knowledge_batch(docs)
        self.sync_knowledge()

knowledge_service = KnowledgeService()

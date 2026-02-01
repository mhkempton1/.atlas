import os
import glob
import yaml
import re
from typing import List, Dict, Optional, Any
from core.config import settings
from services.search_service import search_service

class KnowledgeService:
    """
    Service to index, search, and retrieve knowledge documents 
    from Obsidian and OneDrive.
    """
    
    def __init__(self):
        self.sources = {
            "obsidian": settings.OBSIDIAN_KNOWLEDGE_PATH,
            "onedrive": settings.ONEDRIVE_PATH
        }

    def _parse_frontmatter(self, content: str) -> Dict:
        """Extract YAML frontmatter from markdown content."""
        meta = {}
        # Simple frontmatter regex
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if match:
            try:
                meta = yaml.safe_load(match.group(1))
            except Exception as e:
                print(f"YAML Parse Error: {e}")
        return meta if isinstance(meta, dict) else {}

    def _scan_directory(self, root_path: str, source_name: str) -> List[Dict]:
        """Recursively scan for markdown files."""
        results = []
        if not os.path.exists(root_path):
            return results

        for root, dirs, files in os.walk(root_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.endswith('.md'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, root_path)
                    
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            raw_content = f.read() # Read all for indexing
                            
                            # 1. Parse Frontmatter
                            meta = self._parse_frontmatter(raw_content)
                            
                            # 2. Extract Title (Frontmatter > H1 > Filename)
                            title = meta.get('title')
                            
                            if not title:
                                lines = raw_content.split('\n')
                                for line in lines:
                                    if line.startswith('# '):
                                        title = line.replace('# ', '').strip()
                                        break
                            
                            if not title:
                                title = file.replace('.md', '').replace('.DRAFT', '')

                            # 3. Categorization & Grouping
                            category = meta.get('category') or meta.get('type')
                            group = meta.get('group') or meta.get('folder')
                            
                            # If no category, infer from path
                            if not category:
                                parts = rel_path.split(os.sep)
                                if len(parts) > 1:
                                    category = parts[0]
                                else:
                                    category = source_name.replace('OneDrive/', '')

                        results.append({
                            "id": f"{source_name}:{rel_path.replace(os.sep, '/')}",
                            "title": title,
                            "filename": file,
                            "path": rel_path.replace(os.sep, '/'),
                            "source": source_name,
                            "full_path": full_path,
                            "category": category,
                            "group": group,
                            "is_draft": ".DRAFT." in file or "DRAFTS" in root,
                            "priority": meta.get('priority', 'medium'),
                            "preview": raw_content[:200].replace('#', '').strip() + "...",
                            "content": raw_content # Included for indexing pass
                        })
                    except Exception as e:
                        print(f"Error reading {file}: {e}")
                        continue
        return results

    def get_all_documents(self) -> List[Dict]:
        """Aggregate documents from all sources with deduplication."""
        all_docs = []
        onedrive_subfolders = ["GUIDELINES", "SKILLS", "TRAINING"]
        
        # 1. Collect
        all_docs.extend(self._scan_directory(self.sources["obsidian"], "Knowledge Base"))
        for sub in onedrive_subfolders:
            path = os.path.join(self.sources["onedrive"], sub)
            all_docs.extend(self._scan_directory(path, f"OneDrive/{sub}"))

        # 2. Deduplicate
        deduped = {}
        for doc in all_docs:
            key = doc['title'].lower().strip()
            if key not in deduped or self._get_merit(doc) > self._get_merit(deduped[key]):
                deduped[key] = doc
        
        # Return sorted list (without full content bloating the list response)
        final_list = []
        for d in deduped.values():
            clean_doc = d.copy()
            if "content" in clean_doc: del clean_doc["content"]
            final_list.append(clean_doc)

        return sorted(final_list, key=lambda x: (x['category'] or '', x['title']))

    def reindex_knowledge(self) -> Dict[str, Any]:
        """Manually trigger a full reindex using batching."""
        print("[KnowledgeService] Reindexing knowledge base...")
        all_docs = []
        onedrive_subfolders = ["GUIDELINES", "SKILLS", "TRAINING"]
        
        all_docs.extend(self._scan_directory(self.sources["obsidian"], "Knowledge Base"))
        for sub in onedrive_subfolders:
            path = os.path.join(self.sources["onedrive"], sub)
            all_docs.extend(self._scan_directory(path, f"OneDrive/{sub}"))

        # Deduplicate
        deduped = {}
        for doc in all_docs:
            key = doc['title'].lower().strip()
            if key not in deduped or self._get_merit(doc) > self._get_merit(deduped[key]):
                deduped[key] = doc
        
        docs_to_index = list(deduped.values())
        success = search_service.index_knowledge_batch(docs_to_index)
        
        return {
            "status": "success" if success else "failed",
            "count": len(docs_to_index),
            "message": f"Successfully indexed {len(docs_to_index)} documents" if success else "Indexing failed"
        }

    def _get_merit(self, d) -> int:
        score = 0
        if d['source'] == "Knowledge Base": score += 10
        if not d['is_draft']: score += 5
        return score

    def get_document_content(self, doc_path: str) -> Optional[str]:
        """Retrieve full content of a document."""
        if os.path.exists(doc_path):
             with open(doc_path, 'r', encoding='utf-8') as f:
                  return f.read()
        return None

knowledge_service = KnowledgeService()

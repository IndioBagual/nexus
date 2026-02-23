import os
from datetime import datetime

from slugify import slugify  # pip install python-slugify

from nexus.domain.entities import Note
from nexus.domain.ports import NoteRepository


class MarkdownFileAdapter(NoteRepository):
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        os.makedirs(root_dir, exist_ok=True)

    def save(self, note: Note) -> str:
        safe_title = slugify(note.title) if note.title else "untitled"
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}_{safe_title}.md"
        filepath = os.path.join(self.root_dir, filename)

        frontmatter = f"""---
id: {note.id}
type: note
created_at: {note.created_at.isoformat()}
tags: {note.tags}
---
"""
        content = f"{frontmatter}\n# {note.title}\n\n{note.content}"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath

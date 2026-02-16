import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class Skill:
    name: str
    description: str
    prompt: str
    category: str = "general"

class SkillManager:
    """Manages loading and retrieving skills (prompts)."""
    
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills: Dict[str, Skill] = {}
        self._load_skills()
    
    def _load_skills(self):
        """Load skills from SKILL.md files."""
        if not self.skills_dir.exists():
            return
            
        # Walk through all directories
        for root, dirs, files in os.walk(self.skills_dir):
            if "SKILL.md" in files:
                skill_path = Path(root) / "SKILL.md"
                self._parse_skill(skill_path)
    
    def _parse_skill(self, path: Path):
        """Parse a SKILL.md file."""
        try:
            content = path.read_text(encoding="utf-8")
            
            # Simple frontmatter parsing
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter_raw = parts[1]
                    body = parts[2].strip()
                    
                    metadata = yaml.safe_load(frontmatter_raw)
                    name = metadata.get("name", path.parent.name)
                    description = metadata.get("description", "No description provided.")
                    
                    self.skills[name] = Skill(
                        name=name,
                        description=description,
                        prompt=body,
                        category=path.parent.parent.name  # e.g. superpowers
                    )
        except Exception as e:
            print(f"Error loading skill {path}: {e}")

    def get_skill(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)
        
    def list_skills(self) -> List[Skill]:
        return list(self.skills.values())

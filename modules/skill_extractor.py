import json
import os
import re
from typing import List, Set

class SkillExtractor:
    """
    Extracts skills from text based on a predefined skills taxonomy in data/skills.json.
    """
    def __init__(self, skills_db_path: str = None):
        if skills_db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            skills_db_path = os.path.join(base_dir, "data", "skills.json")
            
        self.skills_db_path = skills_db_path
        self.skills_list = self._load_skills()
        self._compiled_patterns = self._compile_skill_patterns()

    def _load_skills(self) -> List[str]:
        """Loads skills list from JSON file."""
        try:
            if not os.path.exists(self.skills_db_path):
                raise FileNotFoundError(f"Skills database not found at {self.skills_db_path}")
            with open(self.skills_db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("skills", [])
        except Exception as e:
            print(f"Warning: Failed to load skills database: {e}")
            return []

    def _compile_skill_patterns(self) -> List[tuple]:
        """
        Pre-compiles regex patterns for each skill for efficient matching,
        taking special characters like C++, C#, .NET into account.
        """
        compiled = []
        for skill in self.skills_list:
            escaped_skill = re.escape(skill)
            # Use negative lookbehind and lookahead to ensure isolated match
            pattern = re.compile(
                r'(?<![a-zA-Z0-9])' + escaped_skill + r'(?![a-zA-Z0-9])',
                re.IGNORECASE
            )
            compiled.append((skill, pattern))
        return compiled

    def extract_skills(self, text: str) -> List[str]:
        """
        Extracts detected skills from given text string.
        
        Returns:
            Sorted list of unique detected skills (canonical name as defined in skills.json).
        """
        if not text:
            return []

        detected_skills: Set[str] = set()

        for canonical_skill, pattern in self._compiled_patterns:
            if pattern.search(text):
                detected_skills.add(canonical_skill)

        return sorted(list(detected_skills))

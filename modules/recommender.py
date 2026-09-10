import json
import os
import urllib.parse
from typing import List, Dict, Any

class ResourceRecommender:
    """
    Provides learning recommendations for missing skills using data/resources.json.
    Includes smart fallbacks for unlisted skills.
    """
    def __init__(self, resources_db_path: str = None):
        if resources_db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            resources_db_path = os.path.join(base_dir, "data", "resources.json")
            
        self.resources_db_path = resources_db_path
        self.resources_db = self._load_resources()

    def _load_resources(self) -> Dict[str, Any]:
        """Loads resources map from JSON file."""
        try:
            if not os.path.exists(self.resources_db_path):
                return {}
            with open(self.resources_db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load resources database: {e}")
            return {}

    def get_recommendations(self, missing_skills: List[str]) -> List[Dict[str, Any]]:
        """
        Returns a list of structured learning recommendations for missing skills.
        """
        recommendations = []

        for skill in missing_skills:
            if skill in self.resources_db:
                rec = self.resources_db[skill].copy()
                rec["skill"] = skill
                recommendations.append(rec)
            else:
                # Fallback recommendation with direct Google / Youtube search links
                encoded_skill = urllib.parse.quote(f"Learn {skill} tutorial course")
                recommendations.append({
                    "skill": skill,
                    "title": f"Mastering {skill} Fundamentals",
                    "platform": "YouTube / Google Search",
                    "url": f"https://www.google.com/search?q={encoded_skill}",
                    "type": "Online Tutorials & Docs",
                    "level": "Intermediate",
                    "description": f"Explore curated online tutorials, guides, and practical projects to build proficiency in {skill}."
                })

        return recommendations

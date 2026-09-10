import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class ResumeMatcher:
    """
    Uses Sentence Transformers (all-MiniLM-L6-v2) and scikit-learn cosine similarity
    to calculate semantic similarity and compute the final weighted job compatibility score.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("HF_TOKEN") or os.environ.get("API_KEY")
        self.model = None

    def load_model(self):
        """Loads the Sentence Transformer model lazily with optional API authentication token."""
        if self.model is None:
            kwargs = {}
            if self.api_key:
                kwargs["token"] = self.api_key
            self.model = SentenceTransformer(self.model_name, **kwargs)

    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Generates vector embeddings for two texts and computes cosine similarity.
        
        Returns:
            Semantic similarity score as a percentage between 0.0 and 100.0.
        """
        if not text1.strip() or not text2.strip():
            return 0.0

        self.load_model()
        
        # Generate embeddings
        embeddings = self.model.encode([text1, text2])
        
        # Reshape for scikit-learn cosine_similarity
        embedding1 = embeddings[0].reshape(1, -1)
        embedding2 = embeddings[1].reshape(1, -1)
        
        # Compute cosine similarity matrix
        sim_matrix = cosine_similarity(embedding1, embedding2)
        score = float(sim_matrix[0][0])
        
        # Convert range [-1, 1] to percentage [0, 100], clipping negative bounds if any
        similarity_percentage = max(0.0, float(score)) * 100.0
        return round(similarity_percentage, 2)

    def compute_overall_score(
        self, 
        semantic_similarity_pct: float, 
        skill_match_pct: float, 
        semantic_weight: float = 0.6, 
        skill_weight: float = 0.4
    ) -> float:
        """
        Calculates the overall weighted job compatibility score.
        
        Overall Score = (60% * Semantic Similarity) + (40% * Skill Match Score)
        
        Returns:
            Overall score as a percentage between 0.0 and 100.0.
        """
        overall = (semantic_weight * semantic_similarity_pct) + (skill_weight * skill_match_pct)
        return round(overall, 2)

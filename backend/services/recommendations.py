# services/recommendations.py
import os
import json
import boto3
import numpy as np
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

class CarbonRecommendationEngine:
    def __init__(self):
        self.qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        self.collection = os.getenv("COLLECTION_NAME", "carbon_footprint_bedrock")
        self.bedrock = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION", "us-east-1"))
    
    def _safe_extract_text(self, payload) -> str:
        """Safely extract and clean text from payload, handling binary data"""
        try:
            text = payload.get('text', '')
            
            # Handle binary data
            if isinstance(text, bytes):
                # Try multiple encodings to decode binary data
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        return text.decode(encoding, errors='ignore')
                    except:
                        continue
                return "[Binary content - unable to decode]"
            
            # Ensure it's a string
            return str(text) if text else "[No content]"
            
        except Exception:
            return "[Error extracting content]"
    
    def get_embedding(self, text: str) -> list:
        try:
            response = self.bedrock.invoke_model(
                modelId='amazon.titan-embed-text-v2:0',
                body=json.dumps({"inputText": text[:8000]})
            )
            embedding = json.loads(response['body'].read())['embedding']
            return embedding if embedding else []
        except Exception as e:
            print(f"Embedding error: {e}")
            return []
    
    def cosine_sim(self, a, b):
        try:
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        except:
            return 0.0
    
    def get_recommendations(self, analysis_data: dict, top_k: int = 3) -> list:
        try:
            print("🔄 Starting recommendation generation with real data")
            
            # Find over-budget categories
            over_budget_categories = []
            for category, data in analysis_data.get("budget_comparison_by_category", {}).items():
                if isinstance(data, dict) and data.get("status") == "over":
                    over_budget_categories.append({
                        "category": str(category),
                        "over_amount": float(data.get("delta_kg", 0)),
                        "actual_emission": float(data.get("actual_kg", 0))
                    })
            
            # Sort by most over budget
            over_budget_categories.sort(key=lambda x: x["over_amount"], reverse=True)
            
            recommendations = []
            
            # Get real recommendations for each over-budget category
            for category_data in over_budget_categories[:2]:
                category = category_data["category"]
                
                # Create search query
                query = f"carbon emissions reduction strategies {category.lower()}"
                
                # Get relevant documents using safe search
                docs = self._safe_mmr_search(query, top_k=2)
                
                if docs:
                    recommendations.append({
                        "category": category,
                        "problem": f"Over budget by {category_data['over_amount']} kg CO2",
                        "suggestions": docs
                    })
                    print(f"✅ Found {len(docs)} suggestions for {category}")
            
            print(f"🎯 Generated {len(recommendations)} total recommendations")
            return recommendations
            
        except Exception as e:
            print(f"❌ Error in get_recommendations: {e}")
            return []
    
    def _safe_mmr_search(self, query: str, top_k: int = 2) -> list:
        """Safe MMR search that handles binary data gracefully"""
        try:
            # Get query embedding
            query_embedding = self.get_embedding(query)
            if not query_embedding:
                return []
            
            # Get initial results - NO VECTORS to avoid binary issues
            results = self.qdrant.search(
                collection_name=self.collection,
                query_vector=query_embedding,
                limit=10,  # Smaller initial set
                with_payload=True,
                with_vectors=False  # Critical: no binary vector data
            )
            
            if not results:
                return []
            
            # Simple diversity selection (no vector math)
            selected_indices = []
            sources_used = set()
            
            for i, result in enumerate(results):
                if len(selected_indices) >= top_k:
                    break
                    
                source = str(result.payload.get('source', ''))
                
                # Basic diversity: don't pick multiple from same source
                if source not in sources_used:
                    selected_indices.append(i)
                    sources_used.add(source)
                elif not selected_indices:  # Ensure we have at least one
                    selected_indices.append(i)
            
            # Format safe results
            safe_docs = []
            for idx in selected_indices[:top_k]:
                result = results[idx]
                payload = result.payload
                
                # Safely extract and clean text
                clean_text = self._safe_extract_text(payload)
                if len(clean_text) > 200:
                    clean_text = clean_text[:200] + '...'
                
                safe_docs.append({
                    'source': str(payload.get('source', 'Unknown')),
                    'advice': clean_text,
                    'pages': str(payload.get('page_range', 'N/A'))
                })
            
            return safe_docs
            
        except Exception as e:
            print(f"❌ Safe search error: {e}")
            return []

# Global instance
recommendation_engine = CarbonRecommendationEngine()
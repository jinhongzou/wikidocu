import os
import sys
from dotenv import load_dotenv
# Add the parent directory to the path to import podcast_llm modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from podcast_llm.config import PodcastConfig
from podcast_llm.utils.embeddings import get_embeddings_model

# Load environment variables from .env file
print(f"Loading environment variables {os.path.join(os.path.dirname(__file__), '.env')}...")
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

def test_dashscope_embeddings():
    """Test DashScope embeddings model."""
    print("Testing DashScope embeddings...")
    
    # Create a basic config
    config = PodcastConfig.load()
    config.embeddings_model = "siliconcloud"
    
    # Check if API key is set
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key or api_key == "your_siliconflow_api_key":
        print("Warning: SILICONFLOW_API_KEY not set or using default value. Test will likely fail.")
        print("Please set a valid API key in the .env file.")
    
    try:
        # Get the embeddings model
        embeddings = get_embeddings_model(
            config, 
            #base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            base_url="https://api.siliconflow.cn/v1/embeddings",
            api_key=api_key
        )
        
        # Test embedding generation
        texts = ["人工智能是现代科技的重要领域", "Machine learning is a subset of AI"]
        embeddings_result = embeddings.embed_documents(texts)
        
        print(f"Successfully generated embeddings for {len(texts)} texts")
        print(f"Embedding dimension: {len(embeddings_result[0])}")
        print("Test passed!")
        return True
        
    except Exception as e:
        print(f"Error testing DashScope embeddings: {e}")
        if "Invalid token" in str(e):
            print("This error is likely due to an invalid or missing API key.")
            print("Please ensure you have set a valid SILICONFLOW_API_KEY in the .env file.")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dashscope_embeddings()
    if success:
        print("All tests passed!")
    else:
        print("Tests failed!")
        print("Note: If the error is related to API keys, please update the .env file with valid keys.")
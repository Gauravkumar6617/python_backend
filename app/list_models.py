from google import genai
from app.core.config import Settings

# Initialize client
client = genai.Client(api_key=Settings.GEMINI_API_KEY)

# List available models
try:
    pager = client.models.list()
    print("Available Models:")
    print("-" * 30)
    for model in pager:
        # We use getattr to safely check for the attribute
        methods = getattr(model, 'supported_generation_methods', "N/A")
        
        # If that fails, try the other common naming convention
        if methods == "N/A":
            methods = getattr(model, 'supported_methods', "N/A")

        print(f"ID: {model.name}")
        print(f"Display Name: {model.display_name}")
        print(f"Methods: {methods}")
        print("-" * 30)
except Exception as e:
    print(f"Error: {e}")
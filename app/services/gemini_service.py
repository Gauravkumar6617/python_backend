from google import genai
from app.core.config import Settings

client = genai.Client(api_key=Settings.GEMINI_API_KEY)

def generate_questions_stream(prompt: str):
    models_to_try = [
        "gemini-2.5-flash", 
       
    ]
    
    for model_id in models_to_try:
        try:
            # FIX: Use generate_content_stream() instead of generate_content()
            response_stream = client.models.generate_content_stream(
                model=model_id,
                contents=prompt
            )
            
            for chunk in response_stream:
                # In the new SDK, use chunk.text to get the content
                if chunk.text:
                    yield chunk.text
            return 

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                print(f"Quota exhausted for {model_id}, trying next...")
                continue
            print(f"Gemini Error with {model_id}: {e}")
            yield f"Error: {e}"
            return
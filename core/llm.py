"""Groq LLM for chat + Google Gemini for Vision + SentenceTransformer embeddings"""

from groq import Groq
from config.settings import Settings

# Initialize Groq for main chat (FREE & FAST)
groq_client = Groq(api_key=Settings.GROQ_API_KEY)

# Lazy load encoder and vision model to avoid startup issues
_encoder = None
_vision_model = None

def _get_encoder():
    """Lazy load SentenceTransformer encoder"""
    global _encoder
    if _encoder is None:
        from sentence_transformers import SentenceTransformer
        print("🔄 Loading embedding model...")
        _encoder = SentenceTransformer(Settings.SENTENCE_MODEL)
        print("✅ Embedding model loaded")
    return _encoder


def _get_vision_model():
    """Lazy load Gemini Vision model - ONLY when needed for images"""
    global _vision_model
    if _vision_model is None:
        import google.generativeai as genai
        genai.configure(api_key=Settings.GOOGLE_API_KEY)
        _vision_model = genai.GenerativeModel('gemini-2.5-flash')
        print("✅ Vision model loaded: gemini-2.5-flash")
    return _vision_model


def chat(prompt: str, system: str = None, max_tokens: int = None, temperature: float = None):
    """
    Send a chat completion request to Groq (FREE & FAST)
    Args:
        prompt: User message
        system: System message (optional)
        max_tokens: Max tokens in response
        temperature: Temperature for response generation
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",  # User's Groq model
            messages=messages,
            max_tokens=max_tokens or Settings.MAX_TOKENS,
            temperature=temperature or Settings.LLM_TEMPERATURE
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Groq API Error: {e}")
        return f"Error: Unable to get response from AI model. {str(e)}"


def chat_vision(prompt: str, image_data: bytes = None):
    """
    Send a vision request to Google Gemini (for image analysis only)
    ONLY called when user uploads an image
    """
    try:
        vision_model = _get_vision_model()
        if image_data:
            import PIL.Image
            import io
            image = PIL.Image.open(io.BytesIO(image_data))
            response = vision_model.generate_content([prompt, image])
        else:
            response = vision_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ Gemini Vision Error: {e}")
        return f"Error: Unable to analyze image. {str(e)}"


def embed_text(text: str):
    """
    Generate embeddings using SentenceTransformers
    """
    try:
        encoder = _get_encoder()
        return encoder.encode(text, convert_to_numpy=True)
    except Exception as e:
        print(f"Embedding Error: {e}")
        return None


def embed_texts(texts: list):
    """
    Batch embed multiple texts
    """
    try:
        encoder = _get_encoder()
        embeddings = encoder.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.tolist()
    except Exception as e:
        print(f"Batch Embedding Error: {e}")
        return None

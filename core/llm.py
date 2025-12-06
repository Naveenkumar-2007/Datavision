"""Groq-only LLM + SentenceTransformer embeddings"""

from groq import Groq
from sentence_transformers import SentenceTransformer
from config.settings import Settings

# Initialize clients
groq_client = Groq(api_key=Settings.GROQ_API_KEY)
encoder = SentenceTransformer(Settings.SENTENCE_MODEL)


def chat(prompt: str, system: str = None, max_tokens: int = None, temperature: float = None):
    """
    Send a chat completion request to Groq
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
            model=Settings.LLM_MODEL,
            messages=messages,
            max_tokens=max_tokens or Settings.MAX_TOKENS,
            temperature=temperature or Settings.LLM_TEMPERATURE
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq API Error: {e}")
        return f"Error: Unable to get response from AI model. {str(e)}"


def embed_text(text: str):
    """
    Generate embeddings using SentenceTransformers
    """
    try:
        return encoder.encode(text, convert_to_numpy=True)
    except Exception as e:
        print(f"Embedding Error: {e}")
        return None


def embed_texts(texts: list):
    """
    Batch embed multiple texts
    """
    try:
        embeddings = encoder.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.tolist()
    except Exception as e:
        print(f"Batch Embedding Error: {e}")
        return None

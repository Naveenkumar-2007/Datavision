import os
import re
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import tempfile
import uuid

router = APIRouter()

class VoiceRequest(BaseModel):
    text: str

def clean_text_for_speech(text: str) -> str:
    """Removes markdown, code blocks, emojis, and special formatting so it reads naturally."""
    # Remove code blocks
    text = re.sub(r'```.*?```', ' I have generated the requested code. ', text, flags=re.DOTALL)
    # Remove inline code
    text = re.sub(r'`[^`]*`', '', text)
    # Remove markdown headers and lists
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'[\*\-_]+\s*', '', text)
    # Remove tables
    text = re.sub(r'\|.*\|', '', text)
    # Remove emojis (basic range)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

@router.post("/synthesize")
async def synthesize_voice(request: VoiceRequest, background_tasks: BackgroundTasks):
    try:
        from gtts import gTTS
        
        cleaned_text = clean_text_for_speech(request.text)
        if not cleaned_text:
            cleaned_text = "I don't have any readable text for this response."
            
        # Create a temporary file
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"voice_{uuid.uuid4().hex}.mp3")
        
        # Generate speech
        tts = gTTS(text=cleaned_text, lang='en', slow=False)
        tts.save(file_path)
        
        # Clean up file after response is sent
        background_tasks.add_task(os.remove, file_path)
        
        return FileResponse(file_path, media_type="audio/mpeg", filename="response.mp3")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

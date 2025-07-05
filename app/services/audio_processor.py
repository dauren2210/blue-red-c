import asyncio
import io
import wave
import logging
import json
from datetime import datetime
from typing import Dict
from groq import AsyncGroq
from app.core.config import settings
from app.services.connection_manager import manager
from app.services.language_processor import language_processor
from app.crud.crud_session import update_session
from app.models.session import SessionUpdate

logging.basicConfig(level=logging.INFO)

class AudioProcessor:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.audio_buffer = bytearray()
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.stt_model = "whisper-large-v3"

    def add_audio_chunk(self, chunk: bytes):
        self.audio_buffer.extend(chunk)
        logging.info(f"Session {self.session_id}: Chunk added. Buffer size: {len(self.audio_buffer)} bytes")

    def _package_audio_as_wav(self) -> bytes:
        """Packages the raw audio buffer into a WAV file in memory."""
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(16000)  # 16kHz
                wf.writeframes(self.audio_buffer)
            logging.info(f"Session {self.session_id}: Audio packaged as WAV.")
            return wav_buffer.getvalue()

    async def process_final_audio(self):
        logging.info(f"Session {self.session_id}: Starting final audio processing...")
        if not self.audio_buffer:
            logging.warning(f"Session {self.session_id}: Audio buffer is empty. Nothing to process.")
            return

        try:
            wav_data = self._package_audio_as_wav()
            logging.info(f"Session {self.session_id}: Packaged {len(wav_data)} bytes into WAV format.")
            
            transcription_response = await self.client.audio.transcriptions.create(
                file=("in_memory.wav", wav_data),
                model=self.stt_model
            )
            full_transcript = transcription_response.text

            logging.info(f"Session {self.session_id}: Received transcript from Groq: {full_transcript}")
            
            if full_transcript:
                structured_data = await language_processor.extract_structured_data(full_transcript)
                logging.info(f"Session {self.session_id}: Extracted structured data: {structured_data}")
                
                update_data = SessionUpdate(
                    full_transcript=full_transcript.strip(),
                    structured_request=structured_data
                )
                await update_session(self.session_id, update_data)
                
                # Convert datetime objects to strings before sending over JSON
                def json_converter(o):
                    if isinstance(o, datetime):
                        return o.isoformat()
                
                json_safe_data = json.loads(json.dumps(structured_data, default=json_converter))
                
                await manager.send_personal_json(
                    {"status": "final_data", "transcript": full_transcript, "data": json_safe_data},
                    self.session_id
                )
        except Exception as e:
            logging.error(f"An error occurred during final audio processing for session {self.session_id}: {e}", exc_info=True)
            await manager.send_personal_json(
                {"status": "error", "message": "Failed to process audio."},
                self.session_id
            )

# A dictionary to hold an audio processor for each session
audio_processors: Dict[str, AudioProcessor] = {} 
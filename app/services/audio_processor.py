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
from app.services.supplier_search import supplier_search_service
from app.crud.crud_supplier import create_supplier
from app.models.supplier import SupplierCreate

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
            
            # 1. Send transcript to client as soon as it's ready
            await manager.send_personal_json(
                {"status": "transcript_ready", "transcript": full_transcript},
                self.session_id
            )
            
            if full_transcript:
                # 2. Extract structured data
                structured_data = await language_processor.extract_structured_data(full_transcript)
                logging.info(f"Session {self.session_id}: Extracted structured data: {structured_data}")
                
                update_data = SessionUpdate(
                    full_transcript=full_transcript.strip(),
                    structured_request=structured_data
                )
                await update_session(self.session_id, update_data)
                
                # Convert datetime objects for JSON serialization
                def json_converter(o):
                    if isinstance(o, datetime):
                        return o.isoformat()
                
                json_safe_data = json.loads(json.dumps(structured_data, default=json_converter))
                
                # 3. Send structured data to client
                await manager.send_personal_json(
                    {"status": "structured_data_ready", "data": json_safe_data},
                    self.session_id
                )

                # --- Integration: Find and Save Suppliers ---
                if structured_data and "search_query" in structured_data:
                    search_query = structured_data["search_query"]
                    
                    # 4. Notify client that supplier search is starting
                    logging.info(f"Session {self.session_id}: Starting supplier search with query: '{search_query}'")
                    await manager.send_personal_json(
                        {"status": "supplier_search_started", "query": search_query},
                        self.session_id
                    )
                    
                    found_suppliers = await supplier_search_service.find_suppliers(search_query)
                    
                    if found_suppliers:
                        logging.info(f"Session {self.session_id}: Found {len(found_suppliers)} qualified suppliers.")
                        
                        # 5. Send found suppliers to the client
                        await manager.send_personal_json(
                            {"status": "suppliers_found", "count": len(found_suppliers), "data": found_suppliers},
                            self.session_id
                        )

                        for business in found_suppliers:
                            # The new search logic provides a detailed analysis object
                            analysis = business.get("analysis", {})
                            phone_numbers = analysis.get("phone_numbers", [])

                            # We only process suppliers if we found phone numbers
                            if phone_numbers:
                                supplier_create = SupplierCreate(
                                    name=business.get("title"),
                                    phone_numbers=phone_numbers,
                                    extra_data={
                                        "website": business.get("url"),
                                        "reason": analysis.get("reason"),
                                    }
                                )
                                await create_supplier(supplier_create)
                        
                        logging.info(f"Session {self.session_id}: Saved {len(found_suppliers)} suppliers to the database.")
                        
                        # 6. Notify client that processing is complete
                        await manager.send_personal_json(
                            {"status": "processing_complete", "message": f"Saved {len(found_suppliers)} suppliers to the database."},
                            self.session_id
                        )
                    else:
                        logging.info(f"Session {self.session_id}: No suppliers found for query '{search_query}'.")
                        await manager.send_personal_json(
                            {"status": "processing_complete", "message": "No suppliers found for your query."},
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
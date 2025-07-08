from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.crud.crud_session import create_session
from app.models.session import SessionCreate
from app.services.connection_manager import manager
from app.services.audio_processor import AudioProcessor, audio_processors
import json
import logging

router = APIRouter()

@router.websocket("/ws/streaming")
async def websocket_endpoint(websocket: WebSocket):
    # Create a new session with default values
    session_create = SessionCreate()
    session = await create_session(session_create)
    session_id = str(session.id)

    # Create an audio processor for this session
    audio_processors[session_id] = AudioProcessor(session_id)
    
    await manager.connect(websocket, session_id)
    
    try:
        await manager.send_personal_json({"status": "session_created", "session_id": session_id}, session_id)

        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                logging.warning(f"Client initiated disconnect for session: {session_id}")
                logging.info(f"Calling process_final_audio for session: {session_id}")
                await audio_processors[session_id].process_final_audio()
                break

            # Handle binary data (audio chunks)
            if "bytes" in message and message["bytes"]:
                processor = audio_processors.get(session_id)
                if processor:
                    processor.add_audio_chunk(message["bytes"])
            
            # Handle text data (control messages like 'stop')
            elif "text" in message and message["text"]:
                text_data = message["text"]
                try:
                    json_data = json.loads(text_data)
                    if json_data.get("event") == "stop":
                        logging.info(f"Stop event received for session: {session_id}")
                        break
                except json.JSONDecodeError:
                    logging.warning(f"Received non-JSON text message: {text_data}")

    except WebSocketDisconnect:

        logging.info(f"Final processing for session: {session_id}")
        if session_id in audio_processors:
            logging.info(f"Calling process_final_audio for session: {session_id}")
            await audio_processors[session_id].process_final_audio()
            logging.info(f"Finished process_final_audio for session: {session_id}")

        logging.info(f"WebSocket disconnected for session: {session_id}")
        manager.disconnect(session_id)
        # Clean up the processor
        if session_id in audio_processors:
            del audio_processors[session_id]
        logging.info(f"Cleaned up processor for session {session_id}")
        try:
            await websocket.close(code=1011)
        except RuntimeError:
            pass  # Connection might already be closed 
    except Exception as e:
        logging.error(f"An error occurred in WebSocket for session {session_id}: {e}", exc_info=True)
        manager.disconnect(session_id)
        if session_id in audio_processors:
            del audio_processors[session_id]
        logging.info(f"Cleaned up processor for session {session_id}")
        try:
            await websocket.close(code=1011)
        except RuntimeError:
            pass  # Connection might already be closed 
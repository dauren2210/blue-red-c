from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.crud.crud_session import create_session
from app.models.session import SessionCreate
from app.services.connection_manager import manager
from app.services.audio_processor import AudioProcessor, audio_processors

router = APIRouter()

@router.websocket("/ws/streaming")
async def websocket_endpoint(websocket: WebSocket):
    # This is a temporary way to associate a session.
    # In a real app, the session_id might come from the URL path or a message.
    session_create = SessionCreate(customer_request="New audio stream")
    session = await create_session(session_create)
    session_id = str(session.id)

    # Create an audio processor for this session
    audio_processors[session_id] = AudioProcessor(session_id)
    
    await manager.connect(websocket, session_id)
    
    try:
        await manager.send_personal_json({"status": "session_created", "session_id": session_id}, session_id)

        while True:
            data = await websocket.receive_bytes()
            processor = audio_processors.get(session_id)
            if processor:
                await processor.process_audio_chunk(data)
            await manager.send_personal_json({"status": "data_received", "size": len(data)}, session_id)

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        if session_id in audio_processors:
            del audio_processors[session_id]
        print(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        manager.disconnect(session_id)
        if session_id in audio_processors:
            del audio_processors[session_id]
        print(f"An error occurred for session {session_id}: {e}")
        await websocket.close(code=1011) 
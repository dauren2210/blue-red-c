import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import Response
from app.core.config import settings
from app.services.language_processor import language_processor
from app.crud.crud_supplier import update_supplier

import json
from twilio.rest import Client

router = APIRouter()

logging.basicConfig(level=logging.INFO)

sessions = {}

@router.post("/twiml")
async def twiml_endpoint():
    logging.info("Received request for /twiml endpoint.")
    xml_response = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<Response>\n  <Connect>\n    <ConversationRelay url=\"{settings.WS_URL}\" welcomeGreeting=\"{"Hi, I'm with Blue Red C. I would like to inquire about a possibility to collaborate with your company as a supplier for us."}\" />\n  </Connect>\n</Response>"""
    logging.info("Returning TwiML XML response.")
    return Response(content=xml_response, media_type="text/xml")

@router.post("/initiate_call")
async def initiate_call(supplier_phone: str, from_phone: str = settings.TWILIO_PHONE_NUMBER):
    logging.info(f"Initiating call to supplier: {supplier_phone} from: {from_phone}")
    try:
        # Always use our own /twiml endpoint for ConversationRelay
        if not settings.DOMAIN:
            logging.error("DOMAIN environment variable is not set.")
            raise HTTPException(status_code=500, detail="DOMAIN environment variable is not set.")
        twiml_url = f"https://{settings.DOMAIN}/twiml"
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            to=supplier_phone,
            from_=from_phone,
            url=twiml_url
        )
        logging.info(f"Call initiated. Twilio SID: {call.sid}")

        # Update supplier with call details
        supplier_found = await get_supplier_by_phone(supplier_phone)
        if supplier_found is None:
            raise ValueError(f"Supplier not found for phone: {supplier_phone}")
        supplier_update_data = SupplierUpdate.model_validate({"call_status": "in_progress", "response_data": {"call_sid": call.sid}})
        await update_supplier(supplier_found.id, supplier_update_data)

        return {"status": "initiated", "sid": call.sid}
    except Exception as e:
        logging.error(f"Failed to initiate call: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate call.")

@router.websocket("/ws/conversation")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    call_sid = None
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            logging.info(f"Received message: {message}")
            if message["type"] == "setup":
                call_sid = message["callSid"]
                websocket.call_sid = call_sid
                sessions[call_sid] = []
                logging.info(f"Setup for call: {call_sid}")
            elif message["type"] == "prompt":
                transcript = message["voicePrompt"]
                logging.info(f"Processing prompt: {transcript}")
                try:
                    response_content = await language_processor.supplier_key_data_prompt(call_sid, transcript)
                    logging.info(f"Response content: {response_content}")
                    await websocket.send_text(json.dumps({
                        "type": "text",
                        "token": response_content,
                        "last": True
                    }))
                except Exception as e:
                    logging.error(f"Error processing prompt: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "text",
                        "token": "Sorry, I'm having technical issues right now. I will call you later. Thank you!",
                        "last": True
                    }))
            elif message["type"] == "interrupt":
                logging.info("Handling interruption.")
            else:
                logging.warning(f"Unknown message type received: {message['type']}")
    except WebSocketDisconnect:
        logging.info("WebSocket connection closed")

        try:
            supplier_found = await get_supplier_by_phone(supplier_phone)
            if supplier_found is None:
                raise ValueError(f"Supplier not found for phone: {supplier_phone}")
            supplier_update_data = SupplierUpdate.model_validate({
                "call_status": "completed", 
                "response_data": {
                    "call_sid": call.sid,
                    "call_transcript": language_processor.sid_conversations[call_sid]["history"]
                }
            })
            logging.info(f"Updating supplier: {supplier_found.id} with data: {supplier_update_data}")
            await update_supplier(supplier_found.id, supplier_update_data)
        except Exception as e:
            logging.error(f"Error updating supplier: {e}")

        if call_sid:
            sessions.pop(call_sid, None) 
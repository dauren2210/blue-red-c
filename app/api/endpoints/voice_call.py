from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Form
from pydantic import BaseModel, Field
from typing import Optional
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import logging
from app.services.call_processor import CallProcessor, add_call_processor, get_call_processor, remove_call_processor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/twilio", tags=["twilio"])

# Pydantic models for request/response
class VoiceCallRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number to call (E.164 format)")
    request_prompt: str = Field(..., description="Prompt describing what the AI should help with")
    callback_url: Optional[str] = Field(None, description="Webhook URL for call status updates")
    
class VoiceCallResponse(BaseModel):
    call_sid: str
    status: str
    phone_number: str
    message: str

class CallTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

# Initialize Twilio client
def get_twilio_client():
    """Initialize and return Twilio client"""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    if not all([account_sid, auth_token, from_number]):
        raise HTTPException(
            status_code=500,
            detail="Twilio configuration missing. Please set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER environment variables."
        )
    
    return Client(account_sid, auth_token), from_number

async def make_voice_call(phone_number: str, request_prompt: str, callback_url: Optional[str] = None):
    """Background task to make a voice call using Twilio with AI conversation"""
    try:
        # Create call processor
        call_processor = CallProcessor(
            call_sid="",  # Will be set after call creation
            phone_number=phone_number,
            request_prompt=request_prompt
        )
        
        # Start the conversation
        call_sid = await call_processor.start_conversation()
        
        # Store the call processor
        add_call_processor(call_sid, call_processor)
        
        logger.info(f"AI conversation call initiated with SID: {call_sid} to {phone_number}")
        return call_sid
        
    except Exception as e:
        logger.error(f"Error starting AI conversation call: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting AI conversation call: {str(e)}")

@router.post("/voice-call", response_model=CallTaskResponse)
async def create_voice_call_task(
    request: VoiceCallRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a task to call a user by their phone number using Twilio API.
    
    This endpoint creates a background task that will initiate a voice call
    to the specified phone number using Twilio's API.
    """
    try:
        # Validate phone number format (basic E.164 validation)
        if not request.phone_number.startswith('+'):
            raise HTTPException(
                status_code=400,
                detail="Phone number must be in E.164 format (e.g., +1234567890)"
            )
        
        # Generate a task ID (in a real application, you might want to store this in a database)
        import uuid
        task_id = str(uuid.uuid4())
        
        # Add the call task to background tasks
        background_tasks.add_task(
            make_voice_call,
            request.phone_number,
            request.request_prompt,
            request.callback_url
        )
        
        logger.info(f"Voice call task created with ID: {task_id} for number: {request.phone_number}")
        
        return CallTaskResponse(
            task_id=task_id,
            status="queued",
            message=f"Voice call task created successfully. Call will be initiated to {request.phone_number}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating voice call task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating voice call task: {str(e)}")

@router.post("/webhook/{call_sid}")
async def handle_call_webhook(call_sid: str, request: Request):
    """Handle Twilio webhook for call interactions"""
    try:
        form_data = await request.form()
        recording_url = form_data.get("RecordingUrl")
        
        if recording_url:
            # Process the recording
            call_processor = get_call_processor(call_sid)
            if call_processor:
                # Download and process the recording
                # This is a simplified version - you'd need to implement actual audio download
                logger.info(f"Call {call_sid}: Received recording at {recording_url}")
                
                # For now, we'll simulate processing the recording
                # In a real implementation, you would download the audio from recording_url
                # and pass it to process_user_input
                
                # Generate AI response (simulating user input)
                response = await call_processor.generate_response("Hello, how can I help you?")
                
                # Check if the response indicates the conversation should end
                if any(phrase in response.lower() for phrase in [
                    "thank you for your time", 
                    "have a great day", 
                    "goodbye",
                    "end this call"
                ]):
                    # End the conversation
                    await call_processor.end_conversation()
                    remove_call_processor(call_sid)
                    return {"status": "call_ended"}
                
                # Create TwiML with AI response and continue recording
                twiml = f"""
                <Response>
                    <Say voice="alice">{response}</Say>
                    <Record 
                        action="/twilio/webhook/{call_sid}" 
                        method="POST"
                        maxLength="30"
                        playBeep="false"
                        trim="trim-silence"
                        recordingStatusCallback="/twilio/recording-status/{call_sid}"
                        recordingStatusCallbackMethod="POST"
                    />
                </Response>
                """
                
                return {"twiml": twiml}
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Call {call_sid}: Webhook error: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/recording-status/{call_sid}")
async def handle_recording_status(call_sid: str, request: Request):
    """Handle recording status updates"""
    try:
        form_data = await request.form()
        recording_status = form_data.get("RecordingStatus")
        
        if recording_status == "completed":
            recording_url = form_data.get("RecordingUrl")
            logger.info(f"Call {call_sid}: Recording completed at {recording_url}")
            
            # Here you would download the recording and process it
            # For now, we'll just log it
            
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Call {call_sid}: Recording status error: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/call-status/{call_sid}")
async def handle_call_status(call_sid: str, request: Request):
    """Handle call status updates"""
    try:
        form_data = await request.form()
        call_status = form_data.get("CallStatus")
        
        logger.info(f"Call {call_sid}: Status changed to {call_status}")
        
        if call_status in ["completed", "failed", "busy", "no-answer"]:
            # End the conversation and extract supplier data
            call_processor = get_call_processor(call_sid)
            if call_processor:
                # Extract supplier data
                supplier_data = await call_processor.extract_supplier_data()
                logger.info(f"Call {call_sid}: Final supplier data: {supplier_data}")
                
                # Here you would typically save this data to your database
                # For example, update a supplier record with the response_data
                
                await call_processor.end_conversation()
                remove_call_processor(call_sid)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Call {call_sid}: Call status error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/health")
async def twilio_health_check():
    """Health check endpoint for Twilio API module"""
    try:
        # Test Twilio client initialization
        get_twilio_client()
        return {"status": "ok", "message": "Twilio API module is healthy"}
    except Exception as e:
        return {"status": "error", "message": f"Twilio configuration issue: {str(e)}"} 
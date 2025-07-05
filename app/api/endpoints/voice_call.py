from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/twilio", tags=["twilio"])

# Pydantic models for request/response
class VoiceCallRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number to call (E.164 format)")
    message: Optional[str] = Field(None, description="Message to play during the call")
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

async def make_voice_call(phone_number: str, message: str, callback_url: Optional[str] = None):
    """Background task to make a voice call using Twilio"""
    try:
        client, from_number = get_twilio_client()
        
        # Create TwiML for the call
        twiml = f"""
        <Response>
            <Say voice="alice">{message or 'Hello! This is an automated call from your application.'}</Say>
        </Response>
        """
        
        # Make the call
        call = client.calls.create(
            twiml=twiml,
            to=phone_number,
            from_=from_number,
            status_callback=callback_url if callback_url else None,
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            status_callback_method='POST'
        )
        
        logger.info(f"Call initiated with SID: {call.sid} to {phone_number}")
        return call.sid
        
    except TwilioException as e:
        logger.error(f"Twilio error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Twilio error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

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
            request.message or "Hello! This is an automated call from your application.",
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

@router.get("/health")
async def twilio_health_check():
    """Health check endpoint for Twilio API module"""
    try:
        # Test Twilio client initialization
        get_twilio_client()
        return {"status": "ok", "message": "Twilio API module is healthy"}
    except Exception as e:
        return {"status": "error", "message": f"Twilio configuration issue: {str(e)}"} 
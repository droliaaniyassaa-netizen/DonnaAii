from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize OpenAI API key
openai_api_key = os.environ.get('OPENAI_API_KEY')

# Donna's personality system message
DONNA_SYSTEM_MESSAGE = """You are Donna, the smartest most tech-forward AI assistant. You are confident, intelligent, slightly witty, and caring. Like Donna Paulsen from Suits, you are smart but never overcomplicated. You are capable but never intimidating. Users should feel like you 'get them,' anticipate their needs, and make life smoother. You help with scheduling, career planning, and health tracking. Always be predictive and trustworthy in your responses. Keep your responses concise but helpful.

IMPORTANT: When you confirm creating a calendar event, ALWAYS end your response with this exact phrase: "Would you like any reminders or notes for this event?" This helps users add additional context to their events."""

# Models
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    is_user: bool
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    event_created: Optional[bool] = False  # Context for Donna's response

class ChatResponse(BaseModel):
    response: str
    session_id: str

# New model for tracking conversation context
class ConversationContext(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    last_event_id: Optional[str] = None  # ID of the last created event
    waiting_for_notes: bool = False  # True if waiting for user to provide notes
    context_type: Optional[str] = None  # "event_notes", "reminder_setup", etc.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CalendarEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    datetime_utc: datetime  # Store complete datetime in UTC
    category: Optional[str] = "personal"  # Default category
    reminder: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    datetime_utc: str  # ISO string datetime in UTC from frontend
    category: Optional[str] = "personal"  # Default category
    reminder: bool = True

class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

class CareerGoal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    timeframe: str
    action_plan: List[str] = []
    resources: List[str] = []
    progress: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CareerGoalCreate(BaseModel):
    goal: str
    timeframe: str

class HealthEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # meal, hydration, sleep, exercise
    description: str
    value: Optional[str] = None
    datetime_utc: datetime  # Store complete datetime in UTC
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HealthEntryCreate(BaseModel):
    type: str
    description: str
    value: Optional[str] = None
    datetime_utc: str  # ISO string datetime in UTC from frontend

class HealthGoal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal_type: str  # weight_loss, muscle_gain, maintain
    target: str
    current_progress: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HealthGoalCreate(BaseModel):
    goal_type: str
    target: str
    current_progress: str

# Helper function to prepare data for MongoDB
def prepare_for_mongo(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

# Chat endpoints
@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_donna(request: ChatRequest):
    try:
        # Store user message
        user_message = ChatMessage(
            message=request.message,
            is_user=True,
            session_id=request.session_id
        )
        await db.chat_messages.insert_one(prepare_for_mongo(user_message.dict()))
        
        # Check if we're waiting for notes from a previous event creation
        context = await db.conversation_context.find_one(
            {"session_id": request.session_id, "waiting_for_notes": True}
        )
        
        donna_response = ""
        
        if context and context.get("waiting_for_notes"):
            # User is responding to the notes question
            await handle_event_notes_response(request.message, context, request.session_id)
            donna_response = "Perfect! I've added those notes to your event. You're all set!"
            
            # Clear the context
            await db.conversation_context.update_one(
                {"id": context["id"]},
                {"$set": {"waiting_for_notes": False}}
            )
        else:
            # Normal conversation flow
            # Initialize Donna chat
            chat = LlmChat(
                api_key=openai_api_key,
                session_id=request.session_id,
                system_message=DONNA_SYSTEM_MESSAGE
            ).with_model("openai", "gpt-4o-mini")
            
            # Create user message for LLM with event creation context
            user_text = request.message
            if request.event_created:
                user_text += "\n\n[CONTEXT: I just automatically created a calendar event from your message with default reminders (12 hours and 2 hours before). Acknowledge this briefly and naturally, then ask: 'Would you like any reminders or notes for this event?']"
            
            user_msg = UserMessage(text=user_text)
            
            # Get response from Donna
            donna_response = await chat.send_message(user_msg)
            
            # Check if message should create calendar events, career goals, or health entries
            created_event_id = await process_message_context(request.message, request.session_id)
            
            # If an event was created and Donna asked the follow-up question, set up context
            if created_event_id and "Would you like any reminders or notes for this event?" in donna_response:
                await setup_event_notes_context(request.session_id, created_event_id)
        
        # Store Donna's response
        donna_message = ChatMessage(
            message=donna_response,
            is_user=False,
            session_id=request.session_id
        )
        await db.chat_messages.insert_one(prepare_for_mongo(donna_message.dict()))
        
        return ChatResponse(response=donna_response, session_id=request.session_id)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@api_router.get("/chat/history/{session_id}", response_model=List[ChatMessage])
async def get_chat_history(session_id: str):
    messages = await db.chat_messages.find({"session_id": session_id}).sort("timestamp", 1).to_list(100)
    return [ChatMessage(**msg) for msg in messages]

# Calendar endpoints
@api_router.post("/calendar/events", response_model=CalendarEvent)
async def create_event(event: CalendarEventCreate):
    # Parse UTC datetime from frontend
    try:
        datetime_utc = datetime.fromisoformat(event.datetime_utc.replace('Z', '+00:00'))
        if datetime_utc.tzinfo is None:
            datetime_utc = datetime_utc.replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO format.")
    
    event_obj = CalendarEvent(
        title=event.title,
        description=event.description,
        datetime_utc=datetime_utc,
        category=event.category or "personal",
        reminder=event.reminder
    )
    await db.calendar_events.insert_one(prepare_for_mongo(event_obj.dict()))
    return event_obj

@api_router.get("/calendar/events", response_model=List[CalendarEvent])
async def get_events():
    # Fetch events and sort by datetime_utc in ascending order (earliest first)
    events = await db.calendar_events.find().sort("datetime_utc", 1).to_list(100)
    result = []
    
    for event in events:
        # Handle both old and new data formats
        if 'datetime_utc' not in event:
            # Old format: convert date + time to datetime_utc
            if 'date' in event and 'time' in event:
                try:
                    # Create datetime from date and time, assume UTC for old data
                    date_str = event['date']
                    time_str = event.get('time', '12:00')
                    datetime_str = f"{date_str}T{time_str}:00"
                    event['datetime_utc'] = datetime.fromisoformat(datetime_str).replace(tzinfo=timezone.utc)
                except:
                    # Skip invalid events
                    continue
            else:
                # Skip events without proper date/time
                continue
        
        try:
            result.append(CalendarEvent(**event))
        except Exception as e:
            # Skip invalid events
            print(f"Skipping invalid event: {e}")
            continue
    
    # Sort by datetime_utc
    result.sort(key=lambda x: x.datetime_utc)
    return result

@api_router.put("/calendar/events/{event_id}", response_model=CalendarEvent)
async def update_event(event_id: str, update_data: CalendarEventUpdate):
    # Build update document
    update_fields = {}
    if update_data.title is not None:
        update_fields["title"] = update_data.title
    if update_data.description is not None:
        update_fields["description"] = update_data.description
    if update_data.category is not None:
        update_fields["category"] = update_data.category
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Update event in database
    result = await db.calendar_events.update_one(
        {"id": event_id},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Return updated event
    updated_event = await db.calendar_events.find_one({"id": event_id})
    if not updated_event:
        raise HTTPException(status_code=404, detail="Event not found after update")
    
    return CalendarEvent(**updated_event)

@api_router.delete("/calendar/events/{event_id}")
async def delete_event(event_id: str):
    result = await db.calendar_events.delete_one({"id": event_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted successfully"}

# Career endpoints
@api_router.post("/career/goals", response_model=CareerGoal)
async def create_career_goal(goal: CareerGoalCreate):
    # Generate action plan using Donna
    chat = LlmChat(
        api_key=openai_api_key,
        session_id="career_planning",
        system_message="You are Donna, a career coach. Create a detailed, practical action plan with specific steps and resources."
    ).with_model("openai", "gpt-4o-mini")
    
    prompt = f"Create a detailed action plan to achieve this career goal: '{goal.goal}' within {goal.timeframe}. Provide specific steps and recommended resources."
    user_msg = UserMessage(text=prompt)
    action_plan_response = await chat.send_message(user_msg)
    
    # Parse action plan (simple split for now)
    action_steps = [step.strip() for step in action_plan_response.split('\n') if step.strip() and not step.strip().startswith('#')]
    
    goal_obj = CareerGoal(
        goal=goal.goal,
        timeframe=goal.timeframe,
        action_plan=action_steps[:10],  # Limit to 10 steps
        resources=["LinkedIn Learning", "Industry Books", "Networking Events", "Online Courses"]
    )
    await db.career_goals.insert_one(prepare_for_mongo(goal_obj.dict()))
    return goal_obj

@api_router.get("/career/goals", response_model=List[CareerGoal])
async def get_career_goals():
    goals = await db.career_goals.find().sort("created_at", -1).to_list(100)
    return [CareerGoal(**goal) for goal in goals]

@api_router.put("/career/goals/{goal_id}/progress")
async def update_goal_progress(goal_id: str, progress: int):
    result = await db.career_goals.update_one(
        {"id": goal_id},
        {"$set": {"progress": progress}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"message": "Progress updated successfully"}

# Health endpoints
@api_router.post("/health/entries", response_model=HealthEntry)
async def create_health_entry(entry: HealthEntryCreate):
    # Parse UTC datetime from frontend
    try:
        datetime_utc = datetime.fromisoformat(entry.datetime_utc.replace('Z', '+00:00'))
        if datetime_utc.tzinfo is None:
            datetime_utc = datetime_utc.replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO format.")
    
    entry_obj = HealthEntry(
        type=entry.type,
        description=entry.description,
        value=entry.value,
        datetime_utc=datetime_utc
    )
    await db.health_entries.insert_one(prepare_for_mongo(entry_obj.dict()))
    return entry_obj

@api_router.get("/health/entries", response_model=List[HealthEntry])
async def get_health_entries():
    entries = await db.health_entries.find().to_list(100)
    result = []
    
    for entry in entries:
        # Handle both old and new data formats
        if 'datetime_utc' not in entry:
            # Old format: convert date to datetime_utc
            if 'date' in entry:
                try:
                    # Create datetime from date, assume 12:00 UTC for old data
                    date_str = entry['date']
                    datetime_str = f"{date_str}T12:00:00"
                    entry['datetime_utc'] = datetime.fromisoformat(datetime_str).replace(tzinfo=timezone.utc)
                except:
                    # Skip invalid entries
                    continue
            else:
                # Skip entries without proper date
                continue
        
        try:
            result.append(HealthEntry(**entry))
        except Exception as e:
            # Skip invalid entries
            print(f"Skipping invalid health entry: {e}")
            continue
    
    # Sort by datetime_utc (newest first)
    result.sort(key=lambda x: x.datetime_utc, reverse=True)
    return result

@api_router.post("/health/goals", response_model=HealthGoal)
async def create_health_goal(goal: HealthGoalCreate):
    goal_obj = HealthGoal(**goal.dict())
    await db.health_goals.insert_one(prepare_for_mongo(goal_obj.dict()))
    return goal_obj

@api_router.get("/health/goals", response_model=List[HealthGoal])
async def get_health_goals():
    goals = await db.health_goals.find().sort("created_at", -1).to_list(100)
    return [HealthGoal(**goal) for goal in goals]

@api_router.get("/health/analytics")
async def get_health_analytics():
    # Get recent health entries
    recent_entries = await db.health_entries.find().sort("date", -1).to_list(30)
    
    # Basic analytics
    meal_count = len([e for e in recent_entries if e.get('type') == 'meal'])
    water_count = len([e for e in recent_entries if e.get('type') == 'hydration'])
    exercise_count = len([e for e in recent_entries if e.get('type') == 'exercise'])
    sleep_entries = [e for e in recent_entries if e.get('type') == 'sleep']
    
    return {
        "meals_this_week": meal_count,
        "water_glasses_today": water_count,
        "workouts_this_week": exercise_count,
        "average_sleep": len(sleep_entries)
    }

# Helper functions for event notes handling
async def handle_event_notes_response(message: str, context: dict, session_id: str):
    """Handle user's response to event notes question"""
    event_id = context.get("last_event_id")
    if event_id:
        # Update the event with the user's notes
        await db.calendar_events.update_one(
            {"id": event_id},
            {"$set": {"description": message}}
        )

async def setup_event_notes_context(session_id: str, event_id: str):
    """Set up conversation context for collecting event notes"""
    context = ConversationContext(
        session_id=session_id,
        last_event_id=event_id,
        waiting_for_notes=True,
        context_type="event_notes"
    )
    await db.conversation_context.insert_one(prepare_for_mongo(context.dict()))

# Context processing function - ENHANCED to return event ID and use frontend logic
async def process_message_context(message: str, session_id: str):
    """Process message to auto-create calendar events, career goals, or health entries"""
    message_lower = message.lower()
    current_utc = datetime.now(timezone.utc)
    created_event_id = None
    
    # Enhanced event detection patterns (simplified version of frontend logic)
    event_indicators = [
        'meeting', 'appointment', 'schedule', 'book', 'i have',
        'tomorrow', 'today', 'tonight', 'next week', 'next', 'at', 'pm', 'am',
        'doctor', 'dentist', 'gym', 'workout', 'lunch', 'dinner',
        'birthday', 'anniversary', 'remind me', 'reminder',
        'call', 'visit', 'party', 'celebration', 'conference'
    ]
    
    # Check if this looks like an event message
    if any(indicator in message_lower for indicator in event_indicators):
        try:
            # Simple title extraction (clean version)
            title = extract_simple_title(message)
            
            # Simple time extraction
            event_time = extract_simple_time(message)
            
            # Simple date calculation
            event_date = extract_simple_date(message, current_utc)
            
            # Simple category detection
            category = detect_simple_category(message_lower)
            
            # Create the event
            event = CalendarEvent(
                title=title,
                description=message,  # Store original message as description initially
                category=category,
                datetime_utc=event_date,
                reminder=True
            )
            
            await db.calendar_events.insert_one(prepare_for_mongo(event.dict()))
            created_event_id = event.id
            
            print(f"✅ Created event from chat: {event.title} at {event_date}")
                    
        except Exception as e:
            print(f"Error creating event from message: {e}")
    
    # Health context detection (unchanged)
    if any(word in message_lower for word in ['ate', 'drank', 'water', 'meal', 'sleep', 'workout']):
        entry_type = 'meal' if 'ate' in message_lower or 'meal' in message_lower else 'hydration'
        if 'water' in message_lower:
            entry_type = 'hydration'
        elif 'sleep' in message_lower:
            entry_type = 'sleep'
        elif 'workout' in message_lower:
            entry_type = 'exercise'
            
        health_entry = HealthEntry(
            type=entry_type,
            description=message,
            datetime_utc=current_utc
        )
        await db.health_entries.insert_one(prepare_for_mongo(health_entry.dict()))
    
    return created_event_id

# Helper functions for simple event extraction
def extract_simple_title(message):
    """Extract a clean title from the message"""
    import re
    
    text = message.lower()
    
    # Remove common filler phrases
    text = re.sub(r'\b(i have a?|i need to|remind me to|i want to|i should|my|the)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(at|on|for|tomorrow|today|tonight|next week)\s.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d{1,2}:?\d{0,2}\s?(am|pm|AM|PM)\b', '', text)
    
    # Clean up
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Handle specific cases
    if 'birthday' in text:
        return text.replace('birthday', '').strip() + ' Birthday'
    elif 'meeting' in text:
        return 'Meeting'
    elif 'appointment' in text:
        return 'Appointment'
    elif 'gym' in text or 'workout' in text:
        return 'Gym'
    elif 'doctor' in text:
        return 'Doctor'
    elif 'dentist' in text:
        return 'Dentist'
    elif 'meds' in text or 'medication' in text or 'vitamins' in text:
        return text.strip().title()
    
    # Default cleanup and capitalization
    if text:
        return text.strip().title()
    
    return 'Event'

def extract_simple_time(message):
    """Extract time from message, default to reasonable times"""
    import re
    
    # Look for explicit time patterns
    time_match = re.search(r'\b(\d{1,2}):?(\d{0,2})\s?(am|pm|AM|PM)\b', message)
    if time_match:
        hours = int(time_match.group(1))
        minutes = int(time_match.group(2)) if time_match.group(2) else 0
        ampm = time_match.group(3).lower() if time_match.group(3) else ''
        
        # Convert to 24-hour format
        if ampm == 'pm' and hours != 12:
            hours += 12
        elif ampm == 'am' and hours == 12:
            hours = 0
            
        return datetime.now(timezone.utc).replace(hour=hours, minute=minutes, second=0, microsecond=0)
    
    # Default times based on content
    message_lower = message.lower()
    current = datetime.now(timezone.utc)
    
    if any(word in message_lower for word in ['morning', 'breakfast']):
        return current.replace(hour=9, minute=0, second=0, microsecond=0)
    elif any(word in message_lower for word in ['lunch', 'noon']):
        return current.replace(hour=12, minute=0, second=0, microsecond=0)
    elif any(word in message_lower for word in ['afternoon']):
        return current.replace(hour=15, minute=0, second=0, microsecond=0)
    elif any(word in message_lower for word in ['evening', 'dinner']):
        return current.replace(hour=18, minute=0, second=0, microsecond=0)
    elif any(word in message_lower for word in ['night', 'tonight']):
        return current.replace(hour=20, minute=0, second=0, microsecond=0)
    else:
        return current.replace(hour=10, minute=0, second=0, microsecond=0)

def extract_simple_date(message, current_utc):
    """Extract date from message, combining with time"""
    message_lower = message.lower()
    
    # Get time component
    time_component = extract_simple_time(message)
    
    if 'tomorrow' in message_lower:
        target_date = current_utc + timedelta(days=1)
        return target_date.replace(hour=time_component.hour, minute=time_component.minute, second=0, microsecond=0)
    elif 'next week' in message_lower:
        target_date = current_utc + timedelta(weeks=1)
        return target_date.replace(hour=time_component.hour, minute=time_component.minute, second=0, microsecond=0)
    else:
        # Default to today
        return time_component

def detect_simple_category(message_lower):
    """Detect event category from message content"""
    if any(word in message_lower for word in ['meeting', 'work', 'office', 'conference', 'project']):
        return 'work'
    elif any(word in message_lower for word in ['doctor', 'dentist', 'appointment', 'medical', 'checkup']):
        return 'appointments'
    elif any(word in message_lower for word in ['gym', 'workout', 'exercise', 'fitness', 'training']):
        return 'regular_activities'
    elif any(word in message_lower for word in ['birthday', 'anniversary', 'party', 'celebration', 'dinner', 'lunch']):
        return 'personal'
    elif any(word in message_lower for word in ['reminder', 'meds', 'medication', 'vitamins', 'remind me']):
        return 'reminders'
    else:
        return 'personal'

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
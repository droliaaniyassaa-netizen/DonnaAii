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
from datetime import datetime, timezone
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
DONNA_SYSTEM_MESSAGE = """You are Donna, the smartest most tech-forward AI assistant. You are confident, intelligent, slightly witty, and caring. Like Donna Paulsen from Suits, you are smart but never overcomplicated. You are capable but never intimidating. Users should feel like you 'get them,' anticipate their needs, and make life smoother. You help with scheduling, career planning, and health tracking. Always be predictive and trustworthy in your responses. Keep your responses concise but helpful."""

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

class ChatResponse(BaseModel):
    response: str
    session_id: str

class CalendarEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    date: str
    time: str
    reminder: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    date: str
    time: str
    reminder: bool = True

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
    date: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HealthEntryCreate(BaseModel):
    type: str
    description: str
    value: Optional[str] = None
    date: str

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
        
        # Initialize Donna chat
        chat = LlmChat(
            api_key=openai_api_key,
            session_id=request.session_id,
            system_message=DONNA_SYSTEM_MESSAGE
        ).with_model("openai", "gpt-4o-mini")
        
        # Create user message for LLM
        user_msg = UserMessage(text=request.message)
        
        # Get response from Donna
        donna_response = await chat.send_message(user_msg)
        
        # Store Donna's response
        donna_message = ChatMessage(
            message=donna_response,
            is_user=False,
            session_id=request.session_id
        )
        await db.chat_messages.insert_one(prepare_for_mongo(donna_message.dict()))
        
        # Check if message should create calendar events, career goals, or health entries
        await process_message_context(request.message, request.session_id)
        
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
    event_obj = CalendarEvent(**event.dict())
    await db.calendar_events.insert_one(prepare_for_mongo(event_obj.dict()))
    return event_obj

@api_router.get("/calendar/events", response_model=List[CalendarEvent])
async def get_events():
    events = await db.calendar_events.find().sort("date", 1).to_list(100)
    return [CalendarEvent(**event) for event in events]

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
    entry_obj = HealthEntry(**entry.dict())
    await db.health_entries.insert_one(prepare_for_mongo(entry_obj.dict()))
    return entry_obj

@api_router.get("/health/entries", response_model=List[HealthEntry])
async def get_health_entries():
    entries = await db.health_entries.find().sort("date", -1).to_list(100)
    return [HealthEntry(**entry) for entry in entries]

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

# Context processing function
async def process_message_context(message: str, session_id: str):
    """Process message to auto-create calendar events, career goals, or health entries"""
    message_lower = message.lower()
    
    # Simple keyword detection for auto-scheduling
    if any(word in message_lower for word in ['meeting', 'appointment', 'call', 'schedule', 'tomorrow', 'next week']):
        # This is a basic implementation - in a real app, you'd use NLP
        if 'meeting' in message_lower:
            event = CalendarEvent(
                title="Auto-scheduled Meeting",
                description=f"Created from chat: {message}",
                date="2024-01-15",  # Default date - would be smarter in real implementation
                time="10:00"
            )
            await db.calendar_events.insert_one(prepare_for_mongo(event.dict()))
    
    # Health context detection
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
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d")
        )
        await db.health_entries.insert_one(prepare_for_mongo(health_entry.dict()))

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
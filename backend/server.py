from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List
import uuid
from datetime import datetime

# Import route modules
from routes.auth_routes import create_auth_router
from routes.user_routes import create_user_router
from routes.skill_routes import create_skill_router
from routes.matching_routes import create_matching_router
from routes.session_routes import create_session_router
from routes.message_routes import create_message_router
from routes.gamification_routes import create_gamification_router
from routes.community_routes import router as community_router

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(
    title="SkillSwap API",
    description="AI-powered skill exchange platform",
    version="1.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models (keeping existing for backward compatibility)
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Add basic health check routes
@api_router.get("/")
async def root():
    return {"message": "SkillSwap API is running!", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include feature routers
api_router.include_router(create_auth_router(db))
api_router.include_router(create_user_router(db))
api_router.include_router(create_skill_router(db))
api_router.include_router(create_matching_router(db))
api_router.include_router(create_session_router(db))
api_router.include_router(create_message_router(db))
api_router.include_router(create_gamification_router(db))
app.include_router(community_router)

# Include the main router in the app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("SkillSwap API started successfully")
    
    # Initialize default skills
    try:
        from services.skill_service import SkillService
        skill_service = SkillService(db)
        await skill_service.create_default_skills()
        logger.info("Default skills initialized")
    except Exception as e:
        logger.error(f"Failed to initialize default skills: {str(e)}")
    
    # Initialize gamification system
    try:
        from services.gamification_service import GamificationService
        gamification_service = GamificationService(db)
        await gamification_service.create_default_badges()
        await gamification_service.create_default_achievements()
        logger.info("Gamification system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize gamification system: {str(e)}")
    
    # Initialize community features
    try:
        from services.community_service import CommunityService
        community_service = CommunityService()
        await community_service.initialize_default_forums()
        logger.info("Community system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize community system: {str(e)}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("Database connection closed")

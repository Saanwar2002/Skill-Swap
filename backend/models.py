from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid


class UserRole(str, Enum):
    LEARNER = "learner"
    TEACHER = "teacher"
    BOTH = "both"


class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


# Database Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    username: str
    password_hash: str
    first_name: str
    last_name: str
    bio: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    role: UserRole = UserRole.BOTH
    profile_image: Optional[str] = None  # base64 encoded
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    is_verified: bool = False
    
    # Skills and preferences
    skills_offered: List[str] = []
    skills_wanted: List[str] = []
    teaching_style: Optional[str] = None
    learning_style: Optional[str] = None
    availability: Dict[str, Any] = {}  # Weekly availability
    languages: List[str] = []
    
    # Gamification
    skill_coins: int = 100  # Starting balance
    experience_points: int = 0
    level: int = 1
    badges: List[str] = []
    
    # Statistics
    sessions_taught: int = 0
    sessions_learned: int = 0
    total_rating: float = 0.0
    rating_count: int = 0
    
    @property
    def average_rating(self) -> float:
        if self.rating_count == 0:
            return 0.0
        return round(self.total_rating / self.rating_count, 2)


class Skill(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str
    subcategory: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    popularity_score: float = 0.0


class UserSkill(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    skill_id: str
    skill_name: str
    level: SkillLevel
    years_experience: Optional[int] = None
    certifications: List[str] = []
    portfolio_items: List[str] = []  # base64 encoded images/files
    endorsements: List[str] = []  # User IDs who endorsed
    self_assessment: Optional[str] = None
    verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Match(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user1_id: str
    user2_id: str
    skill_offered: str
    skill_wanted: str
    compatibility_score: float
    status: str = "pending"  # pending, accepted, declined, expired
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=7))
    
    # Matching algorithm data
    algorithm_data: Dict[str, Any] = {}
    user1_interest: bool = False
    user2_interest: bool = False


class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    teacher_id: str
    learner_id: str
    skill_id: str
    skill_name: str
    title: str
    description: Optional[str] = None
    
    # Scheduling
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    timezone: str
    
    # Session details
    status: SessionStatus = SessionStatus.SCHEDULED
    session_type: str = "video"  # video, chat, hybrid
    meeting_link: Optional[str] = None
    notes: Optional[str] = None
    
    # Outcomes
    skill_coins_paid: int = 0
    teacher_rating: Optional[float] = None
    learner_rating: Optional[float] = None
    teacher_feedback: Optional[str] = None
    learner_feedback: Optional[str] = None
    
    # Progress tracking
    learning_objectives: List[str] = []
    objectives_completed: List[str] = []
    homework_assigned: Optional[str] = None
    homework_completed: bool = False
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    recipient_id: str
    session_id: Optional[str] = None
    conversation_id: str
    
    content: str
    message_type: MessageType = MessageType.TEXT
    file_data: Optional[str] = None  # base64 encoded
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    
    is_read: bool = False
    is_edited: bool = False
    reply_to: Optional[str] = None  # Message ID
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    participants: List[str]  # User IDs
    session_id: Optional[str] = None
    last_message_id: Optional[str] = None
    last_message_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Review(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reviewer_id: str
    reviewee_id: str
    session_id: str
    rating: float = Field(ge=1, le=5)
    comment: Optional[str] = None
    skills_learned: List[str] = []
    would_recommend: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Achievement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    icon: str
    category: str
    criteria: Dict[str, Any]
    skill_coins_reward: int = 0
    experience_points_reward: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserAchievement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    achievement_id: str
    achievement_name: str
    earned_at: datetime = Field(default_factory=datetime.utcnow)
    progress_data: Dict[str, Any] = {}


# API Request/Response Models
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: str
    last_name: str
    bio: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    role: UserRole = UserRole.BOTH


class UserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    role: Optional[UserRole] = None
    profile_image: Optional[str] = None
    teaching_style: Optional[str] = None
    learning_style: Optional[str] = None
    availability: Optional[Dict[str, Any]] = None
    languages: Optional[List[str]] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    first_name: str
    last_name: str
    bio: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    role: UserRole
    profile_image: Optional[str] = None
    created_at: datetime
    is_active: bool
    is_verified: bool
    
    # Skills and preferences
    skills_offered: List[str] = []
    skills_wanted: List[str] = []
    teaching_style: Optional[str] = None
    learning_style: Optional[str] = None
    availability: Dict[str, Any] = {}
    languages: List[str] = []
    
    # Gamification
    skill_coins: int
    experience_points: int
    level: int
    badges: List[str] = []
    
    # Statistics
    sessions_taught: int
    sessions_learned: int
    average_rating: float
    rating_count: int


class SessionCreate(BaseModel):
    teacher_id: str
    learner_id: str
    skill_id: str
    skill_name: str
    title: str
    description: Optional[str] = None
    scheduled_start: datetime
    scheduled_end: datetime
    timezone: str = "UTC"
    session_type: str = "video"
    learning_objectives: List[str] = []
    skill_coins_paid: int = 0


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    timezone: Optional[str] = None
    session_type: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    notes: Optional[str] = None
    meeting_link: Optional[str] = None
    homework_assigned: Optional[str] = None
    homework_completed: Optional[bool] = None
    objectives_completed: Optional[List[str]] = None


class SkillCreate(BaseModel):
    name: str
    category: str
    subcategory: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []


class UserSkillCreate(BaseModel):
    skill_id: str
    skill_name: str
    level: SkillLevel
    years_experience: Optional[int] = None
    certifications: List[str] = []
    portfolio_items: List[str] = []
    self_assessment: Optional[str] = None


class SessionCreate(BaseModel):
    teacher_id: str
    skill_id: str
    skill_name: str
    title: str
    description: Optional[str] = None
    scheduled_start: datetime
    scheduled_end: datetime
    timezone: str
    session_type: str = "video"
    learning_objectives: List[str] = []
    skill_coins_cost: int


class MessageCreate(BaseModel):
    recipient_id: str
    session_id: Optional[str] = None
    content: str
    message_type: MessageType = MessageType.TEXT
    file_data: Optional[str] = None
    file_name: Optional[str] = None
    reply_to: Optional[str] = None


class ReviewCreate(BaseModel):
    reviewee_id: str
    session_id: str
    rating: float = Field(ge=1, le=5)
    comment: Optional[str] = None
    skills_learned: List[str] = []
    would_recommend: bool = True


class MatchFilters(BaseModel):
    skills_offered: Optional[List[str]] = None
    skills_wanted: Optional[List[str]] = None
    skill_level: Optional[SkillLevel] = None
    location: Optional[str] = None
    languages: Optional[List[str]] = None
    min_rating: Optional[float] = None
    availability: Optional[Dict[str, Any]] = None
    max_distance: Optional[int] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None
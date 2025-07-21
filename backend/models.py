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
    
    # Whiteboard data
    whiteboard_data: Optional[Dict[str, Any]] = None
    
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


# Gamification Models
class BadgeType(str, Enum):
    SKILL_MASTER = "skill_master"
    MENTOR = "mentor"
    LEARNER = "learner"
    SOCIAL = "social"
    MILESTONE = "milestone"
    SPECIAL = "special"


class AchievementType(str, Enum):
    SKILL_EARNED = "skill_earned"
    SESSIONS_COMPLETED = "sessions_completed"
    MENTORING_MILESTONE = "mentoring_milestone"
    LEARNING_MILESTONE = "learning_milestone"
    SOCIAL_MILESTONE = "social_milestone"
    RATING_MILESTONE = "rating_milestone"
    STREAK_MILESTONE = "streak_milestone"


class Badge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    badge_type: BadgeType
    icon_url: Optional[str] = None
    icon_data: Optional[str] = None  # base64 encoded icon
    color: str = "#3B82F6"  # default blue color
    requirements: Dict[str, Any] = {}  # e.g., {"sessions_completed": 10}
    skill_coins_reward: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserBadge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    badge_id: str
    earned_at: datetime = Field(default_factory=datetime.utcnow)
    progress: Dict[str, Any] = {}  # Progress towards badge requirements
    is_displayed: bool = True  # Whether user displays this badge


class Achievement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    achievement_type: AchievementType
    icon_url: Optional[str] = None
    icon_data: Optional[str] = None  # base64 encoded icon
    color: str = "#10B981"  # default green color
    requirements: Dict[str, Any] = {}
    skill_coins_reward: int = 0
    badge_reward_id: Optional[str] = None  # Badge awarded with this achievement
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserAchievement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    achievement_id: str
    earned_at: datetime = Field(default_factory=datetime.utcnow)
    progress: Dict[str, Any] = {}  # Progress towards achievement
    is_notified: bool = False  # Whether user has been notified


class LeaderboardEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    username: str
    skill_coins: int = 0
    total_sessions: int = 0
    teaching_sessions: int = 0
    learning_sessions: int = 0
    average_rating: float = 0.0
    badges_count: int = 0
    achievements_count: int = 0
    current_streak: int = 0  # Days active streak
    longest_streak: int = 0
    last_active: datetime = Field(default_factory=datetime.utcnow)
    rank: int = 0  # Position in leaderboard
    rank_change: int = 0  # Change from previous period


class SkillCoinTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    amount: int  # Positive for earned, negative for spent
    transaction_type: str  # "earned", "spent", "bonus", "refund"
    source: str  # "session_completed", "achievement", "badge", "admin"
    source_id: Optional[str] = None  # ID of session, achievement, etc.
    description: str
    balance_after: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Gamification Request/Response Models
class BadgeCreate(BaseModel):
    name: str
    description: str
    badge_type: BadgeType
    icon_data: Optional[str] = None
    color: str = "#3B82F6"
    requirements: Dict[str, Any] = {}
    skill_coins_reward: int = 0


class AchievementCreate(BaseModel):
    name: str
    description: str
    achievement_type: AchievementType
    icon_data: Optional[str] = None
    color: str = "#10B981"
    requirements: Dict[str, Any] = {}
    skill_coins_reward: int = 0
    badge_reward_id: Optional[str] = None


class UserProgress(BaseModel):
    user_id: str
    skill_coins: int
    total_sessions: int
    teaching_sessions: int
    learning_sessions: int
    average_rating: float
    badges: List[UserBadge]
    achievements: List[UserAchievement]
    current_streak: int
    longest_streak: int
    leaderboard_rank: int
    recent_activities: List[Dict[str, Any]]


# Community Models
class PostType(str, Enum):
    DISCUSSION = "discussion"
    QUESTION = "question"
    SHOWCASE = "showcase"
    TUTORIAL = "tutorial"
    RESOURCE = "resource"
    TESTIMONIAL = "testimonial"


class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    MODERATED = "moderated"


class GroupType(str, Enum):
    SKILL_BASED = "skill_based"
    STUDY_GROUP = "study_group"
    PROJECT_TEAM = "project_team"
    GENERAL = "general"


class GroupPrivacy(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    INVITE_ONLY = "invite_only"


class Forum(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    skill_id: Optional[str] = None  # Link to specific skill
    skill_name: Optional[str] = None
    category: str
    icon: Optional[str] = None  # Icon identifier or base64
    color: str = "#3B82F6"
    is_active: bool = True
    created_by: str  # User ID
    moderators: List[str] = []  # User IDs
    
    # Statistics
    posts_count: int = 0
    members_count: int = 0
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Post(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    post_type: PostType
    status: PostStatus = PostStatus.PUBLISHED
    
    # Author and location
    author_id: str
    forum_id: str
    group_id: Optional[str] = None
    
    # Rich content
    images: List[str] = []  # base64 encoded images
    attachments: List[Dict[str, Any]] = []  # files with metadata
    tags: List[str] = []
    
    # Engagement
    likes: List[str] = []  # User IDs who liked
    views: int = 0
    is_pinned: bool = False
    is_featured: bool = False
    
    # Discussion
    comments_count: int = 0
    last_reply_at: Optional[datetime] = None
    last_reply_by: Optional[str] = None
    
    # Showcase specific
    project_url: Optional[str] = None
    demo_url: Optional[str] = None
    github_url: Optional[str] = None
    skills_demonstrated: List[str] = []
    
    # Tutorial specific
    difficulty_level: Optional[str] = None  # beginner, intermediate, advanced
    estimated_time: Optional[str] = None
    prerequisites: List[str] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    author_id: str
    post_id: str
    parent_comment_id: Optional[str] = None  # For nested comments
    
    # Rich content
    images: List[str] = []  # base64 encoded
    attachments: List[Dict[str, Any]] = []
    
    # Engagement
    likes: List[str] = []  # User IDs who liked
    is_solution: bool = False  # Mark as solution for questions
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Group(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    group_type: GroupType
    privacy: GroupPrivacy = GroupPrivacy.PUBLIC
    
    # Skills and focus
    skills_focus: List[str] = []  # Skill names or IDs
    category: str
    
    # Visual
    image: Optional[str] = None  # base64 encoded group image
    color: str = "#10B981"
    
    # Membership
    created_by: str  # User ID
    moderators: List[str] = []  # User IDs
    members: List[str] = []  # User IDs
    pending_requests: List[str] = []  # User IDs for private groups
    max_members: Optional[int] = None
    
    # Activity
    posts_count: int = 0
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    # Study group specific
    schedule: Optional[Dict[str, Any]] = {}  # Meeting times, etc.
    learning_goals: List[str] = []
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GroupMembership(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    group_id: str
    role: str = "member"  # member, moderator, admin
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class Testimonial(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    author_id: str  # Who wrote the testimonial
    subject_id: str  # Who the testimonial is about
    session_id: Optional[str] = None  # Related session
    
    content: str
    rating: float = Field(ge=1, le=5)
    skills_mentioned: List[str] = []
    highlights: List[str] = []  # Key achievements or qualities
    
    # Visibility
    is_featured: bool = False
    is_approved: bool = True
    is_public: bool = True
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class KnowledgeBase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4))
    title: str
    content: str
    category: str
    subcategory: Optional[str] = None
    
    # Author and contribution
    author_id: str
    contributors: List[str] = []  # User IDs who contributed
    
    # Organization
    tags: List[str] = []
    skill_ids: List[str] = []  # Related skills
    difficulty_level: str = "beginner"  # beginner, intermediate, advanced
    
    # Content structure
    sections: List[Dict[str, Any]] = []  # Structured content sections
    resources: List[Dict[str, Any]] = []  # External links, files, etc.
    
    # Engagement
    views: int = 0
    likes: List[str] = []  # User IDs
    bookmarks: List[str] = []  # User IDs who bookmarked
    
    # Quality
    is_verified: bool = False
    verification_by: Optional[str] = None  # Moderator/expert who verified
    last_reviewed: Optional[datetime] = None
    
    # Version control
    version: str = "1.0"
    change_log: List[Dict[str, Any]] = []
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Community API Models
class ForumCreate(BaseModel):
    name: str
    description: str
    skill_id: Optional[str] = None
    skill_name: Optional[str] = None
    category: str
    icon: Optional[str] = None
    color: str = "#3B82F6"


class PostCreate(BaseModel):
    title: str
    content: str
    post_type: PostType
    forum_id: str
    group_id: Optional[str] = None
    images: List[str] = []
    attachments: List[Dict[str, Any]] = []
    tags: List[str] = []
    
    # Showcase specific
    project_url: Optional[str] = None
    demo_url: Optional[str] = None
    github_url: Optional[str] = None
    skills_demonstrated: List[str] = []
    
    # Tutorial specific
    difficulty_level: Optional[str] = None
    estimated_time: Optional[str] = None
    prerequisites: List[str] = []


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    images: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None
    is_pinned: Optional[bool] = None
    is_featured: Optional[bool] = None
    
    # Showcase specific
    project_url: Optional[str] = None
    demo_url: Optional[str] = None
    github_url: Optional[str] = None
    skills_demonstrated: Optional[List[str]] = None
    
    # Tutorial specific
    difficulty_level: Optional[str] = None
    estimated_time: Optional[str] = None
    prerequisites: Optional[List[str]] = None


class CommentCreate(BaseModel):
    content: str
    post_id: str
    parent_comment_id: Optional[str] = None
    images: List[str] = []
    attachments: List[Dict[str, Any]] = []


class GroupCreate(BaseModel):
    name: str
    description: str
    group_type: GroupType
    privacy: GroupPrivacy = GroupPrivacy.PUBLIC
    skills_focus: List[str] = []
    category: str
    image: Optional[str] = None
    color: str = "#10B981"
    max_members: Optional[int] = None
    
    # Study group specific
    schedule: Optional[Dict[str, Any]] = {}
    learning_goals: List[str] = []


class TestimonialCreate(BaseModel):
    subject_id: str  # Who the testimonial is about
    session_id: Optional[str] = None
    content: str
    rating: float = Field(ge=1, le=5)
    skills_mentioned: List[str] = []
    highlights: List[str] = []
    is_public: bool = True


class KnowledgeBaseCreate(BaseModel):
    title: str
    content: str
    category: str
    subcategory: Optional[str] = None
    tags: List[str] = []
    skill_ids: List[str] = []
    difficulty_level: str = "beginner"
    sections: List[Dict[str, Any]] = []
    resources: List[Dict[str, Any]] = []


# Community Response Models
class ForumResponse(BaseModel):
    id: str
    name: str
    description: str
    skill_id: Optional[str]
    skill_name: Optional[str]
    category: str
    icon: Optional[str]
    color: str
    posts_count: int
    members_count: int
    last_activity: datetime
    created_at: datetime


class PostResponse(BaseModel):
    id: str
    title: str
    content: str
    post_type: PostType
    status: PostStatus
    author_id: str
    author_name: str
    author_avatar: Optional[str]
    forum_id: str
    forum_name: str
    group_id: Optional[str]
    group_name: Optional[str]
    images: List[str]
    attachments: List[Dict[str, Any]]
    tags: List[str]
    likes_count: int
    views: int
    comments_count: int
    is_pinned: bool
    is_featured: bool
    last_reply_at: Optional[datetime]
    last_reply_by: Optional[str]
    
    # Showcase specific
    project_url: Optional[str]
    demo_url: Optional[str]
    github_url: Optional[str]
    skills_demonstrated: List[str]
    
    # Tutorial specific
    difficulty_level: Optional[str]
    estimated_time: Optional[str]
    prerequisites: List[str]
    
    created_at: datetime
    updated_at: datetime


# Notification System Models
class NotificationType(str, Enum):
    MATCH_FOUND = "match_found"
    SESSION_REMINDER = "session_reminder"
    SESSION_STARTED = "session_started"
    SESSION_COMPLETED = "session_completed"
    MESSAGE_RECEIVED = "message_received"
    ACHIEVEMENT_EARNED = "achievement_earned"
    BADGE_EARNED = "badge_earned"
    SKILL_ENDORSED = "skill_endorsed"
    COMMUNITY_POST_LIKE = "community_post_like"
    COMMUNITY_POST_COMMENT = "community_post_comment"
    GROUP_INVITATION = "group_invitation"
    RECOMMENDATION_AVAILABLE = "recommendation_available"
    SYSTEM_ANNOUNCEMENT = "system_announcement"


class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    notification_type: NotificationType
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    data: Dict[str, Any] = {}  # Additional contextual data
    is_read: bool = False
    is_sent_via_email: bool = False
    scheduled_for: Optional[datetime] = None  # For scheduled notifications
    expires_at: Optional[datetime] = None  # Auto-delete after this time
    action_url: Optional[str] = None  # Deep link for notification action
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None


class NotificationPreferences(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email_notifications: bool = True
    push_notifications: bool = True
    sms_notifications: bool = False
    
    # Specific notification types
    match_notifications: bool = True
    session_reminders: bool = True
    message_notifications: bool = True
    achievement_notifications: bool = True
    community_notifications: bool = True
    system_announcements: bool = True
    
    # Frequency settings
    digest_frequency: str = "daily"  # "never", "daily", "weekly"
    quiet_hours_start: Optional[str] = "22:00"  # 24h format
    quiet_hours_end: Optional[str] = "08:00"
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RecommendationType(str, Enum):
    SKILL_LEARNING = "skill_learning"
    SKILL_TEACHING = "skill_teaching"
    USER_MATCH = "user_match"
    SESSION_TIMING = "session_timing"
    COMMUNITY_CONTENT = "community_content"
    LEARNING_PATH = "learning_path"
    GOAL_SUGGESTION = "goal_suggestion"


class Recommendation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    recommendation_type: RecommendationType
    title: str
    description: str
    confidence_score: float = Field(ge=0.0, le=1.0)  # AI confidence in recommendation
    data: Dict[str, Any] = {}  # Recommendation specific data
    is_viewed: bool = False
    is_dismissed: bool = False
    is_acted_upon: bool = False
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    viewed_at: Optional[datetime] = None
    acted_at: Optional[datetime] = None


class LearningGoal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    skill_id: str
    skill_name: str
    target_level: SkillLevel
    current_progress: float = 0.0  # 0.0 to 100.0
    target_date: Optional[datetime] = None
    weekly_session_target: int = 2  # Sessions per week
    is_active: bool = True
    milestones: List[Dict[str, Any]] = []  # Progress milestones
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class UserAnalytics(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    period: str  # "daily", "weekly", "monthly"
    period_start: datetime
    period_end: datetime
    
    # Learning metrics
    sessions_attended: int = 0
    sessions_taught: int = 0
    hours_learned: float = 0.0
    hours_taught: float = 0.0
    skills_improved: List[str] = []
    new_connections: int = 0
    
    # Engagement metrics
    login_days: int = 0
    messages_sent: int = 0
    community_posts: int = 0
    community_comments: int = 0
    
    # Achievement metrics
    badges_earned: int = 0
    achievements_unlocked: int = 0
    skill_coins_earned: int = 0
    
    # Calculated scores
    engagement_score: float = 0.0
    learning_velocity: float = 0.0
    teaching_impact: float = 0.0
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Request/Response Models for Notifications
class NotificationCreate(BaseModel):
    user_id: str
    notification_type: NotificationType
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    data: Dict[str, Any] = {}
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    action_url: Optional[str] = None


class NotificationResponse(BaseModel):
    id: str
    notification_type: NotificationType
    title: str
    message: str
    priority: NotificationPriority
    data: Dict[str, Any]
    is_read: bool
    action_url: Optional[str]
    created_at: datetime
    time_ago: str  # Human readable time ago


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_dismissed: Optional[bool] = None


class RecommendationCreate(BaseModel):
    user_id: str
    recommendation_type: RecommendationType
    title: str
    description: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    data: Dict[str, Any] = {}
    expires_at: Optional[datetime] = None


class RecommendationResponse(BaseModel):
    id: str
    recommendation_type: RecommendationType
    title: str
    description: str
    confidence_score: float
    data: Dict[str, Any]
    is_viewed: bool
    is_dismissed: bool
    is_acted_upon: bool
    created_at: datetime
    time_ago: str


class LearningGoalCreate(BaseModel):
    skill_id: str
    target_level: SkillLevel
    target_date: Optional[datetime] = None
    weekly_session_target: int = 2


class LearningGoalUpdate(BaseModel):
    target_level: Optional[SkillLevel] = None
    target_date: Optional[datetime] = None
    weekly_session_target: Optional[int] = None
    current_progress: Optional[float] = None
    is_active: Optional[bool] = None


# AI Learning Companion Models
class AIConversationType(str, Enum):
    LEARNING_ASSISTANCE = "learning_assistance"
    SESSION_ANALYSIS = "session_analysis"
    SKILL_GUIDANCE = "skill_guidance"
    PRACTICE_FEEDBACK = "practice_feedback"
    CAREER_ADVICE = "career_advice"
    GENERAL_HELP = "general_help"


class AIMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    user_id: str
    role: str  # "user" or "assistant"
    content: str
    context_data: Dict[str, Any] = {}  # Session data, skill info, etc.
    ai_confidence: Optional[float] = None  # AI confidence in response
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata for learning analytics
    conversation_type: Optional[AIConversationType] = None
    skill_context: Optional[str] = None  # Skill being discussed
    session_context: Optional[str] = None  # Session being analyzed


class AIConversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    conversation_type: AIConversationType
    title: str
    summary: Optional[str] = None  # AI-generated summary
    
    # Context and metadata
    skill_context: Optional[str] = None
    session_context: Optional[str] = None
    learning_goal_context: Optional[str] = None
    
    # Conversation state
    is_active: bool = True
    message_count: int = 0
    last_message_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Analytics
    user_satisfaction_rating: Optional[float] = None  # 1-5 rating
    topics_discussed: List[str] = []
    insights_generated: List[str] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SessionAnalysis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str  # Can be teacher or learner
    
    # AI Analysis Results
    transcript: Optional[str] = None  # Session transcript
    summary: str  # AI-generated session summary
    key_topics_covered: List[str] = []
    learning_objectives_achieved: List[str] = []
    knowledge_gaps_identified: List[str] = []
    
    # Performance Analysis
    comprehension_score: Optional[float] = None  # 0-100
    engagement_score: Optional[float] = None  # 0-100
    participation_score: Optional[float] = None  # 0-100
    
    # Personalized Insights
    strengths_identified: List[str] = []
    areas_for_improvement: List[str] = []
    next_steps_suggested: List[str] = []
    practice_recommendations: List[str] = []
    
    # Follow-up Actions
    homework_suggested: Optional[str] = None
    resources_recommended: List[Dict[str, str]] = []  # {"title", "url", "type"}
    skills_to_practice: List[str] = []
    
    # AI Processing Metadata
    ai_model_used: str = "webllm"
    analysis_confidence: float = 0.0  # AI confidence in analysis
    processing_time: Optional[float] = None  # Time taken for analysis
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_reviewed: bool = False  # Whether user has reviewed the analysis


class LearningInsight(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    insight_type: str  # "skill_progress", "learning_pattern", "goal_achievement", etc.
    title: str
    description: str
    
    # Context and Data
    skill_context: Optional[str] = None
    session_context: Optional[str] = None
    time_period: Optional[str] = None  # "last_week", "last_month", etc.
    data_points: Dict[str, Any] = {}  # Supporting data for the insight
    
    # Recommendations
    action_items: List[str] = []
    resource_suggestions: List[Dict[str, str]] = []
    next_milestone: Optional[str] = None
    
    # Engagement
    is_viewed: bool = False
    is_helpful: Optional[bool] = None  # User feedback
    user_notes: Optional[str] = None
    
    # AI Metadata
    confidence_score: float = 0.0
    generated_by: str = "webllm"
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    viewed_at: Optional[datetime] = None


class SkillAssessment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    skill_id: str
    skill_name: str
    
    # Assessment Details
    assessment_type: str  # "ai_generated", "peer_review", "self_assessment"
    questions: List[Dict[str, Any]] = []  # Assessment questions and answers
    
    # Results
    score: float = 0.0  # 0-100
    level_assessment: SkillLevel
    strengths: List[str] = []
    weaknesses: List[str] = []
    
    # Recommendations
    study_plan: List[str] = []
    recommended_sessions: List[str] = []
    practice_exercises: List[str] = []
    
    # Progress Tracking
    previous_score: Optional[float] = None
    improvement_rate: Optional[float] = None
    time_to_next_level: Optional[int] = None  # Estimated days
    
    # AI Analysis
    ai_confidence: float = 0.0
    assessment_notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class StudyPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    skill_id: str
    skill_name: str
    target_level: SkillLevel
    current_level: SkillLevel
    
    # Plan Details
    title: str
    description: str
    estimated_duration_weeks: int
    
    # Learning Path
    modules: List[Dict[str, Any]] = []  # Structured learning modules
    milestones: List[Dict[str, Any]] = []  # Progress checkpoints
    resources: List[Dict[str, str]] = []  # External resources
    
    # Schedule
    weekly_time_commitment: int = 5  # Hours per week
    preferred_session_length: int = 60  # Minutes
    flexibility_level: str = "medium"  # "low", "medium", "high"
    
    # Progress Tracking
    current_module: int = 0
    completion_percentage: float = 0.0
    modules_completed: List[int] = []
    
    # AI Personalization
    generated_by: str = "webllm"
    personalization_factors: Dict[str, Any] = {}
    adaptation_history: List[Dict[str, Any]] = []  # How plan was adapted over time
    
    # Status
    is_active: bool = True
    is_paused: bool = False
    pause_reason: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class LearningAnalytics(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    period_type: str  # "daily", "weekly", "monthly", "quarterly"
    period_start: datetime
    period_end: datetime
    
    # Learning Metrics
    total_study_time: float = 0.0  # Hours
    sessions_completed: int = 0
    sessions_taught: int = 0
    skills_practiced: List[str] = []
    
    # Progress Metrics
    skill_improvements: Dict[str, float] = {}  # skill_name -> improvement_score
    goals_achieved: int = 0
    milestones_reached: int = 0
    assessments_completed: int = 0
    
    # Engagement Metrics
    ai_conversations: int = 0
    insights_viewed: int = 0
    recommendations_followed: int = 0
    study_plan_adherence: float = 0.0  # 0-100%
    
    # Performance Indicators
    avg_comprehension_score: float = 0.0
    avg_engagement_score: float = 0.0
    learning_velocity: float = 0.0  # Rate of skill acquisition
    consistency_score: float = 0.0  # How consistent the learning pattern is
    
    # AI-Generated Insights
    key_insights: List[str] = []
    recommendations: List[str] = []
    trends_identified: List[str] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# AI Companion Request/Response Models
class AIMessageCreate(BaseModel):
    conversation_id: Optional[str] = None  # If None, creates new conversation
    conversation_type: AIConversationType = AIConversationType.GENERAL_HELP
    content: str
    context_data: Dict[str, Any] = {}
    skill_context: Optional[str] = None
    session_context: Optional[str] = None


class AIMessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    ai_confidence: Optional[float]
    created_at: datetime
    conversation_type: AIConversationType
    skill_context: Optional[str]
    session_context: Optional[str]


class AIConversationResponse(BaseModel):
    id: str
    conversation_type: AIConversationType
    title: str
    summary: Optional[str]
    message_count: int
    last_message_at: datetime
    topics_discussed: List[str]
    created_at: datetime
    is_active: bool


class SessionAnalysisCreate(BaseModel):
    session_id: str
    transcript: Optional[str] = None
    additional_context: Dict[str, Any] = {}


class SessionAnalysisResponse(BaseModel):
    id: str
    session_id: str
    summary: str
    key_topics_covered: List[str]
    learning_objectives_achieved: List[str]
    knowledge_gaps_identified: List[str]
    comprehension_score: Optional[float]
    engagement_score: Optional[float]
    strengths_identified: List[str]
    areas_for_improvement: List[str]
    next_steps_suggested: List[str]
    practice_recommendations: List[str]
    homework_suggested: Optional[str]
    resources_recommended: List[Dict[str, str]]
    analysis_confidence: float
    created_at: datetime


class LearningInsightResponse(BaseModel):
    id: str
    insight_type: str
    title: str
    description: str
    action_items: List[str]
    resource_suggestions: List[Dict[str, str]]
    confidence_score: float
    created_at: datetime
    is_viewed: bool


class SkillAssessmentCreate(BaseModel):
    skill_id: str
    assessment_type: str = "ai_generated"
    questions: List[Dict[str, Any]] = []


class StudyPlanCreate(BaseModel):
    skill_id: str
    target_level: SkillLevel
    estimated_duration_weeks: Optional[int] = 8
    weekly_time_commitment: Optional[int] = 5
    preferred_session_length: Optional[int] = 60
    flexibility_level: Optional[str] = "medium"
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
import os
from models import User, UserCreate, UserLogin, UserResponse, Token, TokenData
import uuid
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTPBearer for token extraction
security = HTTPBearer()

class AuthService:
    def __init__(self, db: AsyncIOMotorClient):
        self.db = db
        self.users_collection = db.users
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user_data = await self.users_collection.find_one({"email": email})
        if not user_data:
            return None
        
        user = User(**user_data)
        if not self.verify_password(password, user.password_hash):
            return None
        
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        user_data = await self.users_collection.find_one({"email": email})
        if not user_data:
            return None
        return User(**user_data)
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        user_data = await self.users_collection.find_one({"id": user_id})
        if not user_data:
            return None
        return User(**user_data)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        user_data = await self.users_collection.find_one({"username": username})
        if not user_data:
            return None
        return User(**user_data)
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        existing_username = await self.get_user_by_username(user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        user_dict = user_data.dict()
        user_dict["id"] = str(uuid.uuid4())
        user_dict["password_hash"] = self.get_password_hash(user_data.password)
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()
        
        # Remove plain password
        del user_dict["password"]
        
        # Set default values
        user_dict.update({
            "is_active": True,
            "is_verified": False,
            "skills_offered": [],
            "skills_wanted": [],
            "availability": {},
            "languages": [],
            "skill_coins": 100,
            "experience_points": 0,
            "level": 1,
            "badges": [],
            "sessions_taught": 0,
            "sessions_learned": 0,
            "total_rating": 0.0,
            "rating_count": 0,
        })
        
        user = User(**user_dict)
        
        # Insert into database
        await self.users_collection.insert_one(user.dict())
        
        return user
    
    async def login_user(self, login_data: UserLogin) -> Token:
        """Login user and return JWT token"""
        user = await self.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": user.email, "user_id": user.id}, 
            expires_delta=access_token_expires
        )
        
        user_dict = user.dict()
        user_dict["average_rating"] = user.average_rating
        user_response = UserResponse(**user_dict)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
    
    async def get_current_user(self, token: str) -> User:
        """Get current user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            if email is None or user_id is None:
                raise credentials_exception
            token_data = TokenData(email=email, user_id=user_id)
        except JWTError:
            raise credentials_exception
        
        user = await self.get_user_by_email(email=token_data.email)
        if user is None:
            raise credentials_exception
        
        return user
    
    async def update_user_stats(self, user_id: str, stats_update: Dict[str, Any]):
        """Update user statistics"""
        update_data = {
            "updated_at": datetime.utcnow(),
            **stats_update
        }
        
        await self.users_collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
    
    async def add_skill_coins(self, user_id: str, amount: int):
        """Add skill coins to user account"""
        await self.users_collection.update_one(
            {"id": user_id},
            {"$inc": {"skill_coins": amount}, "$set": {"updated_at": datetime.utcnow()}}
        )
    
    async def deduct_skill_coins(self, user_id: str, amount: int) -> bool:
        """Deduct skill coins from user account"""
        user = await self.get_user_by_id(user_id)
        if not user or user.skill_coins < amount:
            return False
        
        await self.users_collection.update_one(
            {"id": user_id},
            {"$inc": {"skill_coins": -amount}, "$set": {"updated_at": datetime.utcnow()}}
        )
        return True
    
    async def add_experience_points(self, user_id: str, amount: int):
        """Add experience points and update level"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return
        
        new_exp = user.experience_points + amount
        new_level = self.calculate_level(new_exp)
        
        await self.users_collection.update_one(
            {"id": user_id},
            {
                "$set": {
                    "experience_points": new_exp,
                    "level": new_level,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    def calculate_level(self, experience_points: int) -> int:
        """Calculate user level based on experience points"""
        # Level formula: level = floor(sqrt(exp / 100)) + 1
        import math
        return int(math.sqrt(experience_points / 100)) + 1
    
    async def add_badge(self, user_id: str, badge_name: str):
        """Add badge to user"""
        await self.users_collection.update_one(
            {"id": user_id},
            {
                "$addToSet": {"badges": badge_name},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
    
    async def generate_reset_token(self, email: str) -> Optional[str]:
        """Generate password reset token"""
        try:
            # Check if user exists
            user = await self.get_user_by_email(email)
            if not user:
                return None
            
            # Generate reset token (valid for 1 hour)
            reset_token_expires = timedelta(hours=1)
            reset_token = self.create_access_token(
                data={"sub": email, "user_id": user.id, "type": "reset"},
                expires_delta=reset_token_expires
            )
            
            # Store reset token in database (in production, consider using Redis or similar)
            await self.users_collection.update_one(
                {"id": user.id},
                {
                    "$set": {
                        "reset_token": reset_token,
                        "reset_token_expires": datetime.utcnow() + reset_token_expires,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return reset_token
            
        except Exception as e:
            logger.error(f"Error generating reset token: {str(e)}")
            return None
    
    async def reset_password(self, reset_token: str, new_password: str) -> bool:
        """Reset password using reset token"""
        try:
            # Validate reset token
            payload = jwt.decode(reset_token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            token_type: str = payload.get("type")
            
            if not email or not user_id or token_type != "reset":
                return False
            
            # Get user and verify reset token
            user_data = await self.users_collection.find_one({"id": user_id})
            if not user_data:
                return False
            
            user = User(**user_data)
            
            # Check if token matches and is not expired
            if (user_data.get("reset_token") != reset_token or 
                not user_data.get("reset_token_expires") or
                user_data.get("reset_token_expires") < datetime.utcnow()):
                return False
            
            # Hash new password and update user
            hashed_password = self.get_password_hash(new_password)
            
            await self.users_collection.update_one(
                {"id": user_id},
                {
                    "$set": {
                        "password_hash": hashed_password,
                        "updated_at": datetime.utcnow()
                    },
                    "$unset": {
                        "reset_token": "",
                        "reset_token_expires": ""
                    }
                }
            )
            
            return True
            
        except JWTError:
            logger.error("Invalid reset token")
            return False
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            return False


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorClient = Depends(lambda: None)  # Will be injected
) -> User:
    """Dependency to get current authenticated user"""
    # This will be properly injected in the routes
    pass


# Dependency to get current active user
async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Optional dependency for routes that can work with or without authentication
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncIOMotorClient = Depends(lambda: None)  # Will be injected
) -> Optional[User]:
    """Optional dependency to get current user (returns None if not authenticated)"""
    if not credentials:
        return None
    
    # This will be properly injected in the routes
    pass
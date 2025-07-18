from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorClient
from models import UserCreate, UserLogin, UserResponse, Token, User
from auth import AuthService
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

def create_auth_router(db: AsyncIOMotorClient) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["Authentication"])
    auth_service = AuthService(db)
    
    @router.post("/register", response_model=Token)
    async def register(user_data: UserCreate):
        """Register a new user"""
        try:
            user = await auth_service.create_user(user_data)
            login_data = UserLogin(email=user_data.email, password=user_data.password)
            token = await auth_service.login_user(login_data)
            return token
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @router.post("/login", response_model=Token)
    async def login(login_data: UserLogin):
        """Login user"""
        try:
            token = await auth_service.login_user(login_data)
            return token
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
    
    @router.get("/me", response_model=UserResponse)
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current user profile"""
        try:
            token = credentials.credentials
            user = await auth_service.get_current_user(token)
            return UserResponse(**user.dict())
        except Exception as e:
            logger.error(f"Get current user error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    @router.post("/refresh", response_model=Token)
    async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Refresh access token"""
        try:
            token = credentials.credentials
            user = await auth_service.get_current_user(token)
            
            # Create new token
            from datetime import timedelta
            access_token_expires = timedelta(minutes=30 * 24 * 60)  # 30 days
            access_token = auth_service.create_access_token(
                data={"sub": user.email, "user_id": user.id},
                expires_delta=access_token_expires
            )
            
            user_response = UserResponse(**user.dict())
            
            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=30 * 24 * 60 * 60,  # 30 days in seconds
                user=user_response
            )
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not refresh token"
            )
    
    @router.post("/logout")
    async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Logout user (client-side token removal)"""
        # In a real implementation, you might want to blacklist the token
        return {"message": "Successfully logged out"}
    
    return router
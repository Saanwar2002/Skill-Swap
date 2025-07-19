from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging

from auth import get_current_user
from models import (
    User, ForumCreate, PostCreate, PostUpdate, CommentCreate, GroupCreate,
    TestimonialCreate, KnowledgeBaseCreate, Forum, Post, Comment, Group,
    Testimonial, KnowledgeBase, ForumResponse, PostResponse, PostType, GroupType
)
from services.community_service import CommunityService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_community_router(db):
    """Create community router with database dependency"""
    router = APIRouter(prefix="/api/community", tags=["community"])
    
    def get_community_service():
        return CommunityService(db)

    # Forum Endpoints
    @router.get("/forums", response_model=List[ForumResponse])
    async def get_forums(
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Get all forums"""
        try:
            forums = await community_service.get_forums(skip=skip, limit=limit)
            return forums
        except Exception as e:
            logger.error(f"Error fetching forums: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch forums")


    @router.post("/forums", response_model=Forum)
    async def create_forum(
        forum_data: ForumCreate,
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Create a new forum"""
        try:
            forum = await community_service.create_forum(forum_data, current_user.id)
            return forum
        except Exception as e:
            logger.error(f"Error creating forum: {e}")
            raise HTTPException(status_code=500, detail="Failed to create forum")


    @router.get("/forums/{forum_id}", response_model=ForumResponse)
    async def get_forum(
        forum_id: str,
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Get a specific forum"""
        try:
            forum = await community_service.get_forum_by_id(forum_id)
            if not forum:
                raise HTTPException(status_code=404, detail="Forum not found")
            return forum
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching forum {forum_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch forum")


    # Post Endpoints
    @router.get("/posts", response_model=List[PostResponse])
    async def get_posts(
        forum_id: Optional[str] = Query(None),
        group_id: Optional[str] = Query(None),
        post_type: Optional[PostType] = Query(None),
        author_id: Optional[str] = Query(None),
        tag: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Get posts with filtering options"""
        try:
            posts = await community_service.get_posts(
                forum_id=forum_id,
                group_id=group_id,
                post_type=post_type,
                author_id=author_id,
                tag=tag,
                search=search,
                skip=skip,
                limit=limit
            )
            return posts
        except Exception as e:
            logger.error(f"Error fetching posts: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch posts")


    @router.post("/posts", response_model=Post)
    async def create_post(
        post_data: PostCreate,
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Create a new post"""
        try:
            # Verify forum exists
            forum = await community_service.get_forum_by_id(post_data.forum_id)
            if not forum:
                raise HTTPException(status_code=404, detail="Forum not found")
            
            post = await community_service.create_post(post_data, current_user.id)
            return post
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            raise HTTPException(status_code=500, detail="Failed to create post")


    @router.get("/posts/{post_id}", response_model=PostResponse)
    async def get_post(
        post_id: str,
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Get a specific post"""
        try:
            post = await community_service.get_post_by_id(post_id)
            if not post:
                raise HTTPException(status_code=404, detail="Post not found")
            return post
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching post {post_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch post")


    @router.put("/posts/{post_id}", response_model=Post)
    async def update_post(
        post_id: str,
        post_data: PostUpdate,
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Update a post"""
        try:
            post = await community_service.update_post(post_id, post_data, current_user.id)
            if not post:
                raise HTTPException(status_code=404, detail="Post not found or permission denied")
            return post
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating post {post_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update post")


    @router.post("/posts/{post_id}/like")
    async def toggle_post_like(
        post_id: str,
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Toggle like on a post"""
        try:
            liked = await community_service.toggle_post_like(post_id, current_user.id)
            return {"liked": liked, "message": "Post liked" if liked else "Post unliked"}
        except Exception as e:
            logger.error(f"Error toggling like on post {post_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to toggle like")


    # Comment Endpoints
    @router.get("/posts/{post_id}/comments", response_model=List[Comment])
    async def get_comments(
        post_id: str,
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Get comments for a post"""
        try:
            comments = await community_service.get_comments_by_post(post_id, skip=skip, limit=limit)
            return comments
        except Exception as e:
            logger.error(f"Error fetching comments for post {post_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch comments")


    @router.post("/comments", response_model=Comment)
    async def create_comment(
        comment_data: CommentCreate,
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Create a new comment"""
        try:
            comment = await community_service.create_comment(comment_data, current_user.id)
            return comment
        except Exception as e:
            logger.error(f"Error creating comment: {e}")
            raise HTTPException(status_code=500, detail="Failed to create comment")


    @router.post("/comments/{comment_id}/like")
    async def toggle_comment_like(
        comment_id: str,
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Toggle like on a comment"""
        try:
            liked = await community_service.toggle_comment_like(comment_id, current_user.id)
            return {"liked": liked, "message": "Comment liked" if liked else "Comment unliked"}
        except Exception as e:
            logger.error(f"Error toggling like on comment {comment_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to toggle like")


    # Group Endpoints
    @router.get("/groups", response_model=List[Group])
    async def get_groups(
        group_type: Optional[GroupType] = Query(None),
        skill_focus: Optional[str] = Query(None),
        category: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Get groups with filtering"""
        try:
            groups = await community_service.get_groups(
                group_type=group_type,
                skill_focus=skill_focus,
                category=category,
                search=search,
                skip=skip,
                limit=limit
            )
            return groups
        except Exception as e:
            logger.error(f"Error fetching groups: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch groups")


    @router.post("/groups", response_model=Group)
    async def create_group(
        group_data: GroupCreate,
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Create a new group"""
        try:
            group = await community_service.create_group(group_data, current_user.id)
            return group
        except Exception as e:
            logger.error(f"Error creating group: {e}")
            raise HTTPException(status_code=500, detail="Failed to create group")


    @router.post("/groups/{group_id}/join")
    async def join_group(
        group_id: str,
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Join a group"""
        try:
            joined = await community_service.join_group(group_id, current_user.id)
            if joined:
                return {"message": "Successfully joined group"}
            else:
                return {"message": "Join request sent (pending approval for private groups)"}
        except Exception as e:
            logger.error(f"Error joining group {group_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to join group")


    # Testimonial Endpoints
    @router.get("/testimonials", response_model=List[Testimonial])
    async def get_testimonials(
        subject_id: Optional[str] = Query(None),
        author_id: Optional[str] = Query(None),
        featured_only: bool = Query(False),
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Get testimonials"""
        try:
            testimonials = await community_service.get_testimonials(
                subject_id=subject_id,
                author_id=author_id,
                featured_only=featured_only,
                skip=skip,
                limit=limit
            )
            return testimonials
        except Exception as e:
            logger.error(f"Error fetching testimonials: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch testimonials")


    @router.post("/testimonials", response_model=Testimonial)
    async def create_testimonial(
        testimonial_data: TestimonialCreate,
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Create a new testimonial"""
        try:
            testimonial = await community_service.create_testimonial(testimonial_data, current_user.id)
            return testimonial
        except Exception as e:
            logger.error(f"Error creating testimonial: {e}")
            raise HTTPException(status_code=500, detail="Failed to create testimonial")


    # Knowledge Base Endpoints
    @router.get("/knowledge-base", response_model=List[KnowledgeBase])
    async def get_knowledge_base(
        category: Optional[str] = Query(None),
        skill_id: Optional[str] = Query(None),
        difficulty_level: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Get knowledge base entries"""
        try:
            entries = await community_service.get_knowledge_base_entries(
                category=category,
                skill_id=skill_id,
                difficulty_level=difficulty_level,
                search=search,
                skip=skip,
                limit=limit
            )
            return entries
        except Exception as e:
            logger.error(f"Error fetching knowledge base entries: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch knowledge base entries")


    @router.post("/knowledge-base", response_model=KnowledgeBase)
    async def create_knowledge_base_entry(
        kb_data: KnowledgeBaseCreate,
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Create a new knowledge base entry"""
        try:
            entry = await community_service.create_knowledge_base_entry(kb_data, current_user.id)
            return entry
        except Exception as e:
            logger.error(f"Error creating knowledge base entry: {e}")
            raise HTTPException(status_code=500, detail="Failed to create knowledge base entry")


    # Analytics Endpoints
    @router.get("/stats")
    async def get_community_stats(
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Get community statistics"""
        try:
            stats = await community_service.get_community_stats()
            return stats
        except Exception as e:
            logger.error(f"Error fetching community stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch community stats")


    @router.get("/trending")
    async def get_trending_topics(
        days: int = Query(7, ge=1, le=30),
        current_user: User = Depends(get_current_user),
        community_service: CommunityService = Depends(get_community_service)
    ):
        """Get trending topics"""
        try:
            trending = await community_service.get_trending_topics(days=days)
            return {"trending_topics": trending}
        except Exception as e:
            logger.error(f"Error fetching trending topics: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch trending topics")
    
    return router
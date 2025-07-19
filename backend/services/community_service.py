from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import uuid

from models import (
    Forum, Post, Comment, Group, GroupMembership, Testimonial, KnowledgeBase,
    ForumCreate, PostCreate, PostUpdate, CommentCreate, GroupCreate,
    TestimonialCreate, KnowledgeBaseCreate, ForumResponse, PostResponse,
    PostType, PostStatus, GroupType, GroupPrivacy
)


class CommunityService:
    def __init__(self, db=None):
        if db is not None:
            # Use the provided database connection (from FastAPI dependency)
            self.db = db
        else:
            # Create our own connection for standalone usage
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            db_name = os.environ.get('DB_NAME', 'skillswap')
            self.client = AsyncIOMotorClient(mongo_url)
            self.db = self.client[db_name]
        
        # Collections
        self.forums_collection = self.db.forums
        self.posts_collection = self.db.posts
        self.comments_collection = self.db.comments
        self.groups_collection = self.db.groups
        self.group_memberships_collection = self.db.group_memberships
        self.testimonials_collection = self.db.testimonials
        self.knowledge_base_collection = self.db.knowledge_base
        self.users_collection = self.db.users

    async def initialize_default_forums(self):
        """Initialize default forums for popular skill categories"""
        default_forums = [
            {
                "name": "Programming & Development",
                "description": "Discuss programming languages, frameworks, and development practices",
                "category": "Technology",
                "icon": "💻",
                "color": "#3B82F6"
            },
            {
                "name": "Design & Creativity",
                "description": "Share design tips, showcase creative work, and get feedback",
                "category": "Creative",
                "icon": "🎨",
                "color": "#10B981"
            },
            {
                "name": "Business & Entrepreneurship",
                "description": "Business strategies, marketing, and entrepreneurship discussions",
                "category": "Business",
                "icon": "💼",
                "color": "#F59E0B"
            },
            {
                "name": "Languages & Communication",
                "description": "Practice languages, communication skills, and cultural exchange",
                "category": "Language",
                "icon": "🗣️",
                "color": "#EF4444"
            },
            {
                "name": "Science & Research",
                "description": "Scientific discussions, research methods, and academic collaboration",
                "category": "Academic",
                "icon": "🔬",
                "color": "#8B5CF6"
            },
            {
                "name": "Arts & Crafts",
                "description": "Traditional arts, crafts, music, and hands-on creative skills",
                "category": "Arts",
                "icon": "🎭",
                "color": "#EC4899"
            },
            {
                "name": "General Discussion",
                "description": "General skill-sharing discussions and community announcements",
                "category": "General",
                "icon": "💬",
                "color": "#6B7280"
            }
        ]
        
        # System user for creating default content
        system_user_id = "system"
        
        for forum_data in default_forums:
            existing = await self.forums_collection.find_one({"name": forum_data["name"]})
            if not existing:
                forum = Forum(
                    id=str(uuid.uuid4()),
                    name=forum_data["name"],
                    description=forum_data["description"],
                    category=forum_data["category"],
                    icon=forum_data["icon"],
                    color=forum_data["color"],
                    created_by=system_user_id,
                    moderators=[system_user_id]
                )
                await self.forums_collection.insert_one(forum.dict())

    # Forum Management
    async def create_forum(self, forum_data: ForumCreate, creator_id: str) -> Forum:
        """Create a new forum"""
        forum = Forum(
            **forum_data.dict(),
            created_by=creator_id,
            moderators=[creator_id]
        )
        
        await self.forums_collection.insert_one(forum.dict())
        return forum

    async def get_forums(self, skip: int = 0, limit: int = 20) -> List[ForumResponse]:
        """Get all active forums with statistics"""
        cursor = self.forums_collection.find({"is_active": True}).skip(skip).limit(limit)
        forums = []
        
        async for forum_doc in cursor:
            forum_dict = dict(forum_doc)
            forum_dict.pop('_id', None)
            
            # Get forum statistics
            forum_dict['posts_count'] = await self.posts_collection.count_documents({
                "forum_id": forum_dict['id'],
                "status": PostStatus.PUBLISHED
            })
            
            forums.append(ForumResponse(**forum_dict))
        
        return forums

    async def get_forum_by_id(self, forum_id: str) -> Optional[ForumResponse]:
        """Get forum by ID with statistics"""
        forum_doc = await self.forums_collection.find_one({"id": forum_id, "is_active": True})
        if not forum_doc:
            return None
        
        forum_dict = dict(forum_doc)
        forum_dict.pop('_id', None)
        
        # Get statistics
        forum_dict['posts_count'] = await self.posts_collection.count_documents({
            "forum_id": forum_id,
            "status": PostStatus.PUBLISHED
        })
        
        return ForumResponse(**forum_dict)

    # Post Management
    async def create_post(self, post_data: PostCreate, author_id: str) -> Post:
        """Create a new post"""
        post = Post(
            **post_data.dict(),
            author_id=author_id
        )
        
        await self.posts_collection.insert_one(post.dict())
        
        # Update forum statistics
        await self.forums_collection.update_one(
            {"id": post.forum_id},
            {
                "$inc": {"posts_count": 1},
                "$set": {"last_activity": datetime.utcnow()}
            }
        )
        
        return post

    async def get_posts(
        self,
        forum_id: Optional[str] = None,
        group_id: Optional[str] = None,
        post_type: Optional[PostType] = None,
        author_id: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[PostResponse]:
        """Get posts with filtering options"""
        
        query = {"status": PostStatus.PUBLISHED}
        
        if forum_id:
            query["forum_id"] = forum_id
        if group_id:
            query["group_id"] = group_id
        if post_type:
            query["post_type"] = post_type
        if author_id:
            query["author_id"] = author_id
        if tag:
            query["tags"] = {"$in": [tag]}
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"content": {"$regex": search, "$options": "i"}},
                {"tags": {"$regex": search, "$options": "i"}}
            ]
        
        # Sort by pinned posts first, then by creation date
        cursor = self.posts_collection.find(query).sort([
            ("is_pinned", -1),
            ("created_at", -1)
        ]).skip(skip).limit(limit)
        
        posts = []
        async for post_doc in cursor:
            post_dict = dict(post_doc)
            post_dict.pop('_id', None)
            
            # Get author information
            author = await self.users_collection.find_one({"id": post_dict["author_id"]})
            post_dict["author_name"] = f"{author['first_name']} {author['last_name']}" if author else "Unknown"
            post_dict["author_avatar"] = author.get('profile_image') if author else None
            
            # Get forum name
            forum = await self.forums_collection.find_one({"id": post_dict["forum_id"]})
            post_dict["forum_name"] = forum['name'] if forum else "Unknown"
            
            # Get group name if applicable
            if post_dict.get("group_id"):
                group = await self.groups_collection.find_one({"id": post_dict["group_id"]})
                post_dict["group_name"] = group['name'] if group else "Unknown"
            else:
                post_dict["group_name"] = None
            
            # Calculate engagement metrics
            post_dict["likes_count"] = len(post_dict.get("likes", []))
            
            posts.append(PostResponse(**post_dict))
        
        return posts

    async def get_post_by_id(self, post_id: str) -> Optional[PostResponse]:
        """Get post by ID"""
        post_doc = await self.posts_collection.find_one({"id": post_id})
        if not post_doc:
            return None
        
        post_dict = dict(post_doc)
        post_dict.pop('_id', None)
        
        # Increment view count
        await self.posts_collection.update_one(
            {"id": post_id},
            {"$inc": {"views": 1}}
        )
        post_dict["views"] += 1
        
        # Get author information
        author = await self.users_collection.find_one({"id": post_dict["author_id"]})
        post_dict["author_name"] = f"{author['first_name']} {author['last_name']}" if author else "Unknown"
        post_dict["author_avatar"] = author.get('profile_image') if author else None
        
        # Get forum name
        forum = await self.forums_collection.find_one({"id": post_dict["forum_id"]})
        post_dict["forum_name"] = forum['name'] if forum else "Unknown"
        
        # Get group name if applicable
        if post_dict.get("group_id"):
            group = await self.groups_collection.find_one({"id": post_dict["group_id"]})
            post_dict["group_name"] = group['name'] if group else "Unknown"
        else:
            post_dict["group_name"] = None
        
        # Calculate engagement metrics
        post_dict["likes_count"] = len(post_dict.get("likes", []))
        
        return PostResponse(**post_dict)

    async def update_post(self, post_id: str, post_data: PostUpdate, user_id: str) -> Optional[Post]:
        """Update a post (only by author or moderator)"""
        post_doc = await self.posts_collection.find_one({"id": post_id})
        if not post_doc:
            return None
        
        # Check permissions
        if post_doc["author_id"] != user_id:
            # Check if user is a moderator of the forum
            forum = await self.forums_collection.find_one({"id": post_doc["forum_id"]})
            if not forum or user_id not in forum.get("moderators", []):
                return None
        
        update_data = {k: v for k, v in post_data.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        await self.posts_collection.update_one(
            {"id": post_id},
            {"$set": update_data}
        )
        
        updated_doc = await self.posts_collection.find_one({"id": post_id})
        updated_dict = dict(updated_doc)
        updated_dict.pop('_id', None)
        
        return Post(**updated_dict)

    async def toggle_post_like(self, post_id: str, user_id: str) -> bool:
        """Toggle like on a post"""
        post_doc = await self.posts_collection.find_one({"id": post_id})
        if not post_doc:
            return False
        
        likes = post_doc.get("likes", [])
        
        if user_id in likes:
            # Unlike
            await self.posts_collection.update_one(
                {"id": post_id},
                {"$pull": {"likes": user_id}}
            )
            return False
        else:
            # Like
            await self.posts_collection.update_one(
                {"id": post_id},
                {"$addToSet": {"likes": user_id}}
            )
            return True

    # Comment Management
    async def create_comment(self, comment_data: CommentCreate, author_id: str) -> Comment:
        """Create a new comment"""
        comment = Comment(
            **comment_data.dict(),
            author_id=author_id
        )
        
        await self.comments_collection.insert_one(comment.dict())
        
        # Update post comment count
        await self.posts_collection.update_one(
            {"id": comment.post_id},
            {
                "$inc": {"comments_count": 1},
                "$set": {
                    "last_reply_at": datetime.utcnow(),
                    "last_reply_by": author_id
                }
            }
        )
        
        return comment

    async def get_comments_by_post(self, post_id: str, skip: int = 0, limit: int = 50) -> List[Comment]:
        """Get comments for a post"""
        cursor = self.comments_collection.find({"post_id": post_id}).sort("created_at", 1).skip(skip).limit(limit)
        
        comments = []
        async for comment_doc in cursor:
            comment_dict = dict(comment_doc)
            comment_dict.pop('_id', None)
            comments.append(Comment(**comment_dict))
        
        return comments

    async def toggle_comment_like(self, comment_id: str, user_id: str) -> bool:
        """Toggle like on a comment"""
        comment_doc = await self.comments_collection.find_one({"id": comment_id})
        if not comment_doc:
            return False
        
        likes = comment_doc.get("likes", [])
        
        if user_id in likes:
            # Unlike
            await self.comments_collection.update_one(
                {"id": comment_id},
                {"$pull": {"likes": user_id}}
            )
            return False
        else:
            # Like
            await self.comments_collection.update_one(
                {"id": comment_id},
                {"$addToSet": {"likes": user_id}}
            )
            return True

    # Group Management
    async def create_group(self, group_data: GroupCreate, creator_id: str) -> Group:
        """Create a new group"""
        group = Group(
            **group_data.dict(),
            created_by=creator_id,
            moderators=[creator_id],
            members=[creator_id]
        )
        
        await self.groups_collection.insert_one(group.dict())
        
        # Create membership record
        membership = GroupMembership(
            user_id=creator_id,
            group_id=group.id,
            role="admin"
        )
        await self.group_memberships_collection.insert_one(membership.dict())
        
        return group

    async def get_groups(
        self,
        group_type: Optional[GroupType] = None,
        skill_focus: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Group]:
        """Get groups with filtering"""
        
        query = {"is_active": True}
        
        if group_type:
            query["group_type"] = group_type
        if skill_focus:
            query["skills_focus"] = {"$in": [skill_focus]}
        if category:
            query["category"] = category
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        cursor = self.groups_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        
        groups = []
        async for group_doc in cursor:
            group_dict = dict(group_doc)
            group_dict.pop('_id', None)
            groups.append(Group(**group_dict))
        
        return groups

    async def join_group(self, group_id: str, user_id: str) -> bool:
        """Join a group"""
        group_doc = await self.groups_collection.find_one({"id": group_id, "is_active": True})
        if not group_doc:
            return False
        
        # Check if already a member
        existing_membership = await self.group_memberships_collection.find_one({
            "group_id": group_id,
            "user_id": user_id,
            "is_active": True
        })
        if existing_membership:
            return True
        
        # For private groups, add to pending requests
        if group_doc["privacy"] == GroupPrivacy.PRIVATE:
            await self.groups_collection.update_one(
                {"id": group_id},
                {"$addToSet": {"pending_requests": user_id}}
            )
            return False
        
        # Add to group members
        await self.groups_collection.update_one(
            {"id": group_id},
            {"$addToSet": {"members": user_id}}
        )
        
        # Create membership record
        membership = GroupMembership(
            user_id=user_id,
            group_id=group_id
        )
        await self.group_memberships_collection.insert_one(membership.dict())
        
        return True

    # Testimonial Management
    async def create_testimonial(self, testimonial_data: TestimonialCreate, author_id: str) -> Testimonial:
        """Create a new testimonial"""
        testimonial = Testimonial(
            **testimonial_data.dict(),
            author_id=author_id
        )
        
        await self.testimonials_collection.insert_one(testimonial.dict())
        return testimonial

    async def get_testimonials(
        self,
        subject_id: Optional[str] = None,
        author_id: Optional[str] = None,
        featured_only: bool = False,
        skip: int = 0,
        limit: int = 20
    ) -> List[Testimonial]:
        """Get testimonials"""
        
        query = {"is_public": True, "is_approved": True}
        
        if subject_id:
            query["subject_id"] = subject_id
        if author_id:
            query["author_id"] = author_id
        if featured_only:
            query["is_featured"] = True
        
        cursor = self.testimonials_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        
        testimonials = []
        async for testimonial_doc in cursor:
            testimonial_dict = dict(testimonial_doc)
            testimonial_dict.pop('_id', None)
            testimonials.append(Testimonial(**testimonial_dict))
        
        return testimonials

    # Knowledge Base Management
    async def create_knowledge_base_entry(self, kb_data: KnowledgeBaseCreate, author_id: str) -> KnowledgeBase:
        """Create a new knowledge base entry"""
        kb_entry = KnowledgeBase(
            **kb_data.dict(),
            author_id=author_id
        )
        
        await self.knowledge_base_collection.insert_one(kb_entry.dict())
        return kb_entry

    async def get_knowledge_base_entries(
        self,
        category: Optional[str] = None,
        skill_id: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[KnowledgeBase]:
        """Get knowledge base entries"""
        
        query = {"is_active": True}
        
        if category:
            query["category"] = category
        if skill_id:
            query["skill_ids"] = {"$in": [skill_id]}
        if difficulty_level:
            query["difficulty_level"] = difficulty_level
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"content": {"$regex": search, "$options": "i"}},
                {"tags": {"$regex": search, "$options": "i"}}
            ]
        
        cursor = self.knowledge_base_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        
        entries = []
        async for entry_doc in cursor:
            entry_dict = dict(entry_doc)
            entry_dict.pop('_id', None)
            entries.append(KnowledgeBase(**entry_dict))
        
        return entries

    # Statistics and Analytics
    async def get_community_stats(self) -> Dict[str, Any]:
        """Get overall community statistics"""
        stats = {
            "total_forums": await self.forums_collection.count_documents({"is_active": True}),
            "total_posts": await self.posts_collection.count_documents({"status": PostStatus.PUBLISHED}),
            "total_comments": await self.comments_collection.count_documents({}),
            "total_groups": await self.groups_collection.count_documents({"is_active": True}),
            "total_testimonials": await self.testimonials_collection.count_documents({"is_public": True}),
            "total_kb_entries": await self.knowledge_base_collection.count_documents({"is_active": True})
        }
        
        # Get recent activity
        recent_posts = await self.posts_collection.find(
            {"status": PostStatus.PUBLISHED}
        ).sort("created_at", -1).limit(5).to_list(length=5)
        
        stats["recent_posts"] = len(recent_posts)
        
        return stats

    async def get_trending_topics(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get trending topics based on recent activity"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Aggregate posts by tags to find trending topics
        pipeline = [
            {"$match": {"created_at": {"$gte": since_date}, "status": PostStatus.PUBLISHED}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        trending = []
        async for item in self.posts_collection.aggregate(pipeline):
            trending.append({
                "topic": item["_id"],
                "post_count": item["count"]
            })
        
        return trending
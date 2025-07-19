import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  ChatBubbleLeftIcon,
  UserGroupIcon,
  StarIcon,
  HeartIcon,
  EyeIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  FireIcon,
  AcademicCapIcon,
  BookOpenIcon,
  TrophyIcon,
  ChevronRightIcon,
  ClockIcon,
  TagIcon
} from '@heroicons/react/24/outline';
import {
  HeartIcon as HeartSolidIcon,
  FireIcon as FireSolidIcon
} from '@heroicons/react/24/solid';

const Community = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('forums');
  const [forums, setForums] = useState([]);
  const [posts, setPosts] = useState([]);
  const [groups, setGroups] = useState([]);
  const [testimonials, setTestimonials] = useState([]);
  const [knowledgeBase, setKnowledgeBase] = useState([]);
  const [communityStats, setCommunityStats] = useState({});
  const [trendingTopics, setTrendingTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedForum, setSelectedForum] = useState(null);
  const [postType, setPostType] = useState('all');

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    loadCommunityData();
  }, []);

  const loadCommunityData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Load forums
      const forumsResponse = await fetch(`${backendUrl}/community/forums`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (forumsResponse.ok) {
        const forumsData = await forumsResponse.json();
        setForums(forumsData);
      }

      // Load recent posts
      const postsResponse = await fetch(`${backendUrl}/community/posts?limit=10`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (postsResponse.ok) {
        const postsData = await postsResponse.json();
        setPosts(postsData);
      }

      // Load groups
      const groupsResponse = await fetch(`${backendUrl}/community/groups?limit=6`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (groupsResponse.ok) {
        const groupsData = await groupsResponse.json();
        setGroups(groupsData);
      }

      // Load featured testimonials
      const testimonialsResponse = await fetch(`${backendUrl}/community/testimonials?featured_only=true&limit=3`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (testimonialsResponse.ok) {
        const testimonialsData = await testimonialsResponse.json();
        setTestimonials(testimonialsData);
      }

      // Load knowledge base
      const kbResponse = await fetch(`${backendUrl}/community/knowledge-base?limit=6`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (kbResponse.ok) {
        const kbData = await kbResponse.json();
        setKnowledgeBase(kbData);
      }

      // Load community stats
      const statsResponse = await fetch(`${backendUrl}/community/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setCommunityStats(statsData);
      }

      // Load trending topics
      const trendingResponse = await fetch(`${backendUrl}/community/trending`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (trendingResponse.ok) {
        const trendingData = await trendingResponse.json();
        setTrendingTopics(trendingData.trending_topics || []);
      }
    } catch (error) {
      console.error('Error loading community data:', error);
    } finally {
      setLoading(false);
    }
  };

  const togglePostLike = async (postId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${backendUrl}/community/posts/${postId}/like`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        // Refresh posts to update like counts
        loadCommunityData();
      }
    } catch (error) {
      console.error('Error toggling like:', error);
    }
  };

  const getPostTypeIcon = (type) => {
    switch (type) {
      case 'showcase': return <StarIcon className="h-4 w-4" />;
      case 'question': return <ChatBubbleLeftIcon className="h-4 w-4" />;
      case 'tutorial': return <AcademicCapIcon className="h-4 w-4" />;
      case 'testimonial': return <TrophyIcon className="h-4 w-4" />;
      default: return <ChatBubbleLeftIcon className="h-4 w-4" />;
    }
  };

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
    return `${Math.floor(diffInHours / 168)}w ago`;
  };

  const tabs = [
    { id: 'forums', name: 'Forums', icon: ChatBubbleLeftIcon },
    { id: 'groups', name: 'Groups', icon: UserGroupIcon },
    { id: 'showcases', name: 'Showcases', icon: StarIcon },
    { id: 'testimonials', name: 'Testimonials', icon: TrophyIcon },
    { id: 'knowledge', name: 'Knowledge Base', icon: BookOpenIcon }
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading community...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <h1 className="text-4xl font-bold mb-4">SkillSwap Community</h1>
            <p className="text-xl text-blue-100 mb-8">
              Connect, Learn, and Share Knowledge with Fellow Skill Enthusiasts
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto">
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 text-center">
                <div className="text-2xl font-bold">{communityStats.total_forums || 0}</div>
                <div className="text-sm text-blue-100">Forums</div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 text-center">
                <div className="text-2xl font-bold">{communityStats.total_posts || 0}</div>
                <div className="text-sm text-blue-100">Posts</div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 text-center">
                <div className="text-2xl font-bold">{communityStats.total_groups || 0}</div>
                <div className="text-sm text-blue-100">Groups</div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 text-center">
                <div className="text-2xl font-bold">{communityStats.total_testimonials || 0}</div>
                <div className="text-sm text-blue-100">Testimonials</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content Area */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-3">
            {activeTab === 'forums' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-gray-900">Discussion Forums</h2>
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2">
                    <PlusIcon className="h-4 w-4" />
                    <span>New Post</span>
                  </button>
                </div>

                {/* Forums Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {forums.map((forum) => (
                    <div key={forum.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="text-2xl">{forum.icon}</div>
                          <div>
                            <h3 className="font-semibold text-gray-900">{forum.name}</h3>
                            <p className="text-sm text-gray-600 mt-1">{forum.description}</p>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span>{forum.posts_count} posts</span>
                          <span>{forum.members_count} members</span>
                        </div>
                        <button className="text-blue-600 hover:text-blue-700 font-medium text-sm">
                          View Forum
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Recent Posts */}
                <div className="mt-8">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-semibold text-gray-900">Recent Discussions</h3>
                    <div className="flex items-center space-x-4">
                      <select
                        value={postType}
                        onChange={(e) => setPostType(e.target.value)}
                        className="rounded-lg border-gray-300 text-sm"
                      >
                        <option value="all">All Posts</option>
                        <option value="discussion">Discussions</option>
                        <option value="question">Questions</option>
                        <option value="showcase">Showcases</option>
                        <option value="tutorial">Tutorials</option>
                      </select>
                    </div>
                  </div>

                  <div className="space-y-4">
                    {posts.map((post) => (
                      <div key={post.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                        <div className="flex items-start space-x-4">
                          <img
                            src={post.author_avatar || `https://ui-avatars.com/api/?name=${post.author_name}&background=random`}
                            alt={post.author_name}
                            className="h-10 w-10 rounded-full"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-2">
                              {getPostTypeIcon(post.post_type)}
                              <span className="text-sm font-medium text-blue-600 capitalize">
                                {post.post_type}
                              </span>
                              <span className="text-gray-500">•</span>
                              <span className="text-sm text-gray-500">{post.forum_name}</span>
                            </div>
                            <h4 className="text-lg font-semibold text-gray-900 mb-2">{post.title}</h4>
                            <p className="text-gray-600 line-clamp-2 mb-3">{post.content}</p>
                            
                            {post.tags && post.tags.length > 0 && (
                              <div className="flex flex-wrap gap-2 mb-3">
                                {post.tags.map((tag) => (
                                  <span key={tag} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                    #{tag}
                                  </span>
                                ))}
                              </div>
                            )}

                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-6 text-sm text-gray-500">
                                <span className="flex items-center space-x-1">
                                  <EyeIcon className="h-4 w-4" />
                                  <span>{post.views}</span>
                                </span>
                                <span className="flex items-center space-x-1">
                                  <ChatBubbleLeftIcon className="h-4 w-4" />
                                  <span>{post.comments_count}</span>
                                </span>
                                <button
                                  onClick={() => togglePostLike(post.id)}
                                  className="flex items-center space-x-1 hover:text-red-600"
                                >
                                  <HeartIcon className="h-4 w-4" />
                                  <span>{post.likes_count}</span>
                                </button>
                              </div>
                              <div className="flex items-center space-x-3 text-sm text-gray-500">
                                <span>by {post.author_name}</span>
                                <span>•</span>
                                <span>{formatTimeAgo(post.created_at)}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'groups' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-gray-900">Study Groups</h2>
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2">
                    <PlusIcon className="h-4 w-4" />
                    <span>Create Group</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {groups.map((group) => (
                    <div key={group.id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
                      {group.image && (
                        <img src={group.image} alt={group.name} className="w-full h-32 object-cover" />
                      )}
                      <div className="p-6">
                        <div className="flex items-center justify-between mb-2">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 capitalize">
                            {group.group_type.replace('_', ' ')}
                          </span>
                          <span className="text-sm text-gray-500">{group.members.length} members</span>
                        </div>
                        <h3 className="font-semibold text-gray-900 mb-2">{group.name}</h3>
                        <p className="text-sm text-gray-600 mb-4 line-clamp-3">{group.description}</p>
                        
                        {group.skills_focus && group.skills_focus.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-4">
                            {group.skills_focus.slice(0, 3).map((skill) => (
                              <span key={skill} className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700">
                                {skill}
                              </span>
                            ))}
                            {group.skills_focus.length > 3 && (
                              <span className="text-xs text-gray-500">+{group.skills_focus.length - 3} more</span>
                            )}
                          </div>
                        )}

                        <button className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
                          Join Group
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'showcases' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-gray-900">Skill Showcases</h2>
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2">
                    <PlusIcon className="h-4 w-4" />
                    <span>Share Project</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {posts.filter(post => post.post_type === 'showcase').map((showcase) => (
                    <div key={showcase.id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
                      {showcase.images && showcase.images.length > 0 && (
                        <img src={showcase.images[0]} alt={showcase.title} className="w-full h-48 object-cover" />
                      )}
                      <div className="p-6">
                        <div className="flex items-center space-x-2 mb-3">
                          <StarIcon className="h-5 w-5 text-yellow-500" />
                          <span className="text-sm font-medium text-yellow-600">Showcase</span>
                        </div>
                        <h3 className="font-semibold text-gray-900 mb-2">{showcase.title}</h3>
                        <p className="text-gray-600 mb-4 line-clamp-3">{showcase.content}</p>
                        
                        {showcase.skills_demonstrated && showcase.skills_demonstrated.length > 0 && (
                          <div className="flex flex-wrap gap-2 mb-4">
                            {showcase.skills_demonstrated.map((skill) => (
                              <span key={skill} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                {skill}
                              </span>
                            ))}
                          </div>
                        )}

                        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                          <div className="flex items-center space-x-4 text-sm text-gray-500">
                            <span className="flex items-center space-x-1">
                              <EyeIcon className="h-4 w-4" />
                              <span>{showcase.views}</span>
                            </span>
                            <span className="flex items-center space-x-1">
                              <HeartIcon className="h-4 w-4" />
                              <span>{showcase.likes_count}</span>
                            </span>
                          </div>
                          <span className="text-sm text-gray-500">by {showcase.author_name}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'testimonials' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-gray-900">Success Stories</h2>
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2">
                    <PlusIcon className="h-4 w-4" />
                    <span>Share Story</span>
                  </button>
                </div>

                <div className="space-y-6">
                  {testimonials.map((testimonial) => (
                    <div key={testimonial.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                      <div className="flex items-start space-x-4">
                        <img
                          src={`https://ui-avatars.com/api/?name=User&background=random`}
                          alt="Author"
                          className="h-12 w-12 rounded-full"
                        />
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <div className="flex items-center">
                              {[...Array(5)].map((_, i) => (
                                <StarIcon
                                  key={i}
                                  className={`h-4 w-4 ${i < testimonial.rating ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
                                />
                              ))}
                            </div>
                            <span className="text-sm text-gray-500">•</span>
                            <span className="text-sm text-gray-500">{formatTimeAgo(testimonial.created_at)}</span>
                          </div>
                          <p className="text-gray-700 mb-4">{testimonial.content}</p>
                          
                          {testimonial.skills_mentioned && testimonial.skills_mentioned.length > 0 && (
                            <div className="flex flex-wrap gap-2 mb-4">
                              {testimonial.skills_mentioned.map((skill) => (
                                <span key={skill} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  {skill}
                                </span>
                              ))}
                            </div>
                          )}

                          {testimonial.highlights && testimonial.highlights.length > 0 && (
                            <div className="space-y-1">
                              <p className="text-sm font-medium text-gray-700">Key Achievements:</p>
                              <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                                {testimonial.highlights.map((highlight, index) => (
                                  <li key={index}>{highlight}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'knowledge' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-gray-900">Knowledge Base</h2>
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2">
                    <PlusIcon className="h-4 w-4" />
                    <span>Contribute</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {knowledgeBase.map((entry) => (
                    <div key={entry.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between mb-3">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          entry.difficulty_level === 'beginner' ? 'bg-green-100 text-green-800' :
                          entry.difficulty_level === 'intermediate' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {entry.difficulty_level}
                        </span>
                        {entry.is_verified && (
                          <div className="flex items-center space-x-1 text-blue-600">
                            <TrophyIcon className="h-4 w-4" />
                            <span className="text-xs">Verified</span>
                          </div>
                        )}
                      </div>
                      
                      <h3 className="font-semibold text-gray-900 mb-2">{entry.title}</h3>
                      <p className="text-sm text-gray-600 mb-4 line-clamp-3">{entry.content}</p>
                      
                      {entry.tags && entry.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-4">
                          {entry.tags.slice(0, 3).map((tag) => (
                            <span key={tag} className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700">
                              #{tag}
                            </span>
                          ))}
                        </div>
                      )}

                      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                        <div className="flex items-center space-x-3 text-sm text-gray-500">
                          <span className="flex items-center space-x-1">
                            <EyeIcon className="h-4 w-4" />
                            <span>{entry.views}</span>
                          </span>
                          <span className="flex items-center space-x-1">
                            <HeartIcon className="h-4 w-4" />
                            <span>{entry.likes?.length || 0}</span>
                          </span>
                        </div>
                        <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                          Read More
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Trending Topics */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center space-x-2">
                <FireSolidIcon className="h-5 w-5 text-orange-500" />
                <span>Trending Topics</span>
              </h3>
              <div className="space-y-3">
                {trendingTopics.slice(0, 5).map((topic, index) => (
                  <div key={topic.topic} className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">#{topic.topic}</span>
                    <span className="text-xs text-gray-500">{topic.post_count} posts</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <button className="w-full text-left px-3 py-2 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors">
                  Ask a Question
                </button>
                <button className="w-full text-left px-3 py-2 rounded-lg bg-green-50 text-green-700 hover:bg-green-100 transition-colors">
                  Share a Project
                </button>
                <button className="w-full text-left px-3 py-2 rounded-lg bg-purple-50 text-purple-700 hover:bg-purple-100 transition-colors">
                  Write Tutorial
                </button>
                <button className="w-full text-left px-3 py-2 rounded-lg bg-orange-50 text-orange-700 hover:bg-orange-100 transition-colors">
                  Create Group
                </button>
              </div>
            </div>

            {/* Community Guidelines */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Community Guidelines</h3>
              <div className="space-y-2 text-sm text-gray-600">
                <p>• Be respectful and supportive</p>
                <p>• Share knowledge generously</p>
                <p>• Ask questions and learn</p>
                <p>• Credit others' work</p>
                <p>• Keep discussions on-topic</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Community;
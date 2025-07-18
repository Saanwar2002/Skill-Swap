import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  UserIcon,
  PencilIcon,
  CheckIcon,
  XMarkIcon,
  PlusIcon,
  TrashIcon,
  CameraIcon,
  MapPinIcon,
  ClockIcon,
  StarIcon,
  AcademicCapIcon,
  BookOpenIcon,
  GlobeAltIcon,
  UserCircleIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

const Profile = () => {
  const { user, updateUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    bio: '',
    location: '',
    timezone: '',
    role: 'both',
    teaching_style: '',
    learning_style: '',
    languages: [],
    profile_image: null
  });
  const [skills, setSkills] = useState([]);
  const [availableSkills, setAvailableSkills] = useState([]);
  const [editingProfile, setEditingProfile] = useState(false);
  const [editingSkill, setEditingSkill] = useState(null);
  const [newSkill, setNewSkill] = useState({
    skill_id: '',
    skill_name: '',
    level: 'beginner',
    years_experience: 0,
    certifications: [],
    portfolio_items: []
  });
  const [showAddSkill, setShowAddSkill] = useState(false);
  const [profileImageFile, setProfileImageFile] = useState(null);

  const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  const skillLevels = [
    { value: 'beginner', label: 'Beginner', color: 'bg-green-100 text-green-800' },
    { value: 'intermediate', label: 'Intermediate', color: 'bg-yellow-100 text-yellow-800' },
    { value: 'advanced', label: 'Advanced', color: 'bg-orange-100 text-orange-800' },
    { value: 'expert', label: 'Expert', color: 'bg-red-100 text-red-800' }
  ];

  const userRoles = [
    { value: 'learner', label: 'Learner', description: 'I want to learn new skills' },
    { value: 'teacher', label: 'Teacher', description: 'I want to teach others' },
    { value: 'both', label: 'Both', description: 'I want to learn and teach' }
  ];

  const commonLanguages = [
    'English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese', 'Russian',
    'Chinese', 'Japanese', 'Korean', 'Arabic', 'Hindi', 'Dutch', 'Swedish'
  ];

  useEffect(() => {
    if (user) {
      setProfileData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        bio: user.bio || '',
        location: user.location || '',
        timezone: user.timezone || '',
        role: user.role || 'both',
        teaching_style: user.teaching_style || '',
        learning_style: user.learning_style || '',
        languages: user.languages || [],
        profile_image: user.profile_image || null
      });
    }
    fetchUserSkills();
    fetchAvailableSkills();
  }, [user]);

  const fetchUserSkills = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/users/skills`);
      setSkills(response.data);
    } catch (error) {
      console.error('Error fetching user skills:', error);
    }
  };

  const fetchAvailableSkills = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/skills/`);
      setAvailableSkills(response.data);
    } catch (error) {
      console.error('Error fetching available skills:', error);
    }
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      let imageBase64 = profileData.profile_image;
      
      // Convert image file to base64 if new image was selected
      if (profileImageFile) {
        const reader = new FileReader();
        imageBase64 = await new Promise((resolve, reject) => {
          reader.onload = () => resolve(reader.result);
          reader.onerror = reject;
          reader.readAsDataURL(profileImageFile);
        });
      }

      const updateData = {
        ...profileData,
        profile_image: imageBase64
      };

      const result = await updateUser(updateData);
      if (result.success) {
        setEditingProfile(false);
        setProfileImageFile(null);
      }
    } catch (error) {
      toast.error('Failed to update profile');
      console.error('Profile update error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        toast.error('Image size must be less than 5MB');
        return;
      }
      setProfileImageFile(file);
      
      // Preview the image
      const reader = new FileReader();
      reader.onload = (event) => {
        setProfileData(prev => ({
          ...prev,
          profile_image: event.target.result
        }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAddSkill = async () => {
    if (!newSkill.skill_id || !newSkill.skill_name) {
      toast.error('Please select a skill');
      return;
    }

    try {
      const response = await axios.post(`${API_BASE}/api/users/skills`, {
        skill_id: newSkill.skill_id,
        skill_name: newSkill.skill_name,
        level: newSkill.level,
        years_experience: parseInt(newSkill.years_experience) || 0,
        certifications: newSkill.certifications,
        portfolio_items: newSkill.portfolio_items
      });

      setSkills([...skills, response.data]);
      setNewSkill({
        skill_id: '',
        skill_name: '',
        level: 'beginner',
        years_experience: 0,
        certifications: [],
        portfolio_items: []
      });
      setShowAddSkill(false);
      toast.success('Skill added successfully');
    } catch (error) {
      toast.error('Failed to add skill');
      console.error('Add skill error:', error);
    }
  };

  const handleRemoveSkill = async (skillId) => {
    try {
      await axios.delete(`${API_BASE}/api/users/skills/${skillId}`);
      setSkills(skills.filter(skill => skill.id !== skillId));
      toast.success('Skill removed successfully');
    } catch (error) {
      toast.error('Failed to remove skill');
      console.error('Remove skill error:', error);
    }
  };

  const handleUpdateSkill = async (skillId, updateData) => {
    try {
      const response = await axios.put(`${API_BASE}/api/users/skills/${skillId}`, updateData);
      setSkills(skills.map(skill => 
        skill.id === skillId ? response.data : skill
      ));
      setEditingSkill(null);
      toast.success('Skill updated successfully');
    } catch (error) {
      toast.error('Failed to update skill');
      console.error('Update skill error:', error);
    }
  };

  const handleLanguageToggle = (language) => {
    setProfileData(prev => ({
      ...prev,
      languages: prev.languages.includes(language)
        ? prev.languages.filter(lang => lang !== language)
        : [...prev.languages, language]
    }));
  };

  const renderStars = (rating) => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <StarIconSolid
          key={i}
          className={`h-4 w-4 ${i <= rating ? 'text-yellow-400' : 'text-gray-300'}`}
        />
      );
    }
    return stars;
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Profile Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 text-white">
          <div className="flex items-center space-x-6">
            <div className="relative">
              {profileData.profile_image ? (
                <img 
                  src={profileData.profile_image} 
                  alt="Profile"
                  className="w-20 h-20 rounded-full object-cover border-4 border-white"
                />
              ) : (
                <div className="w-20 h-20 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
                  <UserCircleIcon className="h-12 w-12 text-white" />
                </div>
              )}
              {editingProfile && (
                <label className="absolute bottom-0 right-0 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-full p-2 cursor-pointer">
                  <CameraIcon className="h-4 w-4 text-white" />
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="hidden"
                  />
                </label>
              )}
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold">
                {user?.first_name} {user?.last_name}
              </h1>
              <p className="text-blue-100 mt-1">
                @{user?.username} • Level {user?.level}
              </p>
              <div className="flex items-center space-x-4 mt-2">
                <div className="flex items-center">
                  {renderStars(Math.floor(user?.average_rating || 0))}
                  <span className="ml-2 text-sm">({user?.rating_count || 0} reviews)</span>
                </div>
                <span className="text-sm">
                  {user?.skill_coins} coins
                </span>
              </div>
            </div>
            <button
              onClick={() => setEditingProfile(!editingProfile)}
              className="bg-white bg-opacity-20 hover:bg-opacity-30 px-4 py-2 rounded-lg transition-colors"
            >
              {editingProfile ? (
                <XMarkIcon className="h-5 w-5" />
              ) : (
                <PencilIcon className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>

        {/* Profile Form */}
        <div className="p-6">
          <form onSubmit={handleProfileUpdate}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Basic Information */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  First Name
                </label>
                <input
                  type="text"
                  value={profileData.first_name}
                  onChange={(e) => setProfileData(prev => ({ ...prev, first_name: e.target.value }))}
                  disabled={!editingProfile}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Last Name
                </label>
                <input
                  type="text"
                  value={profileData.last_name}
                  onChange={(e) => setProfileData(prev => ({ ...prev, last_name: e.target.value }))}
                  disabled={!editingProfile}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <MapPinIcon className="h-4 w-4 inline mr-1" />
                  Location
                </label>
                <input
                  type="text"
                  value={profileData.location}
                  onChange={(e) => setProfileData(prev => ({ ...prev, location: e.target.value }))}
                  disabled={!editingProfile}
                  placeholder="City, Country"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <ClockIcon className="h-4 w-4 inline mr-1" />
                  Timezone
                </label>
                <select
                  value={profileData.timezone}
                  onChange={(e) => setProfileData(prev => ({ ...prev, timezone: e.target.value }))}
                  disabled={!editingProfile}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
                >
                  <option value="">Select timezone</option>
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">Eastern Time</option>
                  <option value="America/Chicago">Central Time</option>
                  <option value="America/Denver">Mountain Time</option>
                  <option value="America/Los_Angeles">Pacific Time</option>
                  <option value="Europe/London">London</option>
                  <option value="Europe/Paris">Paris</option>
                  <option value="Asia/Tokyo">Tokyo</option>
                  <option value="Asia/Shanghai">Shanghai</option>
                  <option value="Asia/Mumbai">Mumbai</option>
                </select>
              </div>
            </div>

            {/* Bio */}
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                About Me
              </label>
              <textarea
                value={profileData.bio}
                onChange={(e) => setProfileData(prev => ({ ...prev, bio: e.target.value }))}
                disabled={!editingProfile}
                rows={4}
                placeholder="Tell others about yourself, your interests, and what you're passionate about..."
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
              />
            </div>

            {/* Role Selection */}
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-4">
                I'm here to...
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {userRoles.map((role) => (
                  <div
                    key={role.value}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      profileData.role === role.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-300 hover:border-gray-400'
                    } ${!editingProfile ? 'pointer-events-none' : ''}`}
                    onClick={() => editingProfile && setProfileData(prev => ({ ...prev, role: role.value }))}
                  >
                    <h3 className="font-medium text-gray-900">{role.label}</h3>
                    <p className="text-sm text-gray-600 mt-1">{role.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Learning & Teaching Style */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <BookOpenIcon className="h-4 w-4 inline mr-1" />
                  Learning Style
                </label>
                <select
                  value={profileData.learning_style}
                  onChange={(e) => setProfileData(prev => ({ ...prev, learning_style: e.target.value }))}
                  disabled={!editingProfile}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
                >
                  <option value="">Select learning style</option>
                  <option value="visual">Visual</option>
                  <option value="auditory">Auditory</option>
                  <option value="kinesthetic">Kinesthetic</option>
                  <option value="reading">Reading/Writing</option>
                  <option value="mixed">Mixed</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <AcademicCapIcon className="h-4 w-4 inline mr-1" />
                  Teaching Style
                </label>
                <select
                  value={profileData.teaching_style}
                  onChange={(e) => setProfileData(prev => ({ ...prev, teaching_style: e.target.value }))}
                  disabled={!editingProfile}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
                >
                  <option value="">Select teaching style</option>
                  <option value="structured">Structured</option>
                  <option value="flexible">Flexible</option>
                  <option value="interactive">Interactive</option>
                  <option value="practical">Practical</option>
                  <option value="collaborative">Collaborative</option>
                </select>
              </div>
            </div>

            {/* Languages */}
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-4">
                <GlobeAltIcon className="h-4 w-4 inline mr-1" />
                Languages I speak
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {commonLanguages.map((language) => (
                  <label
                    key={language}
                    className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                      profileData.languages.includes(language)
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-300 hover:border-gray-400'
                    } ${!editingProfile ? 'pointer-events-none' : ''}`}
                  >
                    <input
                      type="checkbox"
                      checked={profileData.languages.includes(language)}
                      onChange={() => handleLanguageToggle(language)}
                      disabled={!editingProfile}
                      className="sr-only"
                    />
                    <span className="text-sm">{language}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Save Button */}
            {editingProfile && (
              <div className="mt-6 flex space-x-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center space-x-2"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <CheckIcon className="h-4 w-4" />
                  )}
                  <span>Save Changes</span>
                </button>
                <button
                  type="button"
                  onClick={() => setEditingProfile(false)}
                  className="bg-gray-200 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            )}
          </form>
        </div>
      </div>

      {/* Skills Management */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">My Skills</h2>
            <button
              onClick={() => setShowAddSkill(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
            >
              <PlusIcon className="h-4 w-4" />
              <span>Add Skill</span>
            </button>
          </div>
        </div>

        <div className="p-6">
          {skills.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {skills.map((skill) => (
                <div key={skill.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium text-gray-900">{skill.skill_name}</h3>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setEditingSkill(skill.id)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleRemoveSkill(skill.id)}
                        className="text-red-400 hover:text-red-600"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      skillLevels.find(level => level.value === skill.level)?.color || 'bg-gray-100 text-gray-800'
                    }`}>
                      {skillLevels.find(level => level.value === skill.level)?.label || skill.level}
                    </span>
                    {skill.years_experience > 0 && (
                      <span className="text-xs text-gray-500">
                        {skill.years_experience} years experience
                      </span>
                    )}
                  </div>
                  {skill.certifications && skill.certifications.length > 0 && (
                    <div className="text-xs text-gray-500">
                      Certifications: {skill.certifications.join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <StarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">No skills added yet</p>
              <button
                onClick={() => setShowAddSkill(true)}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Add Your First Skill
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Add Skill Modal */}
      {showAddSkill && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New Skill</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Skill
                </label>
                <select
                  value={newSkill.skill_id}
                  onChange={(e) => {
                    const selectedSkill = availableSkills.find(skill => skill.id === e.target.value);
                    setNewSkill(prev => ({
                      ...prev,
                      skill_id: e.target.value,
                      skill_name: selectedSkill ? selectedSkill.name : ''
                    }));
                  }}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select a skill</option>
                  {availableSkills.map((skill) => (
                    <option key={skill.id} value={skill.id}>
                      {skill.name} ({skill.category})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Proficiency Level
                </label>
                <select
                  value={newSkill.level}
                  onChange={(e) => setNewSkill(prev => ({ ...prev, level: e.target.value }))}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {skillLevels.map((level) => (
                    <option key={level.value} value={level.value}>
                      {level.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Years of Experience
                </label>
                <input
                  type="number"
                  min="0"
                  value={newSkill.years_experience}
                  onChange={(e) => setNewSkill(prev => ({ ...prev, years_experience: e.target.value }))}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="mt-6 flex space-x-4">
              <button
                onClick={handleAddSkill}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <CheckIcon className="h-4 w-4" />
                <span>Add Skill</span>
              </button>
              <button
                onClick={() => setShowAddSkill(false)}
                className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Profile;
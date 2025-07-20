import React, { useEffect, useState } from 'react';
import { 
  MicrophoneIcon, 
  VideoCameraIcon,
  PhoneXMarkIcon,
  ComputerDesktopIcon,
  SpeakerWaveIcon,
  ExclamationTriangleIcon,
  UserIcon,
  ClockIcon,
  PencilSquareIcon
} from '@heroicons/react/24/outline';
import { 
  MicrophoneIcon as MicrophoneIconSolid,
  VideoCameraIcon as VideoCameraIconSolid,
  ComputerDesktopIcon as ComputerDesktopIconSolid,
  SpeakerWaveIcon as SpeakerWaveIconSolid,
  PencilSquareIcon as PencilSquareIconSolid
} from '@heroicons/react/24/solid';
import useWebRTC from '../hooks/useWebRTC';
import Whiteboard from './Whiteboard';

const VideoChat = ({ sessionId, onClose, sessionDetails }) => {
  const {
    localStream,
    remoteStream,
    isConnected,
    isConnecting,
    error,
    connectionStatus,
    participants,
    isMuted,
    isVideoOff,
    isScreenSharing,
    localVideoRef,
    remoteVideoRef,
    connect,
    disconnect,
    startCall,
    toggleMute,
    toggleVideo,
    toggleScreenShare
  } = useWebRTC(sessionId);

  const [callDuration, setCallDuration] = useState(0);
  const [callStartTime, setCallStartTime] = useState(null);
  const [showControls, setShowControls] = useState(true);
  const [fullScreen, setFullScreen] = useState(false);

  // Call duration timer
  useEffect(() => {
    let interval = null;
    if (isConnected && !callStartTime) {
      setCallStartTime(Date.now());
    }
    
    if (isConnected && callStartTime) {
      interval = setInterval(() => {
        setCallDuration(Math.floor((Date.now() - callStartTime) / 1000));
      }, 1000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isConnected, callStartTime]);

  // Auto-hide controls
  useEffect(() => {
    if (!showControls) return;
    
    const timer = setTimeout(() => {
      setShowControls(false);
    }, 5000);
    
    return () => clearTimeout(timer);
  }, [showControls]);

  // Connect when component mounts
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Format call duration
  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Handle end call
  const handleEndCall = () => {
    disconnect();
    onClose();
  };

  // Get connection status color
  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-500';
      case 'connecting': return 'text-yellow-500';
      case 'failed': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  return (
    <div 
      className={`fixed inset-0 bg-black z-50 flex flex-col ${fullScreen ? 'cursor-none' : ''}`}
      onMouseMove={() => setShowControls(true)}
      onClick={() => setShowControls(true)}
    >
      {/* Header */}
      <div className={`absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-black/70 to-transparent p-4 transition-opacity duration-300 ${showControls ? 'opacity-100' : 'opacity-0'}`}>
        <div className="flex justify-between items-center text-white">
          <div>
            <h2 className="text-xl font-semibold">{sessionDetails?.title || 'Video Call'}</h2>
            <div className="flex items-center space-x-4 text-sm opacity-90">
              <div className="flex items-center space-x-1">
                <div className={`w-2 h-2 rounded-full ${getStatusColor()}`}></div>
                <span className="capitalize">{connectionStatus}</span>
              </div>
              {isConnected && (
                <div className="flex items-center space-x-1">
                  <ClockIcon className="h-4 w-4" />
                  <span>{formatDuration(callDuration)}</span>
                </div>
              )}
              <div className="flex items-center space-x-1">
                <UserIcon className="h-4 w-4" />
                <span>{participants.length + 1} participant{participants.length !== 0 ? 's' : ''}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Video Container */}
      <div className="flex-1 relative">
        {/* Remote Video (Main) */}
        <div className="absolute inset-0">
          {remoteStream ? (
            <video
              ref={remoteVideoRef}
              autoPlay
              playsInline
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-gray-900 flex items-center justify-center">
              <div className="text-center text-white">
                {isConnecting ? (
                  <div>
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                    <p>Connecting to video call...</p>
                  </div>
                ) : (
                  <div>
                    <UserIcon className="h-24 w-24 mx-auto mb-4 opacity-50" />
                    <p className="text-lg">Waiting for other participant...</p>
                    <p className="text-sm opacity-75 mt-2">Share this session with others to start the call</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Local Video (Picture-in-Picture) */}
        <div className="absolute top-4 right-4 w-64 h-48 bg-gray-800 rounded-lg overflow-hidden shadow-lg">
          {localStream ? (
            <video
              ref={localVideoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <UserIcon className="h-16 w-16 text-gray-500" />
            </div>
          )}
          {isVideoOff && (
            <div className="absolute inset-0 bg-black flex items-center justify-center">
              <VideoCameraIconSolid className="h-8 w-8 text-gray-500" />
            </div>
          )}
        </div>

        {/* Screen Sharing Indicator */}
        {isScreenSharing && (
          <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg">
            <div className="flex items-center space-x-2">
              <ComputerDesktopIconSolid className="h-5 w-5" />
              <span>You're sharing your screen</span>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="absolute top-20 left-1/2 transform -translate-x-1/2 bg-red-600 text-white px-6 py-3 rounded-lg shadow-lg max-w-md">
            <div className="flex items-center space-x-2">
              <ExclamationTriangleIcon className="h-5 w-5" />
              <span>{error}</span>
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className={`absolute bottom-0 left-0 right-0 z-10 bg-gradient-to-t from-black/70 to-transparent p-6 transition-opacity duration-300 ${showControls ? 'opacity-100' : 'opacity-0'}`}>
        <div className="flex justify-center items-center space-x-4">
          {/* Mute Toggle */}
          <button
            onClick={toggleMute}
            className={`p-4 rounded-full transition-colors ${
              isMuted 
                ? 'bg-red-600 hover:bg-red-700' 
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
            title={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? (
              <MicrophoneIconSolid className="h-6 w-6 text-white" />
            ) : (
              <MicrophoneIcon className="h-6 w-6 text-white" />
            )}
          </button>

          {/* Video Toggle */}
          <button
            onClick={toggleVideo}
            className={`p-4 rounded-full transition-colors ${
              isVideoOff 
                ? 'bg-red-600 hover:bg-red-700' 
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
            title={isVideoOff ? 'Turn on camera' : 'Turn off camera'}
          >
            {isVideoOff ? (
              <VideoCameraIconSolid className="h-6 w-6 text-white" />
            ) : (
              <VideoCameraIcon className="h-6 w-6 text-white" />
            )}
          </button>

          {/* Screen Share Toggle */}
          <button
            onClick={toggleScreenShare}
            className={`p-4 rounded-full transition-colors ${
              isScreenSharing 
                ? 'bg-blue-600 hover:bg-blue-700' 
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
            title={isScreenSharing ? 'Stop sharing' : 'Share screen'}
          >
            {isScreenSharing ? (
              <ComputerDesktopIconSolid className="h-6 w-6 text-white" />
            ) : (
              <ComputerDesktopIcon className="h-6 w-6 text-white" />
            )}
          </button>

          {/* End Call */}
          <button
            onClick={handleEndCall}
            className="p-4 rounded-full bg-red-600 hover:bg-red-700 transition-colors"
            title="End call"
          >
            <PhoneXMarkIcon className="h-6 w-6 text-white" />
          </button>

          {/* Fullscreen Toggle */}
          <button
            onClick={() => setFullScreen(!fullScreen)}
            className="p-4 rounded-full bg-gray-700 hover:bg-gray-600 transition-colors"
            title={fullScreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          >
            <SpeakerWaveIcon className="h-6 w-6 text-white" />
          </button>
        </div>

        {/* Call Info */}
        <div className="text-center text-white mt-4 text-sm opacity-75">
          <p>Move mouse to show controls • Click anywhere to show controls</p>
          {!isConnected && !isConnecting && (
            <p className="mt-1">Waiting for connection...</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default VideoChat;
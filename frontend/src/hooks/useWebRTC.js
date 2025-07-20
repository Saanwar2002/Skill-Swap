import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

const useWebRTC = (sessionId) => {
  const { token } = useAuth();
  const [localStream, setLocalStream] = useState(null);
  const [remoteStream, setRemoteStream] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [participants, setParticipants] = useState([]);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  
  // Whiteboard state
  const [whiteboardEvents, setWhiteboardEvents] = useState([]);

  const peerConnectionRef = useRef(null);
  const websocketRef = useRef(null);
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const screenStreamRef = useRef(null);
  const originalStreamRef = useRef(null);

  const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  const WS_BASE = API_BASE.replace('https://', 'wss://').replace('http://', 'ws://');

  // WebRTC Configuration
  const rtcConfig = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' }
    ]
  };

  // Initialize media stream
  const initializeMedia = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 },
        audio: { echoCancellation: true, noiseSuppression: true }
      });
      
      setLocalStream(stream);
      originalStreamRef.current = stream;
      
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }
      
      return stream;
    } catch (err) {
      console.error('Error accessing media devices:', err);
      setError('Failed to access camera/microphone. Please check permissions.');
      throw err;
    }
  }, []);

  // Create peer connection
  const createPeerConnection = useCallback(() => {
    const peerConnection = new RTCPeerConnection(rtcConfig);
    
    peerConnection.onicecandidate = (event) => {
      if (event.candidate && websocketRef.current) {
        websocketRef.current.send(JSON.stringify({
          type: 'ice-candidate',
          target_user_id: participants[0], // For now, assume single participant
          data: event.candidate
        }));
      }
    };
    
    peerConnection.ontrack = (event) => {
      console.log('Received remote stream:', event);
      const remoteStream = event.streams[0];
      setRemoteStream(remoteStream);
      
      if (remoteVideoRef.current) {
        remoteVideoRef.current.srcObject = remoteStream;
      }
    };
    
    peerConnection.onconnectionstatechange = () => {
      console.log('Connection state changed:', peerConnection.connectionState);
      setConnectionStatus(peerConnection.connectionState);
      
      if (peerConnection.connectionState === 'connected') {
        setIsConnected(true);
        setIsConnecting(false);
      } else if (peerConnection.connectionState === 'failed' || 
                 peerConnection.connectionState === 'disconnected') {
        setIsConnected(false);
        setIsConnecting(false);
      }
    };
    
    return peerConnection;
  }, [participants]);

  // Connect to WebSocket signaling
  const connectWebSocket = useCallback(() => {
    if (!sessionId || !token) return;

    const wsUrl = `${WS_BASE}/api/webrtc/ws/${sessionId}?token=${token}`;
    const websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
      console.log('WebSocket connected for session:', sessionId);
      setConnectionStatus('connected');
    };
    
    websocket.onmessage = async (event) => {
      const message = JSON.parse(event.data);
      console.log('Received message:', message);
      
      switch (message.type) {
        case 'connected':
          console.log('WebRTC signaling connected:', message);
          break;
          
        case 'user_joined':
          setParticipants(prev => [...prev, message.user_id]);
          break;
          
        case 'user_left':
          setParticipants(prev => prev.filter(id => id !== message.user_id));
          break;
          
        case 'offer':
          await handleOffer(message);
          break;
          
        case 'answer':
          await handleAnswer(message);
          break;
          
        case 'ice-candidate':
          await handleIceCandidate(message);
          break;
          
        case 'call_started':
          console.log('Call started by:', message.initiated_by);
          break;
          
        case 'call_ended':
          console.log('Call ended by:', message.ended_by);
          disconnect();
          break;
          
        default:
          console.log('Unknown message type:', message.type);
      }
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket connection failed');
      setConnectionStatus('failed');
    };
    
    websocket.onclose = () => {
      console.log('WebSocket disconnected');
      setConnectionStatus('disconnected');
      setIsConnected(false);
    };
    
    websocketRef.current = websocket;
  }, [sessionId, token]);

  // Handle offer
  const handleOffer = async (message) => {
    try {
      if (!peerConnectionRef.current) {
        peerConnectionRef.current = createPeerConnection();
      }
      
      const peerConnection = peerConnectionRef.current;
      await peerConnection.setRemoteDescription(new RTCSessionDescription(message.data));
      
      // Add local stream tracks
      if (localStream) {
        localStream.getTracks().forEach(track => {
          peerConnection.addTrack(track, localStream);
        });
      }
      
      const answer = await peerConnection.createAnswer();
      await peerConnection.setLocalDescription(answer);
      
      if (websocketRef.current) {
        websocketRef.current.send(JSON.stringify({
          type: 'answer',
          target_user_id: message.from_user_id,
          data: answer
        }));
      }
    } catch (err) {
      console.error('Error handling offer:', err);
      setError('Failed to handle call offer');
    }
  };

  // Handle answer
  const handleAnswer = async (message) => {
    try {
      if (peerConnectionRef.current) {
        await peerConnectionRef.current.setRemoteDescription(
          new RTCSessionDescription(message.data)
        );
      }
    } catch (err) {
      console.error('Error handling answer:', err);
      setError('Failed to handle call answer');
    }
  };

  // Handle ICE candidate
  const handleIceCandidate = async (message) => {
    try {
      if (peerConnectionRef.current && message.data) {
        await peerConnectionRef.current.addIceCandidate(
          new RTCIceCandidate(message.data)
        );
      }
    } catch (err) {
      console.error('Error handling ICE candidate:', err);
    }
  };

  // Start call
  const startCall = async (targetUserId) => {
    try {
      setIsConnecting(true);
      
      if (!peerConnectionRef.current) {
        peerConnectionRef.current = createPeerConnection();
      }
      
      const peerConnection = peerConnectionRef.current;
      
      // Add local stream tracks
      if (localStream) {
        localStream.getTracks().forEach(track => {
          peerConnection.addTrack(track, localStream);
        });
      }
      
      const offer = await peerConnection.createOffer({
        offerToReceiveAudio: true,
        offerToReceiveVideo: true
      });
      
      await peerConnection.setLocalDescription(offer);
      
      if (websocketRef.current) {
        websocketRef.current.send(JSON.stringify({
          type: 'offer',
          target_user_id: targetUserId,
          data: offer
        }));
      }
    } catch (err) {
      console.error('Error starting call:', err);
      setError('Failed to start call');
      setIsConnecting(false);
    }
  };

  // Toggle mute
  const toggleMute = useCallback(() => {
    if (localStream) {
      const audioTracks = localStream.getAudioTracks();
      audioTracks.forEach(track => {
        track.enabled = !track.enabled;
      });
      setIsMuted(!isMuted);
    }
  }, [localStream, isMuted]);

  // Toggle video
  const toggleVideo = useCallback(() => {
    if (localStream) {
      const videoTracks = localStream.getVideoTracks();
      videoTracks.forEach(track => {
        track.enabled = !track.enabled;
      });
      setIsVideoOff(!isVideoOff);
    }
  }, [localStream, isVideoOff]);

  // Screen sharing
  const toggleScreenShare = useCallback(async () => {
    try {
      if (isScreenSharing) {
        // Stop screen sharing, switch back to camera
        if (screenStreamRef.current) {
          screenStreamRef.current.getTracks().forEach(track => track.stop());
          screenStreamRef.current = null;
        }
        
        if (originalStreamRef.current && peerConnectionRef.current) {
          const videoTrack = originalStreamRef.current.getVideoTracks()[0];
          const sender = peerConnectionRef.current.getSenders().find(s => 
            s.track && s.track.kind === 'video'
          );
          
          if (sender && videoTrack) {
            await sender.replaceTrack(videoTrack);
          }
          
          setLocalStream(originalStreamRef.current);
          if (localVideoRef.current) {
            localVideoRef.current.srcObject = originalStreamRef.current;
          }
        }
        
        setIsScreenSharing(false);
      } else {
        // Start screen sharing
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: true
        });
        
        screenStreamRef.current = screenStream;
        
        if (peerConnectionRef.current) {
          const videoTrack = screenStream.getVideoTracks()[0];
          const sender = peerConnectionRef.current.getSenders().find(s => 
            s.track && s.track.kind === 'video'
          );
          
          if (sender && videoTrack) {
            await sender.replaceTrack(videoTrack);
          }
          
          // Handle screen share end
          videoTrack.onended = () => {
            toggleScreenShare(); // This will switch back to camera
          };
        }
        
        setLocalStream(screenStream);
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = screenStream;
        }
        
        setIsScreenSharing(true);
      }
    } catch (err) {
      console.error('Error toggling screen share:', err);
      setError('Failed to share screen');
    }
  }, [isScreenSharing]);

  // Connect to session
  const connect = useCallback(async () => {
    try {
      setError(null);
      setIsConnecting(true);
      
      await initializeMedia();
      connectWebSocket();
    } catch (err) {
      console.error('Error connecting to session:', err);
      setError(err.message);
      setIsConnecting(false);
    }
  }, [initializeMedia, connectWebSocket]);

  // Disconnect
  const disconnect = useCallback(() => {
    // Stop all tracks
    if (localStream) {
      localStream.getTracks().forEach(track => track.stop());
    }
    if (screenStreamRef.current) {
      screenStreamRef.current.getTracks().forEach(track => track.stop());
    }
    
    // Close peer connection
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }
    
    // Close WebSocket
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    
    // Reset state
    setLocalStream(null);
    setRemoteStream(null);
    setIsConnected(false);
    setIsConnecting(false);
    setConnectionStatus('disconnected');
    setParticipants([]);
    setIsMuted(false);
    setIsVideoOff(false);
    setIsScreenSharing(false);
    
    screenStreamRef.current = null;
    originalStreamRef.current = null;
  }, [localStream]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
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
  };
};

export default useWebRTC;
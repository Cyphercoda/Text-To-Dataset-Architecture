/**
 * Chat Page Component
 * AI-powered chat interface for document analysis and assistance
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

// Components
import MessageList from '../../components/chat/MessageList';
import MessageInput from '../../components/chat/MessageInput';
import ChatSidebar from '../../components/chat/ChatSidebar';
import TypingIndicator from '../../components/chat/TypingIndicator';
import AttachmentPreview from '../../components/chat/AttachmentPreview';
import LoadingSpinner from '../../components/ui/LoadingSpinner';

// Hooks and Services
import { useChatStore } from '../../stores/realTimeStore';
import { useWebSocket } from '../../services/webSocketService';
import { chatAPI } from '../../services/api/chat';

// Types
import { ChatMessage, ChatSession, AttachmentFile } from '../../types';

// Icons
import {
  PaperAirplaneIcon,
  PaperClipIcon,
  MicrophoneIcon,
  StopIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

const ChatPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const {
    sessions,
    activeSession,
    setActiveSession,
    addMessage,
    subscribeToSession,
    setTypingIndicator,
  } = useChatStore();
  
  const { subscribeToChatMessages, send } = useWebSocket();
  
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [messageInput, setMessageInput] = useState('');
  const [attachments, setAttachments] = useState<AttachmentFile[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  // Fetch chat sessions
  const {
    data: sessionsData,
    isLoading: isSessionsLoading,
  } = useQuery({
    queryKey: ['chat', 'sessions'],
    queryFn: chatAPI.getSessions,
  });

  // Fetch session messages
  const {
    data: messagesData,
    isLoading: isMessagesLoading,
    refetch: refetchMessages,
  } = useQuery({
    queryKey: ['chat', 'messages', sessionId],
    queryFn: () => sessionId ? chatAPI.getMessages(sessionId) : Promise.resolve([]),
    enabled: !!sessionId,
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: ({ sessionId, message, attachments }: {
      sessionId: string;
      message: string;
      attachments?: AttachmentFile[];
    }) => chatAPI.sendMessage(sessionId, message, attachments),
    onSuccess: (data) => {
      // Message will be added via WebSocket, so we don't need to add it here
      setMessageInput('');
      setAttachments([]);
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages', sessionId] });
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to send message');
    },
  });

  // Create new session mutation
  const createSessionMutation = useMutation({
    mutationFn: (name?: string) => chatAPI.createSession({ name }),
    onSuccess: (session) => {
      navigate(`/chat/${session.id}`);
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions'] });
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to create chat session');
    },
  });

  // Subscribe to WebSocket messages for current session
  useEffect(() => {
    if (!sessionId) return;

    const unsubscribe = subscribeToChatMessages(sessionId, (data) => {
      if (data.type === 'message') {
        addMessage(sessionId, data.message);
        
        // Scroll to bottom after message is added
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      } else if (data.type === 'typing') {
        setTypingIndicator(sessionId, data.isTyping);
        setIsTyping(data.isTyping);
      }
    });

    return unsubscribe;
  }, [sessionId, subscribeToChatMessages, addMessage, setTypingIndicator]);

  // Set active session
  useEffect(() => {
    if (sessionId && sessionsData) {
      const session = sessionsData.find(s => s.id === sessionId);
      if (session) {
        setActiveSession(session);
      }
    }
  }, [sessionId, sessionsData, setActiveSession]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messagesData]);

  // Handle message send
  const handleSendMessage = useCallback(async () => {
    if (!messageInput.trim() && attachments.length === 0) return;
    if (!sessionId) {
      // Create new session first
      createSessionMutation.mutate();
      return;
    }

    try {
      await sendMessageMutation.mutateAsync({
        sessionId,
        message: messageInput.trim(),
        attachments,
      });
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  }, [messageInput, attachments, sessionId, sendMessageMutation, createSessionMutation]);

  // Handle key press in input
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Handle file attachment
  const handleFileSelect = (files: FileList) => {
    const newAttachments: AttachmentFile[] = Array.from(files).map(file => ({
      id: `${file.name}-${Date.now()}`,
      file,
      name: file.name,
      size: file.size,
      type: file.type,
    }));
    
    setAttachments(prev => [...prev, ...newAttachments]);
  };

  // Remove attachment
  const removeAttachment = (id: string) => {
    setAttachments(prev => prev.filter(a => a.id !== id));
  };

  // Voice recording functions
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      const chunks: BlobPart[] = [];
      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        const audioFile: AttachmentFile = {
          id: `voice-${Date.now()}`,
          file: new File([audioBlob], 'voice-message.webm', { type: 'audio/webm' }),
          name: 'Voice Message',
          size: audioBlob.size,
          type: 'audio/webm',
        };
        setAttachments(prev => [...prev, audioFile]);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      toast.error('Could not access microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Create new chat session
  const handleNewChat = () => {
    createSessionMutation.mutate();
  };

  // Loading state
  if (isSessionsLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-80 bg-white border-r transform transition-transform
        lg:relative lg:translate-x-0 lg:block
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <ChatSidebar
          sessions={sessionsData || []}
          activeSessionId={sessionId}
          onSessionSelect={(id) => {
            navigate(`/chat/${id}`);
            setSidebarOpen(false);
          }}
          onNewChat={handleNewChat}
          onCloseSidebar={() => setSidebarOpen(false)}
          loading={createSessionMutation.isPending}
        />
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="bg-white border-b px-4 py-3 flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 text-gray-500 hover:text-gray-700 lg:hidden"
            >
              <Bars3Icon className="h-5 w-5" />
            </button>
            <h1 className="text-lg font-semibold text-gray-900 ml-2">
              {activeSession?.name || 'New Chat'}
            </h1>
          </div>
          
          {/* Session info */}
          {activeSession && (
            <div className="text-sm text-gray-500">
              {activeSession.messages?.length || 0} messages
            </div>
          )}
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto p-4">
          {sessionId ? (
            <>
              {isMessagesLoading ? (
                <div className="flex justify-center py-8">
                  <LoadingSpinner />
                </div>
              ) : (
                <MessageList
                  messages={messagesData || []}
                  loading={isMessagesLoading}
                />
              )}
              
              {/* Typing indicator */}
              {isTyping && <TypingIndicator />}
              
              {/* Scroll anchor */}
              <div ref={messagesEndRef} />
            </>
          ) : (
            // Welcome message for no session
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                  Welcome to AI Assistant
                </h2>
                <p className="text-gray-600 mb-4">
                  Start a new conversation to get help with your documents and datasets
                </p>
                <button
                  onClick={handleNewChat}
                  disabled={createSessionMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {createSessionMutation.isPending ? 'Creating...' : 'Start New Chat'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Input area */}
        {sessionId && (
          <div className="bg-white border-t p-4">
            {/* Attachment previews */}
            {attachments.length > 0 && (
              <AttachmentPreview
                attachments={attachments}
                onRemove={removeAttachment}
                className="mb-3"
              />
            )}

            {/* Message input */}
            <div className="flex items-end space-x-2">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message... (Shift+Enter for new line)"
                  className="w-full px-4 py-2 pr-12 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={Math.min(Math.max(messageInput.split('\n').length, 1), 4)}
                  disabled={sendMessageMutation.isPending}
                />
                
                {/* Attachment button */}
                <label className="absolute right-2 bottom-2 p-1 text-gray-400 hover:text-gray-600 cursor-pointer">
                  <PaperClipIcon className="h-5 w-5" />
                  <input
                    type="file"
                    multiple
                    className="hidden"
                    onChange={(e) => e.target.files && handleFileSelect(e.target.files)}
                    accept=".pdf,.doc,.docx,.txt,.md,.rtf,image/*"
                  />
                </label>
              </div>

              {/* Voice recording button */}
              <button
                onClick={isRecording ? stopRecording : startRecording}
                className={`p-2 rounded-lg ${
                  isRecording
                    ? 'bg-red-500 text-white animate-pulse'
                    : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
                }`}
              >
                {isRecording ? (
                  <StopIcon className="h-5 w-5" />
                ) : (
                  <MicrophoneIcon className="h-5 w-5" />
                )}
              </button>

              {/* Send button */}
              <button
                onClick={handleSendMessage}
                disabled={(!messageInput.trim() && attachments.length === 0) || sendMessageMutation.isPending}
                className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {sendMessageMutation.isPending ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <PaperAirplaneIcon className="h-5 w-5" />
                )}
              </button>
            </div>

            <p className="text-xs text-gray-500 mt-2">
              AI assistant can help you analyze documents, generate datasets, and answer questions about your data.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatPage;
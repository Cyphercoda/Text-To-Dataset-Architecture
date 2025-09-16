/**
 * Enhanced State Management for Real-time Data
 * Integrates with WebSocket service for live updates
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { webSocketService } from '../services/webSocketService';

// Types for real-time data
export interface ProcessingJob {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  estimatedCompletion?: string;
  documentsProcessed: number;
  totalDocuments: number;
  currentStage: string;
  errors?: string[];
  createdAt: string;
  updatedAt: string;
}

export interface ChatSession {
  id: string;
  name: string;
  messages: ChatMessage[];
  isTyping: boolean;
  lastActivity: string;
  participantCount: number;
}

export interface ChatMessage {
  id: string;
  sessionId: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: string;
  attachments?: File[];
  metadata?: Record<string, any>;
}

export interface SystemNotification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actions?: NotificationAction[];
  expiresAt?: string;
}

export interface NotificationAction {
  id: string;
  label: string;
  action: string;
  primary?: boolean;
}

export interface RealTimeMetrics {
  activeUsers: number;
  processingQueue: number;
  systemStatus: 'operational' | 'degraded' | 'down';
  averageProcessingTime: number;
  successRate: number;
  lastUpdated: string;
}

// Enhanced Processing Store with Real-time Updates
interface ProcessingStore {
  jobs: ProcessingJob[];
  activeJob: ProcessingJob | null;
  subscribedJobs: Set<string>;
  isConnected: boolean;
  
  // Actions
  addJob: (job: ProcessingJob) => void;
  updateJob: (jobId: string, updates: Partial<ProcessingJob>) => void;
  removeJob: (jobId: string) => void;
  subscribeToJob: (jobId: string) => () => void;
  unsubscribeFromJob: (jobId: string) => void;
  setActiveJob: (job: ProcessingJob | null) => void;
  syncJobs: (jobs: ProcessingJob[]) => void;
}

export const useProcessingStore = create<ProcessingStore>()(
  subscribeWithSelector((set, get) => ({
    jobs: [],
    activeJob: null,
    subscribedJobs: new Set(),
    isConnected: false,

    addJob: (job) => {
      set((state) => ({
        jobs: [job, ...state.jobs]
      }));
      
      // Auto-subscribe to new jobs
      get().subscribeToJob(job.id);
    },

    updateJob: (jobId, updates) => {
      set((state) => ({
        jobs: state.jobs.map(job => 
          job.id === jobId 
            ? { ...job, ...updates, updatedAt: new Date().toISOString() }
            : job
        ),
        activeJob: state.activeJob?.id === jobId 
          ? { ...state.activeJob, ...updates, updatedAt: new Date().toISOString() }
          : state.activeJob
      }));
    },

    removeJob: (jobId) => {
      get().unsubscribeFromJob(jobId);
      set((state) => ({
        jobs: state.jobs.filter(job => job.id !== jobId),
        activeJob: state.activeJob?.id === jobId ? null : state.activeJob
      }));
    },

    subscribeToJob: (jobId) => {
      const { subscribedJobs } = get();
      
      if (subscribedJobs.has(jobId)) {
        return () => {}; // Already subscribed
      }

      const unsubscribe = webSocketService.subscribeToJobProgress(jobId, (data) => {
        get().updateJob(jobId, {
          status: data.status,
          progress: data.progress,
          currentStage: data.currentStage,
          estimatedCompletion: data.estimatedCompletion,
          documentsProcessed: data.documentsProcessed,
          errors: data.errors
        });
      });

      set((state) => ({
        subscribedJobs: new Set([...state.subscribedJobs, jobId])
      }));

      return () => {
        unsubscribe();
        get().unsubscribeFromJob(jobId);
      };
    },

    unsubscribeFromJob: (jobId) => {
      set((state) => {
        const newSubscribed = new Set(state.subscribedJobs);
        newSubscribed.delete(jobId);
        return { subscribedJobs: newSubscribed };
      });
    },

    setActiveJob: (job) => {
      set({ activeJob: job });
      if (job) {
        get().subscribeToJob(job.id);
      }
    },

    syncJobs: (jobs) => {
      set({ jobs });
      // Subscribe to all active jobs
      jobs
        .filter(job => ['pending', 'processing'].includes(job.status))
        .forEach(job => get().subscribeToJob(job.id));
    }
  }))
);

// Chat Store with Real-time Messaging
interface ChatStore {
  sessions: ChatSession[];
  activeSession: ChatSession | null;
  subscribedSessions: Set<string>;
  isConnected: boolean;
  
  // Actions
  addSession: (session: ChatSession) => void;
  updateSession: (sessionId: string, updates: Partial<ChatSession>) => void;
  removeSession: (sessionId: string) => void;
  addMessage: (sessionId: string, message: ChatMessage) => void;
  setActiveSession: (session: ChatSession | null) => void;
  subscribeToSession: (sessionId: string) => () => void;
  unsubscribeFromSession: (sessionId: string) => void;
  setTypingIndicator: (sessionId: string, isTyping: boolean) => void;
}

export const useChatStore = create<ChatStore>()(
  subscribeWithSelector((set, get) => ({
    sessions: [],
    activeSession: null,
    subscribedSessions: new Set(),
    isConnected: false,

    addSession: (session) => {
      set((state) => ({
        sessions: [session, ...state.sessions]
      }));
    },

    updateSession: (sessionId, updates) => {
      set((state) => ({
        sessions: state.sessions.map(session =>
          session.id === sessionId
            ? { ...session, ...updates, lastActivity: new Date().toISOString() }
            : session
        ),
        activeSession: state.activeSession?.id === sessionId
          ? { ...state.activeSession, ...updates, lastActivity: new Date().toISOString() }
          : state.activeSession
      }));
    },

    removeSession: (sessionId) => {
      get().unsubscribeFromSession(sessionId);
      set((state) => ({
        sessions: state.sessions.filter(session => session.id !== sessionId),
        activeSession: state.activeSession?.id === sessionId ? null : state.activeSession
      }));
    },

    addMessage: (sessionId, message) => {
      set((state) => ({
        sessions: state.sessions.map(session =>
          session.id === sessionId
            ? {
                ...session,
                messages: [...session.messages, message],
                lastActivity: new Date().toISOString()
              }
            : session
        ),
        activeSession: state.activeSession?.id === sessionId
          ? {
              ...state.activeSession,
              messages: [...state.activeSession.messages, message],
              lastActivity: new Date().toISOString()
            }
          : state.activeSession
      }));
    },

    setActiveSession: (session) => {
      set({ activeSession: session });
      if (session) {
        get().subscribeToSession(session.id);
      }
    },

    subscribeToSession: (sessionId) => {
      const { subscribedSessions } = get();
      
      if (subscribedSessions.has(sessionId)) {
        return () => {}; // Already subscribed
      }

      const unsubscribe = webSocketService.subscribeToChatMessages(sessionId, (data) => {
        if (data.type === 'message') {
          get().addMessage(sessionId, data.message);
        } else if (data.type === 'typing') {
          get().setTypingIndicator(sessionId, data.isTyping);
        }
      });

      set((state) => ({
        subscribedSessions: new Set([...state.subscribedSessions, sessionId])
      }));

      return () => {
        unsubscribe();
        get().unsubscribeFromSession(sessionId);
      };
    },

    unsubscribeFromSession: (sessionId) => {
      set((state) => {
        const newSubscribed = new Set(state.subscribedSessions);
        newSubscribed.delete(sessionId);
        return { subscribedSessions: newSubscribed };
      });
    },

    setTypingIndicator: (sessionId, isTyping) => {
      get().updateSession(sessionId, { isTyping });
    }
  }))
);

// Notifications Store with Real-time Updates
interface NotificationStore {
  notifications: SystemNotification[];
  unreadCount: number;
  isConnected: boolean;
  
  // Actions
  addNotification: (notification: SystemNotification) => void;
  markAsRead: (notificationId: string) => void;
  markAllAsRead: () => void;
  removeNotification: (notificationId: string) => void;
  clearExpired: () => void;
  subscribeToNotifications: () => () => void;
}

export const useNotificationStore = create<NotificationStore>()(
  subscribeWithSelector((set, get) => ({
    notifications: [],
    unreadCount: 0,
    isConnected: false,

    addNotification: (notification) => {
      set((state) => {
        const newNotifications = [notification, ...state.notifications];
        return {
          notifications: newNotifications,
          unreadCount: newNotifications.filter(n => !n.read).length
        };
      });

      // Auto-expire notifications if specified
      if (notification.expiresAt) {
        const expiryTime = new Date(notification.expiresAt).getTime() - Date.now();
        if (expiryTime > 0) {
          setTimeout(() => {
            get().removeNotification(notification.id);
          }, expiryTime);
        }
      }
    },

    markAsRead: (notificationId) => {
      set((state) => {
        const updatedNotifications = state.notifications.map(notification =>
          notification.id === notificationId
            ? { ...notification, read: true }
            : notification
        );
        return {
          notifications: updatedNotifications,
          unreadCount: updatedNotifications.filter(n => !n.read).length
        };
      });
    },

    markAllAsRead: () => {
      set((state) => ({
        notifications: state.notifications.map(n => ({ ...n, read: true })),
        unreadCount: 0
      }));
    },

    removeNotification: (notificationId) => {
      set((state) => {
        const filteredNotifications = state.notifications.filter(n => n.id !== notificationId);
        return {
          notifications: filteredNotifications,
          unreadCount: filteredNotifications.filter(n => !n.read).length
        };
      });
    },

    clearExpired: () => {
      const now = Date.now();
      set((state) => {
        const activeNotifications = state.notifications.filter(notification => {
          if (!notification.expiresAt) return true;
          return new Date(notification.expiresAt).getTime() > now;
        });
        return {
          notifications: activeNotifications,
          unreadCount: activeNotifications.filter(n => !n.read).length
        };
      });
    },

    subscribeToNotifications: () => {
      return webSocketService.subscribeToNotifications((notification) => {
        get().addNotification(notification);
      });
    }
  }))
);

// Real-time Metrics Store
interface MetricsStore {
  metrics: RealTimeMetrics;
  history: RealTimeMetrics[];
  maxHistoryItems: number;
  
  // Actions
  updateMetrics: (metrics: Partial<RealTimeMetrics>) => void;
  addToHistory: (metrics: RealTimeMetrics) => void;
  clearHistory: () => void;
}

export const useMetricsStore = create<MetricsStore>()((set, get) => ({
  metrics: {
    activeUsers: 0,
    processingQueue: 0,
    systemStatus: 'operational',
    averageProcessingTime: 0,
    successRate: 0,
    lastUpdated: new Date().toISOString()
  },
  history: [],
  maxHistoryItems: 100,

  updateMetrics: (newMetrics) => {
    set((state) => {
      const updatedMetrics = {
        ...state.metrics,
        ...newMetrics,
        lastUpdated: new Date().toISOString()
      };
      
      // Add to history
      const newHistory = [updatedMetrics, ...state.history].slice(0, state.maxHistoryItems);
      
      return {
        metrics: updatedMetrics,
        history: newHistory
      };
    });
  },

  addToHistory: (metrics) => {
    set((state) => ({
      history: [metrics, ...state.history].slice(0, state.maxHistoryItems)
    }));
  },

  clearHistory: () => {
    set({ history: [] });
  }
}));

// Connection Status Store
interface ConnectionStore {
  isWebSocketConnected: boolean;
  lastConnected: string | null;
  reconnectAttempts: number;
  connectionQuality: 'excellent' | 'good' | 'poor' | 'disconnected';
  
  // Actions
  setConnectionStatus: (connected: boolean) => void;
  updateConnectionQuality: (quality: ConnectionStore['connectionQuality']) => void;
  incrementReconnectAttempts: () => void;
  resetReconnectAttempts: () => void;
}

export const useConnectionStore = create<ConnectionStore>()((set) => ({
  isWebSocketConnected: false,
  lastConnected: null,
  reconnectAttempts: 0,
  connectionQuality: 'disconnected',

  setConnectionStatus: (connected) => {
    set((state) => ({
      isWebSocketConnected: connected,
      lastConnected: connected ? new Date().toISOString() : state.lastConnected,
      connectionQuality: connected ? 'good' : 'disconnected',
      reconnectAttempts: connected ? 0 : state.reconnectAttempts
    }));
  },

  updateConnectionQuality: (quality) => {
    set({ connectionQuality: quality });
  },

  incrementReconnectAttempts: () => {
    set((state) => ({ reconnectAttempts: state.reconnectAttempts + 1 }));
  },

  resetReconnectAttempts: () => {
    set({ reconnectAttempts: 0 });
  }
}));

// Initialization hook for real-time stores
export const useRealTimeStores = () => {
  const processingStore = useProcessingStore();
  const chatStore = useChatStore();
  const notificationStore = useNotificationStore();
  const connectionStore = useConnectionStore();

  React.useEffect(() => {
    // Subscribe to WebSocket connection status
    const unsubscribeConnection = webSocketService.subscribe('connection', (data) => {
      const isConnected = data.status === 'connected';
      connectionStore.setConnectionStatus(isConnected);
      
      if (isConnected) {
        // Subscribe to notifications when connected
        notificationStore.subscribeToNotifications();
      }
    });

    // Subscribe to system alerts
    const unsubscribeAlerts = webSocketService.subscribe('system_alert', (data) => {
      notificationStore.addNotification({
        id: `system-${Date.now()}`,
        type: data.level || 'info',
        title: 'System Alert',
        message: data.message,
        timestamp: new Date().toISOString(),
        read: false,
        expiresAt: data.expiresAt
      });
    });

    // Clean up expired notifications periodically
    const cleanupInterval = setInterval(() => {
      notificationStore.clearExpired();
    }, 60000); // Every minute

    return () => {
      unsubscribeConnection();
      unsubscribeAlerts();
      clearInterval(cleanupInterval);
    };
  }, []);

  return {
    processingStore,
    chatStore,
    notificationStore,
    connectionStore
  };
};
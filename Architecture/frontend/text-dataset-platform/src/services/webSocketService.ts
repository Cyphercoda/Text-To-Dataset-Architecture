/**
 * WebSocket Service for Real-time Communication
 * Handles all real-time updates for the text-to-dataset platform
 */

export interface WebSocketMessage {
  type: 'job_progress' | 'chat_message' | 'notification' | 'system_alert';
  data: any;
  timestamp: string;
  id: string;
}

export interface WebSocketConfig {
  url: string;
  reconnectAttempts: number;
  reconnectInterval: number;
  heartbeatInterval: number;
}

export class WebSocketService {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private reconnectCount = 0;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private isConnecting = false;

  constructor(config: WebSocketConfig) {
    this.config = config;
  }

  /**
   * Connect to WebSocket server
   */
  async connect(token: string): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return;
    }

    this.isConnecting = true;
    
    try {
      const wsUrl = `${this.config.url}?token=${token}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.isConnecting = false;
        this.reconnectCount = 0;
        this.startHeartbeat();
        this.emit('connection', { status: 'connected' });
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.isConnecting = false;
        this.stopHeartbeat();
        this.emit('connection', { status: 'disconnected' });
        
        if (event.code !== 1000 && this.reconnectCount < this.config.reconnectAttempts) {
          this.scheduleReconnect(token);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
        this.emit('error', { error: 'WebSocket connection failed' });
      };

    } catch (error) {
      this.isConnecting = false;
      throw error;
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  /**
   * Subscribe to specific message types
   */
  subscribe(type: string, callback: (data: any) => void): () => void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    
    this.listeners.get(type)!.add(callback);
    
    // Return unsubscribe function
    return () => {
      const typeListeners = this.listeners.get(type);
      if (typeListeners) {
        typeListeners.delete(callback);
        if (typeListeners.size === 0) {
          this.listeners.delete(type);
        }
      }
    };
  }

  /**
   * Subscribe to job progress updates
   */
  subscribeToJobProgress(jobId: string, callback: (progress: any) => void): () => void {
    return this.subscribe(`job_progress_${jobId}`, callback);
  }

  /**
   * Subscribe to chat messages
   */
  subscribeToChatMessages(sessionId: string, callback: (message: any) => void): () => void {
    return this.subscribe(`chat_${sessionId}`, callback);
  }

  /**
   * Subscribe to system notifications
   */
  subscribeToNotifications(callback: (notification: any) => void): () => void {
    return this.subscribe('notification', callback);
  }

  /**
   * Send message to server
   */
  send(type: string, data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      const message = {
        type,
        data,
        timestamp: new Date().toISOString(),
        id: this.generateId()
      };
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected. Cannot send message:', type);
    }
  }

  /**
   * Handle incoming messages
   */
  private handleMessage(message: WebSocketMessage): void {
    const { type, data } = message;
    
    // Handle different message types
    switch (type) {
      case 'job_progress':
        this.emit(`job_progress_${data.jobId}`, data);
        break;
      case 'chat_message':
        this.emit(`chat_${data.sessionId}`, data);
        break;
      case 'notification':
        this.emit('notification', data);
        break;
      case 'system_alert':
        this.emit('system_alert', data);
        break;
      default:
        this.emit(type, data);
    }
  }

  /**
   * Emit message to subscribers
   */
  private emit(type: string, data: any): void {
    const listeners = this.listeners.get(type);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in WebSocket callback:', error);
        }
      });
    }
  }

  /**
   * Schedule reconnection
   */
  private scheduleReconnect(token: string): void {
    this.reconnectCount++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectCount), 30000);
    
    setTimeout(() => {
      console.log(`Attempting WebSocket reconnection (${this.reconnectCount}/${this.config.reconnectAttempts})`);
      this.connect(token);
    }, delay);
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send('ping', { timestamp: Date.now() });
      }
    }, this.config.heartbeatInterval);
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Generate unique message ID
   */
  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get connection status
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Create singleton instance
export const webSocketService = new WebSocketService({
  url: process.env.REACT_APP_WS_URL || 'wss://api.textdataset.com/ws',
  reconnectAttempts: 5,
  reconnectInterval: 1000,
  heartbeatInterval: 30000
});

// React hook for WebSocket integration
export const useWebSocket = () => {
  const [isConnected, setIsConnected] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const unsubscribeConnection = webSocketService.subscribe('connection', (data) => {
      setIsConnected(data.status === 'connected');
    });

    const unsubscribeError = webSocketService.subscribe('error', (data) => {
      setError(data.error);
    });

    return () => {
      unsubscribeConnection();
      unsubscribeError();
    };
  }, []);

  return {
    isConnected,
    error,
    subscribe: webSocketService.subscribe.bind(webSocketService),
    subscribeToJobProgress: webSocketService.subscribeToJobProgress.bind(webSocketService),
    subscribeToChatMessages: webSocketService.subscribeToChatMessages.bind(webSocketService),
    subscribeToNotifications: webSocketService.subscribeToNotifications.bind(webSocketService),
    send: webSocketService.send.bind(webSocketService)
  };
};

export default webSocketService;
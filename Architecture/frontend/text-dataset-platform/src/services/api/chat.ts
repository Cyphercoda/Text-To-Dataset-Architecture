/**
 * Chat API Service
 * API calls for AI chat assistant functionality
 */

import { apiClient } from './client';
import { ChatSession, ChatMessage, AttachmentFile } from '../../types';

export interface CreateSessionRequest {
  name?: string;
  documentContext?: string[];
  initialMessage?: string;
}

export interface SendMessageRequest {
  message: string;
  attachments?: AttachmentFile[];
  context?: Record<string, any>;
}

export interface ChatQuery {
  page?: number;
  limit?: number;
  activeOnly?: boolean;
  messageType?: 'user' | 'assistant';
}

export class ChatAPI {
  // Create new chat session
  async createSession(request: CreateSessionRequest = {}): Promise<ChatSession> {
    return apiClient.post('/chat/sessions', request);
  }

  // Get user's chat sessions
  async getSessions(params: ChatQuery = {}): Promise<ChatSession[]> {
    return apiClient.get('/chat/sessions', { params });
  }

  // Get specific chat session
  async getSession(sessionId: string): Promise<ChatSession> {
    return apiClient.get(`/chat/sessions/${sessionId}`);
  }

  // Update chat session
  async updateSession(sessionId: string, updates: {
    name?: string;
    archived?: boolean;
  }): Promise<ChatSession> {
    return apiClient.put(`/chat/sessions/${sessionId}`, updates);
  }

  // Delete chat session
  async deleteSession(sessionId: string): Promise<void> {
    return apiClient.delete(`/chat/sessions/${sessionId}`);
  }

  // Send message in chat session
  async sendMessage(
    sessionId: string, 
    message: string, 
    attachments?: AttachmentFile[]
  ): Promise<ChatMessage> {
    const formData = new FormData();
    formData.append('message', message);

    // Add attachments if any
    if (attachments && attachments.length > 0) {
      attachments.forEach((attachment, index) => {
        formData.append(`attachments[${index}]`, attachment.file);
      });
    }

    return apiClient.uploadFile(`/chat/sessions/${sessionId}/messages`, formData);
  }

  // Get chat messages
  async getMessages(sessionId: string, params: ChatQuery = {}): Promise<ChatMessage[]> {
    return apiClient.get(`/chat/sessions/${sessionId}/messages`, { params });
  }

  // Delete a message
  async deleteMessage(sessionId: string, messageId: string): Promise<void> {
    return apiClient.delete(`/chat/sessions/${sessionId}/messages/${messageId}`);
  }

  // Export chat conversation
  async exportChat(
    sessionId: string, 
    format: 'json' | 'txt' | 'pdf' = 'json'
  ): Promise<{ downloadUrl: string; expiresAt: string }> {
    return apiClient.post(`/chat/sessions/${sessionId}/export`, { format });
  }

  // Search chat messages
  async searchMessages(params: {
    query: string;
    sessionId?: string;
    limit?: number;
    dateRange?: { start: string; end: string };
  }): Promise<{
    messages: ChatMessage[];
    totalCount: number;
    sessions: ChatSession[];
  }> {
    return apiClient.get('/chat/search', { params });
  }

  // Get chat analytics
  async getChatAnalytics(params: {
    period?: string;
    sessionId?: string;
  } = {}): Promise<{
    totalSessions: number;
    totalMessages: number;
    averageMessagesPerSession: number;
    averageResponseTime: number;
    popularTopics: Array<{ topic: string; count: number }>;
    timeSeriesData: Array<{
      date: string;
      sessions: number;
      messages: number;
    }>;
  }> {
    return apiClient.get('/analytics/chat', { params });
  }

  // Get suggested prompts
  async getSuggestedPrompts(context?: {
    documentTypes?: string[];
    recentActivity?: string[];
  }): Promise<Array<{
    prompt: string;
    category: string;
    description: string;
  }>> {
    return apiClient.post('/chat/suggested-prompts', context);
  }

  // Rate a chat response
  async rateResponse(
    sessionId: string, 
    messageId: string, 
    rating: 'positive' | 'negative',
    feedback?: string
  ): Promise<void> {
    return apiClient.post(`/chat/sessions/${sessionId}/messages/${messageId}/rate`, {
      rating,
      feedback,
    });
  }

  // Get chat templates
  async getChatTemplates(): Promise<Array<{
    id: string;
    name: string;
    description: string;
    prompt: string;
    category: string;
    useCount: number;
  }>> {
    return apiClient.get('/chat/templates');
  }

  // Save chat template
  async saveChatTemplate(template: {
    name: string;
    description: string;
    prompt: string;
    category: string;
  }): Promise<{ id: string }> {
    return apiClient.post('/chat/templates', template);
  }

  // Get conversation insights
  async getConversationInsights(sessionId: string): Promise<{
    topics: string[];
    entities: Array<{ type: string; text: string; confidence: number }>;
    sentiment: { overall: number; breakdown: Record<string, number> };
    keyPoints: string[];
    suggestedActions: string[];
  }> {
    return apiClient.get(`/chat/sessions/${sessionId}/insights`);
  }
}

export const chatAPI = new ChatAPI();
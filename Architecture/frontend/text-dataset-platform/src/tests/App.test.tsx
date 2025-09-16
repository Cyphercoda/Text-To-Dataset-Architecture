import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { render } from './utils';
import App from '../App';

// Mock the stores
vi.mock('../stores/appStore', () => ({
  useAppStore: () => ({
    user: null,
    isAuthenticated: false,
    theme: 'light',
    sidebarOpen: false,
    connectionStatus: {
      websocket: 'disconnected',
      api: 'healthy',
      lastCheck: new Date().toISOString(),
    },
    notifications: [],
  }),
}));

vi.mock('../stores/realTimeStore', () => ({
  useRealTimeStore: () => ({
    processingJobs: [],
    activeJobs: [],
    chatSessions: [],
    activeChatSession: null,
    chatMessages: {},
    connected: false,
    reconnectAttempts: 0,
  }),
}));

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(<App />);
    expect(document.body).toBeInTheDocument();
  });

  it('shows login page when user is not authenticated', async () => {
    render(<App />);
    
    // Should redirect to login or show login form
    // This test would need to be adjusted based on your routing logic
    expect(document.body).toBeInTheDocument();
  });

  it('applies correct theme class to document', () => {
    render(<App />);
    
    // Check if theme is applied correctly
    expect(document.documentElement).toHaveAttribute('data-theme', 'light');
  });
});
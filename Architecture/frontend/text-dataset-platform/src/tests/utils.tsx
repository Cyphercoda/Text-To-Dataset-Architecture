import React from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import type { User, ProcessingJob, ChatSession, Document } from '../types';

// Create a custom render function that includes providers
const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

const customRender = (ui: React.ReactElement, options?: Omit<RenderOptions, 'wrapper'>) =>
  render(ui, { wrapper: AllTheProviders, ...options });

// Mock data factories
export const createMockUser = (overrides?: Partial<User>): User => ({
  id: 'user-123',
  email: 'test@example.com',
  name: 'Test User',
  role: 'basic',
  company: 'Test Company',
  createdDate: new Date().toISOString(),
  subscriptionTier: 'basic',
  usageLimits: {
    apiCallsPerDay: 1000,
    uploadVolumePerDay: 1000,
    documentsPerDay: 100,
    concurrentUploads: 5,
  },
  ...overrides,
});

export const createMockDocument = (overrides?: Partial<Document>): Document => ({
  id: 'doc-123',
  userId: 'user-123',
  filename: 'test-document.pdf',
  uploadDate: new Date().toISOString(),
  status: 'completed',
  fileSize: 1024000,
  format: 'pdf',
  processingStage: {
    current: 'completed',
    progress: 100,
  },
  qualityScore: 0.85,
  language: 'en',
  ...overrides,
});

export const createMockProcessingJob = (overrides?: Partial<ProcessingJob>): ProcessingJob => ({
  id: 'job-123',
  userId: 'user-123',
  documentIds: ['doc-123'],
  status: 'completed',
  createdDate: new Date().toISOString(),
  processingConfig: {
    extractEntities: true,
    analyzeSentiment: true,
    classifyDocument: true,
    extractKeyPhrases: true,
    qualityThreshold: 0.8,
    outputFormats: ['json'],
  },
  progressPercentage: 100,
  costEstimate: 2.50,
  ...overrides,
});

export const createMockChatSession = (overrides?: Partial<ChatSession>): ChatSession => ({
  id: 'session-123',
  userId: 'user-123',
  name: 'Test Chat Session',
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  messageCount: 5,
  isActive: true,
  documentContext: ['doc-123'],
  ...overrides,
});

// Mock API responses
export const mockApiResponse = <T>(data: T) => ({
  success: true,
  data,
  message: 'Success',
});

export const mockApiError = (message: string = 'API Error', code: string = 'API_ERROR') => ({
  success: false,
  error: {
    code,
    message,
    details: null,
  },
});

// Mock fetch responses
export const mockFetchResponse = <T>(data: T, status: number = 200) => {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(mockApiResponse(data)),
    text: () => Promise.resolve(JSON.stringify(mockApiResponse(data))),
  } as Response);
};

export const mockFetchError = (message: string, status: number = 500) => {
  return Promise.resolve({
    ok: false,
    status,
    json: () => Promise.resolve(mockApiError(message)),
    text: () => Promise.resolve(JSON.stringify(mockApiError(message))),
  } as Response);
};

// Test helpers for async operations
export const waitForNextTick = () => new Promise(resolve => setTimeout(resolve, 0));

export const waitForTimeout = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Mock File objects for upload testing
export const createMockFile = (
  name: string = 'test-file.txt',
  content: string = 'test content',
  type: string = 'text/plain'
) => {
  const file = new File([content], name, { type });
  return file;
};

// Mock drag and drop events
export const createMockDragEvent = (files: File[]) => {
  const event = {
    preventDefault: vi.fn(),
    stopPropagation: vi.fn(),
    dataTransfer: {
      files,
      items: files.map(file => ({
        kind: 'file',
        type: file.type,
        getAsFile: () => file,
      })),
      types: ['Files'],
    },
  };
  return event as unknown as React.DragEvent<HTMLDivElement>;
};

// Mock WebSocket for testing real-time features
export class MockWebSocketService {
  private listeners: { [event: string]: Function[] } = {};

  connect = vi.fn();
  disconnect = vi.fn();
  send = vi.fn();

  on = vi.fn((event: string, callback: Function) => {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  });

  off = vi.fn((event: string, callback: Function) => {
    if (this.listeners[event]) {
      const index = this.listeners[event].indexOf(callback);
      if (index > -1) {
        this.listeners[event].splice(index, 1);
      }
    }
  });

  emit = (event: string, data: any) => {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  };
}

// Mock chart.js for testing charts
export const mockChartJs = () => {
  vi.mock('chart.js', () => ({
    Chart: vi.fn(() => ({
      destroy: vi.fn(),
      update: vi.fn(),
      render: vi.fn(),
    })),
    registerables: [],
  }));

  vi.mock('react-chartjs-2', () => ({
    Line: vi.fn(({ data, options }) => (
      <div data-testid="line-chart" data-chart-data={JSON.stringify(data)} />
    )),
    Bar: vi.fn(({ data, options }) => (
      <div data-testid="bar-chart" data-chart-data={JSON.stringify(data)} />
    )),
    Pie: vi.fn(({ data, options }) => (
      <div data-testid="pie-chart" data-chart-data={JSON.stringify(data)} />
    )),
    Doughnut: vi.fn(({ data, options }) => (
      <div data-testid="doughnut-chart" data-chart-data={JSON.stringify(data)} />
    )),
  }));
};

// Mock AWS SDK for testing AWS integrations
export const mockAwsSdk = () => {
  vi.mock('aws-sdk', () => ({
    S3: vi.fn(() => ({
      upload: vi.fn(() => ({
        promise: () => Promise.resolve({
          Location: 'https://test-bucket.s3.amazonaws.com/test-file.txt',
          Key: 'test-file.txt',
          Bucket: 'test-bucket',
        }),
      })),
    })),
    CognitoIdentityServiceProvider: vi.fn(() => ({
      initiateAuth: vi.fn(() => ({
        promise: () => Promise.resolve({
          AuthenticationResult: {
            AccessToken: 'mock-access-token',
            RefreshToken: 'mock-refresh-token',
            IdToken: 'mock-id-token',
          },
        }),
      })),
    })),
  }));
};

// Mock intersection observer for testing virtualization
export const mockIntersectionObserver = () => {
  const mockIntersectionObserver = vi.fn();
  mockIntersectionObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  });
  window.IntersectionObserver = mockIntersectionObserver;
};

// Component testing utilities
export const expectElementToBeInDocument = (element: HTMLElement) => {
  expect(element).toBeInTheDocument();
};

export const expectElementToHaveText = (element: HTMLElement, text: string) => {
  expect(element).toHaveTextContent(text);
};

export const expectElementToHaveClass = (element: HTMLElement, className: string) => {
  expect(element).toHaveClass(className);
};

// Re-export testing library utilities
export * from '@testing-library/react';
export { customRender as render };
export { default as userEvent } from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { apiClient } from '../../../services/api/client';
import { mockFetchResponse, mockFetchError } from '../../utils';

// Mock the fetch function
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock the store
vi.mock('../../../stores/appStore', () => ({
  useAppStore: {
    getState: () => ({
      user: {
        accessToken: 'mock-access-token',
      },
      refreshAuthToken: vi.fn(),
      logout: vi.fn(),
    }),
  },
}));

describe('API Client', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    vi.clearAllTimers();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('GET requests', () => {
    it('makes successful GET request', async () => {
      const mockData = { id: 1, name: 'Test' };
      mockFetch.mockResolvedValueOnce(mockFetchResponse(mockData));

      const result = await apiClient.get('/test');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-access-token',
            'X-Request-ID': expect.stringMatching(/^req_\d+_[a-z0-9]+$/),
          }),
        })
      );
      expect(result).toEqual(mockData);
    });

    it('handles GET request with query parameters', async () => {
      const mockData = { results: [] };
      mockFetch.mockResolvedValueOnce(mockFetchResponse(mockData));

      await apiClient.get('/test', {
        params: { page: 1, limit: 10 },
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('page=1&limit=10'),
        expect.any(Object)
      );
    });
  });

  describe('POST requests', () => {
    it('makes successful POST request', async () => {
      const requestData = { name: 'New Item' };
      const responseData = { id: 1, name: 'New Item' };
      mockFetch.mockResolvedValueOnce(mockFetchResponse(responseData));

      const result = await apiClient.post('/test', requestData);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(requestData),
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result).toEqual(responseData);
    });
  });

  describe('Error handling', () => {
    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network Error'));

      await expect(apiClient.get('/test')).rejects.toThrow();
    });

    it('handles 401 errors with token refresh', async () => {
      // Mock 401 error first, then success after retry
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: () => Promise.resolve({ message: 'Unauthorized' }),
        })
        .mockResolvedValueOnce(mockFetchResponse({ success: true }));

      await apiClient.get('/test');

      // Should make two requests - original and retry
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    it('handles API errors', async () => {
      mockFetch.mockResolvedValueOnce(mockFetchError('API Error', 400));

      await expect(apiClient.get('/test')).rejects.toMatchObject({
        message: 'API Error',
        code: 'API_ERROR',
        status: 400,
      });
    });
  });

  describe('File upload', () => {
    it('handles file upload correctly', async () => {
      const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
      const responseData = { url: 'https://example.com/uploaded-file.txt' };
      mockFetch.mockResolvedValueOnce(mockFetchResponse(responseData));

      const result = await apiClient.uploadFile('/upload', file);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/upload'),
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData),
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-access-token',
          }),
        })
      );
      expect(result).toEqual(responseData);
    });

    it('handles upload progress callback', async () => {
      const file = new File(['test content'], 'test.txt');
      const onProgress = vi.fn();
      mockFetch.mockResolvedValueOnce(mockFetchResponse({}));

      await apiClient.uploadFile('/upload', file, onProgress);

      expect(onProgress).toHaveBeenCalled();
    });
  });

  describe('Batch requests', () => {
    it('handles batch requests correctly', async () => {
      const requests = [
        { method: 'GET', url: '/test1' },
        { method: 'POST', url: '/test2', data: { name: 'Test' } },
      ];

      mockFetch
        .mockResolvedValueOnce(mockFetchResponse({ id: 1 }))
        .mockResolvedValueOnce(mockFetchResponse({ id: 2 }));

      const results = await apiClient.batch(requests);

      expect(results).toHaveLength(2);
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Health check', () => {
    it('performs health check', async () => {
      const healthData = { status: 'healthy', timestamp: new Date().toISOString() };
      mockFetch.mockResolvedValueOnce(mockFetchResponse(healthData));

      const result = await apiClient.healthCheck();

      expect(result).toEqual(healthData);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/health'),
        expect.any(Object)
      );
    });
  });
});
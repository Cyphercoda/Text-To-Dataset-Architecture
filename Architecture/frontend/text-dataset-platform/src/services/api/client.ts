/**
 * API Client
 * Centralized HTTP client with authentication and error handling
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';
import { useAppStore } from '../../stores/appStore';

// Types
export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  details?: any;
}

export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
  meta?: {
    page?: number;
    limit?: number;
    total?: number;
    hasMore?: boolean;
  };
}

class ApiClient {
  private axiosInstance: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'https://api.textdataset.com/v1';
    
    this.axiosInstance = axios.create({
      baseURL: this.baseURL,
      timeout: 30000, // 30 seconds
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.axiosInstance.interceptors.request.use(
      (config) => {
        const { user } = useAppStore.getState();
        
        if (user?.accessToken) {
          config.headers.Authorization = `Bearer ${user.accessToken}`;
        }

        // Add request ID for tracking
        config.headers['X-Request-ID'] = this.generateRequestId();

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.axiosInstance.interceptors.response.use(
      (response: AxiosResponse<ApiResponse>) => {
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Handle authentication errors
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            // Try to refresh token
            const { user, refreshAuthToken, logout } = useAppStore.getState();
            
            if (user?.refreshToken) {
              await refreshAuthToken();
              
              // Retry original request with new token
              const { user: updatedUser } = useAppStore.getState();
              if (updatedUser?.accessToken) {
                originalRequest.headers.Authorization = `Bearer ${updatedUser.accessToken}`;
                return this.axiosInstance(originalRequest);
              }
            }
          } catch (refreshError) {
            // Refresh failed, logout user
            const { logout } = useAppStore.getState();
            logout();
            window.location.href = '/auth/login';
            return Promise.reject(refreshError);
          }
        }

        // Handle network errors
        if (!error.response) {
          const networkError: ApiError = {
            message: 'Network error. Please check your connection.',
            code: 'NETWORK_ERROR',
          };
          
          toast.error(networkError.message);
          return Promise.reject(networkError);
        }

        // Handle API errors
        const apiError: ApiError = {
          message: error.response.data?.message || 'An unexpected error occurred',
          code: error.response.data?.code || 'API_ERROR',
          status: error.response.status,
          details: error.response.data?.details,
        };

        // Don't show toast for validation errors (handled by forms)
        if (error.response.status !== 422) {
          toast.error(apiError.message);
        }

        return Promise.reject(apiError);
      }
    );
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Generic request methods
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.get<ApiResponse<T>>(url, config);
    return response.data.data;
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.post<ApiResponse<T>>(url, data, config);
    return response.data.data;
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.put<ApiResponse<T>>(url, data, config);
    return response.data.data;
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.patch<ApiResponse<T>>(url, data, config);
    return response.data.data;
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.delete<ApiResponse<T>>(url, config);
    return response.data.data;
  }

  // File upload method
  async uploadFile<T = any>(
    url: string, 
    file: File | FormData, 
    onProgress?: (progress: number) => void,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const formData = file instanceof FormData ? file : new FormData();
    if (file instanceof File) {
      formData.append('file', file);
    }

    const response = await this.axiosInstance.post<ApiResponse<T>>(url, formData, {
      ...config,
      headers: {
        ...config?.headers,
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = (progressEvent.loaded / progressEvent.total) * 100;
          onProgress(progress);
        }
      },
    });

    return response.data.data;
  }

  // Download file method
  async downloadFile(url: string, filename?: string): Promise<void> {
    const response = await this.axiosInstance.get(url, {
      responseType: 'blob',
    });

    // Create download link
    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  // Batch request method
  async batch<T = any>(requests: Array<{ method: string; url: string; data?: any }>): Promise<T[]> {
    const promises = requests.map(({ method, url, data }) => {
      switch (method.toLowerCase()) {
        case 'get':
          return this.get(url);
        case 'post':
          return this.post(url, data);
        case 'put':
          return this.put(url, data);
        case 'patch':
          return this.patch(url, data);
        case 'delete':
          return this.delete(url);
        default:
          throw new Error(`Unsupported method: ${method}`);
      }
    });

    return Promise.all(promises);
  }

  // Health check method
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.get('/health');
  }

  // Get base URL
  getBaseURL(): string {
    return this.baseURL;
  }

  // Get axios instance for custom requests
  getAxiosInstance(): AxiosInstance {
    return this.axiosInstance;
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Export hooks for React Query integration
export const useApiClient = () => {
  return {
    client: apiClient,
    get: apiClient.get.bind(apiClient),
    post: apiClient.post.bind(apiClient),
    put: apiClient.put.bind(apiClient),
    patch: apiClient.patch.bind(apiClient),
    delete: apiClient.delete.bind(apiClient),
    uploadFile: apiClient.uploadFile.bind(apiClient),
    downloadFile: apiClient.downloadFile.bind(apiClient),
    batch: apiClient.batch.bind(apiClient),
  };
};

export default apiClient;
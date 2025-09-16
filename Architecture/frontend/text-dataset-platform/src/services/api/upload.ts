/**
 * Upload API Service
 * API calls for document upload and processing
 */

import { apiClient } from './client';
import { ProcessingJob, ProcessingConfig } from '../../types';

export interface UploadDocumentsRequest {
  files: Array<{
    name: string;
    s3Key?: string;
    size: number;
    type: string;
  }>;
  config: ProcessingConfig;
}

export interface UploadResponse {
  uploadId: string;
  jobs: ProcessingJob[];
  estimatedCompletion: string;
  totalFiles: number;
}

export interface BatchUploadRequest {
  files: File[];
  folderStructure?: Record<string, any>;
  processingConfig: ProcessingConfig;
}

export class UploadAPI {
  // Upload documents for processing
  async uploadDocuments(request: UploadDocumentsRequest): Promise<UploadResponse> {
    return apiClient.post('/documents/upload', request);
  }

  // Batch upload with folder structure
  async batchUpload(request: BatchUploadRequest): Promise<UploadResponse> {
    const formData = new FormData();
    
    // Add files to form data
    request.files.forEach((file, index) => {
      formData.append(`files[${index}]`, file);
    });

    // Add metadata
    formData.append('folderStructure', JSON.stringify(request.folderStructure || {}));
    formData.append('processingConfig', JSON.stringify(request.processingConfig));

    return apiClient.uploadFile('/documents/batch-upload', formData);
  }

  // Get upload history
  async getUploadHistory(params: {
    page?: number;
    limit?: number;
    status?: string;
    dateRange?: { start: string; end: string };
  } = {}): Promise<{
    uploads: Array<{
      id: string;
      filename: string;
      status: string;
      createdAt: string;
      size: number;
      jobId?: string;
    }>;
    pagination: {
      page: number;
      limit: number;
      total: number;
      hasMore: boolean;
    };
  }> {
    return apiClient.get('/documents/upload-history', { params });
  }

  // Get upload status
  async getUploadStatus(uploadId: string): Promise<{
    status: string;
    progress: number;
    completedFiles: number;
    totalFiles: number;
    errors?: string[];
  }> {
    return apiClient.get(`/documents/upload-status/${uploadId}`);
  }

  // Cancel upload
  async cancelUpload(uploadId: string): Promise<void> {
    return apiClient.delete(`/documents/upload/${uploadId}`);
  }

  // Get supported file formats
  async getSupportedFormats(): Promise<{
    formats: string[];
    maxSize: number;
    maxFiles: number;
  }> {
    return apiClient.get('/documents/supported-formats');
  }

  // Validate files before upload
  async validateFiles(files: File[]): Promise<{
    valid: boolean;
    errors: Array<{
      file: string;
      error: string;
    }>;
    warnings: Array<{
      file: string;
      warning: string;
    }>;
  }> {
    const formData = new FormData();
    files.forEach((file, index) => {
      formData.append(`files[${index}]`, file);
    });

    return apiClient.post('/documents/validate', formData);
  }

  // Get processing configuration templates
  async getProcessingTemplates(): Promise<Array<{
    id: string;
    name: string;
    description: string;
    config: ProcessingConfig;
    isDefault: boolean;
  }>> {
    return apiClient.get('/processing/templates');
  }

  // Save processing configuration as template
  async saveProcessingTemplate(template: {
    name: string;
    description: string;
    config: ProcessingConfig;
  }): Promise<{ id: string }> {
    return apiClient.post('/processing/templates', template);
  }

  // Get upload analytics
  async getUploadAnalytics(params: {
    period?: string;
    granularity?: 'daily' | 'weekly' | 'monthly';
  } = {}): Promise<{
    totalUploads: number;
    successRate: number;
    averageFileSize: number;
    popularFormats: Array<{ format: string; count: number }>;
    timeSeriesData: Array<{
      date: string;
      uploads: number;
      size: number;
    }>;
  }> {
    return apiClient.get('/analytics/uploads', { params });
  }
}

export const uploadAPI = new UploadAPI();
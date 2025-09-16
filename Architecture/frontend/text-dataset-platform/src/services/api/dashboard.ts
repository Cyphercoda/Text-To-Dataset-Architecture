/**
 * Dashboard API Service
 * API calls for dashboard data and metrics
 */

import { apiClient } from './client';
import { DashboardMetrics, ProcessingJob, Document, SystemMetrics } from '../../types';

export interface DashboardQuery {
  period?: string;
  granularity?: 'hourly' | 'daily' | 'weekly' | 'monthly';
  filters?: Record<string, any>;
}

export interface RecentDocumentsQuery {
  limit?: number;
  status?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export class DashboardAPI {
  // Get dashboard overview data
  async getDashboard(params: DashboardQuery = {}): Promise<DashboardMetrics> {
    return apiClient.get('/analytics/dashboard', { params });
  }

  // Get recent documents
  async getRecentDocuments(params: RecentDocumentsQuery = {}): Promise<Document[]> {
    return apiClient.get('/documents/list', {
      params: {
        limit: 10,
        sortBy: 'createdAt',
        sortOrder: 'desc',
        ...params,
      },
    });
  }

  // Get processing jobs
  async getProcessingJobs(params: { 
    status?: string; 
    limit?: number; 
    page?: number;
  } = {}): Promise<ProcessingJob[]> {
    return apiClient.get('/processing/jobs', { params });
  }

  // Get system metrics
  async getSystemMetrics(): Promise<SystemMetrics> {
    return apiClient.get('/system/metrics');
  }

  // Get user activity
  async getUserActivity(params: { 
    period?: string;
    limit?: number;
  } = {}): Promise<any[]> {
    return apiClient.get('/users/recent-activity', { params });
  }

  // Get quick stats
  async getQuickStats(): Promise<{
    totalDocuments: number;
    totalDatasets: number;
    processingJobs: number;
    storageUsed: number;
  }> {
    return apiClient.get('/analytics/quick-stats');
  }

  // Refresh dashboard data
  async refreshDashboard(): Promise<void> {
    return apiClient.post('/analytics/refresh');
  }
}

export const dashboardAPI = new DashboardAPI();
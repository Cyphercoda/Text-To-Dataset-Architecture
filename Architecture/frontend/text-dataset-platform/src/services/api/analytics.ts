/**
 * Analytics API Service
 * API calls for analytics and reporting data
 */

import { apiClient } from './client';

export interface AnalyticsQuery {
  startDate?: string;
  endDate?: string;
  granularity?: 'hourly' | 'daily' | 'weekly' | 'monthly';
  filters?: Record<string, any>;
}

export interface TimeSeriesData {
  date: string;
  value: number;
  metadata?: Record<string, any>;
}

export interface AnalyticsDashboard {
  kpis: {
    documents_processed: number;
    documents_processed_change?: number;
    projects_count: number;
    projects_change?: number;
    accuracy_avg: number;
    accuracy_change?: number;
    cost_saved: number;
    cost_saved_change?: number;
    avg_processing_time: number;
    processing_time_change?: number;
  };
  processing_volume: TimeSeriesData[];
  entity_distribution: Array<{ type: string; count: number; percentage: number }>;
  export_activity: Array<{ format: string; count: number }>;
  system_performance: {
    cpu_usage: number;
    memory_usage: number;
    active_connections: number;
    queue_depth: number;
  };
}

export class AnalyticsAPI {
  // Get comprehensive dashboard data
  async getDashboard(params: AnalyticsQuery = {}): Promise<AnalyticsDashboard> {
    return apiClient.get('/analytics/dashboard', { params });
  }

  // Get processing volume trends
  async getProcessingVolume(params: AnalyticsQuery = {}): Promise<{
    time_series: TimeSeriesData[];
    total_volume: number;
    growth_rate: number;
    trends: Array<{ metric: string; trend: 'up' | 'down' | 'stable'; change: number }>;
  }> {
    return apiClient.get('/analytics/processing-volume', { params });
  }

  // Get entity distribution analytics
  async getEntityDistribution(params: AnalyticsQuery = {}): Promise<{
    entity_types: Array<{
      type: string;
      count: number;
      percentage: number;
      confidence_avg: number;
    }>;
    total_entities: number;
    trends: Array<{ type: string; change: number }>;
  }> {
    return apiClient.get('/analytics/entity-distribution', { params });
  }

  // Get export activity metrics
  async getExportActivity(params: AnalyticsQuery = {}): Promise<{
    export_counts: TimeSeriesData[];
    formats_breakdown: Array<{ format: string; count: number; percentage: number }>;
    total_exports: number;
    export_change: number;
    popular_formats: Array<{ format: string; count: number }>;
  }> {
    return apiClient.get('/analytics/export-activity', { params });
  }

  // Get cost tracking data
  async getCostTracking(params: AnalyticsQuery = {}): Promise<{
    daily_costs: TimeSeriesData[];
    total_spend: number;
    savings_calculated: number;
    cost_projections: Array<{ period: string; projected_cost: number }>;
    optimization_suggestions: Array<{
      category: string;
      suggestion: string;
      potential_savings: number;
    }>;
    projected_monthly: number;
  }> {
    return apiClient.get('/analytics/cost-tracking', { params });
  }

  // Get quality metrics trends
  async getQualityMetrics(params: AnalyticsQuery = {}): Promise<{
    quality_trends: TimeSeriesData[];
    average_scores: Record<string, number>;
    improvement_areas: Array<{
      area: string;
      current_score: number;
      target_score: number;
      suggestions: string[];
    }>;
    quality_distribution: Array<{ score_range: string; count: number }>;
  }> {
    return apiClient.get('/analytics/quality-metrics', { params });
  }

  // Get user engagement metrics
  async getUserEngagement(params: AnalyticsQuery = {}): Promise<{
    active_users: number;
    feature_usage: Array<{ feature: string; usage_count: number; users_count: number }>;
    session_duration: {
      average: number;
      median: number;
      breakdown: Array<{ duration_range: string; count: number }>;
    };
    retention_rates: Array<{ period: string; rate: number }>;
  }> {
    return apiClient.get('/analytics/user-engagement', { params });
  }

  // Get performance analytics
  async getPerformanceAnalytics(params: AnalyticsQuery = {}): Promise<{
    response_times: {
      api: TimeSeriesData[];
      processing: TimeSeriesData[];
      average_api_response: number;
      average_processing_time: number;
    };
    error_rates: TimeSeriesData[];
    throughput: TimeSeriesData[];
    resource_utilization: {
      cpu: TimeSeriesData[];
      memory: TimeSeriesData[];
      storage: TimeSeriesData[];
    };
  }> {
    return apiClient.get('/analytics/performance', { params });
  }

  // Get comparative analytics
  async getComparativeAnalytics(params: {
    metrics: string[];
    compareWith: 'previous_period' | 'same_period_last_year';
    period: string;
  }): Promise<{
    comparisons: Array<{
      metric: string;
      current_value: number;
      comparison_value: number;
      change_percentage: number;
      trend: 'up' | 'down' | 'stable';
    }>;
  }> {
    return apiClient.get('/analytics/compare', { params });
  }

  // Export analytics data
  async exportAnalytics(params: {
    type: 'dashboard' | 'processing' | 'entity' | 'export' | 'cost';
    format: 'csv' | 'excel' | 'json' | 'pdf';
    dateRange: { start: string; end: string };
    includeCharts?: boolean;
  }): Promise<{ downloadUrl: string; expiresAt: string }> {
    return apiClient.post('/analytics/export', params);
  }

  // Get real-time metrics
  async getRealTimeMetrics(): Promise<{
    current_processing: number;
    queue_depth: number;
    active_users: number;
    system_health: 'healthy' | 'warning' | 'critical';
    recent_completions: number;
    average_response_time: number;
    error_rate: number;
  }> {
    return apiClient.get('/analytics/real-time');
  }

  // Get custom analytics
  async getCustomAnalytics(query: {
    metrics: string[];
    dimensions: string[];
    filters: Array<{ field: string; operator: string; value: any }>;
    dateRange: { start: string; end: string };
    granularity: 'hourly' | 'daily' | 'weekly' | 'monthly';
  }): Promise<{
    data: Array<Record<string, any>>;
    metadata: {
      total_records: number;
      query_time: number;
      cached: boolean;
    };
  }> {
    return apiClient.post('/analytics/custom', query);
  }

  // Get analytics alerts
  async getAnalyticsAlerts(): Promise<Array<{
    id: string;
    type: 'threshold' | 'anomaly' | 'trend';
    metric: string;
    condition: string;
    current_value: number;
    threshold_value: number;
    severity: 'low' | 'medium' | 'high' | 'critical';
    timestamp: string;
    resolved: boolean;
  }>> {
    return apiClient.get('/analytics/alerts');
  }

  // Create analytics alert
  async createAlert(alert: {
    name: string;
    metric: string;
    condition: 'greater_than' | 'less_than' | 'equals' | 'anomaly';
    threshold: number;
    notification_channels: string[];
  }): Promise<{ id: string }> {
    return apiClient.post('/analytics/alerts', alert);
  }

  // Get analytics insights
  async getInsights(params: AnalyticsQuery = {}): Promise<Array<{
    type: 'trend' | 'anomaly' | 'opportunity' | 'risk';
    title: string;
    description: string;
    impact: 'low' | 'medium' | 'high';
    confidence: number;
    recommendations: string[];
    data_points: any[];
  }>> {
    return apiClient.get('/analytics/insights', { params });
  }
}

export const analyticsAPI = new AnalyticsAPI();
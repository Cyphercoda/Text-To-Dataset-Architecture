/**
 * Dashboard Page Component
 * Main dashboard with analytics, quick actions, and real-time updates
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';

// Components
import { OptimizedCard } from '../../components/optimization/PerformanceOptimized';
import VirtualizedTable from '../../components/optimization/VirtualizedTable';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import MetricCard from '../../components/dashboard/MetricCard';
import QuickActions from '../../components/dashboard/QuickActions';
import ProcessingQueue from '../../components/dashboard/ProcessingQueue';
import RecentActivity from '../../components/dashboard/RecentActivity';
import SystemStatus from '../../components/dashboard/SystemStatus';

// Hooks and Services
import { useProcessingStore } from '../../stores/realTimeStore';
import { useWebSocket } from '../../services/webSocketService';
import { dashboardAPI } from '../../services/api/dashboard';

// Types
import { ProcessingJob, DashboardMetrics } from '../../types';

// Icons
import {
  DocumentTextIcon,
  ChartBarIcon,
  CpuChipIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d');
  const { jobs, isConnected } = useProcessingStore();
  const { subscribeToNotifications } = useWebSocket();

  // Fetch dashboard data
  const {
    data: dashboardData,
    isLoading: isDashboardLoading,
    error: dashboardError,
    refetch: refetchDashboard,
  } = useQuery({
    queryKey: ['dashboard', selectedTimeRange],
    queryFn: () => dashboardAPI.getDashboard({ period: selectedTimeRange }),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Fetch recent documents
  const {
    data: recentDocuments,
    isLoading: isDocumentsLoading,
  } = useQuery({
    queryKey: ['documents', 'recent'],
    queryFn: () => dashboardAPI.getRecentDocuments({ limit: 10 }),
    refetchInterval: 60000, // Refetch every minute
  });

  // Subscribe to real-time notifications
  useEffect(() => {
    const unsubscribe = subscribeToNotifications((notification) => {
      toast(notification.message, {
        icon: notification.type === 'success' ? '✅' : 
              notification.type === 'error' ? '❌' : 
              notification.type === 'warning' ? '⚠️' : 'ℹ️',
      });
    });

    return unsubscribe;
  }, [subscribeToNotifications]);

  // Calculate dashboard metrics
  const metrics = useMemo(() => {
    if (!dashboardData) return null;

    const activeJobs = jobs.filter(job => 
      ['pending', 'processing'].includes(job.status)
    ).length;

    const completedJobs = jobs.filter(job => 
      job.status === 'completed'
    ).length;

    const failedJobs = jobs.filter(job => 
      job.status === 'failed'
    ).length;

    return {
      totalDocuments: {
        value: dashboardData.kpis.documents_processed,
        change: dashboardData.kpis.documents_processed_change || 0,
        icon: DocumentTextIcon,
        color: 'blue',
      },
      activeJobs: {
        value: activeJobs,
        change: 0,
        icon: CpuChipIcon,
        color: 'yellow',
      },
      completedJobs: {
        value: completedJobs,
        change: 0,
        icon: CheckCircleIcon,
        color: 'green',
      },
      averageTime: {
        value: `${Math.round(dashboardData.kpis.average_processing_time || 0)}s`,
        change: dashboardData.kpis.processing_time_change || 0,
        icon: ClockIcon,
        color: 'purple',
      },
      successRate: {
        value: `${Math.round(dashboardData.kpis.success_rate || 0)}%`,
        change: dashboardData.kpis.success_rate_change || 0,
        icon: ChartBarIcon,
        color: 'green',
      },
      costSaved: {
        value: `$${dashboardData.kpis.cost_saved || 0}`,
        change: dashboardData.kpis.cost_saved_change || 0,
        icon: ExclamationTriangleIcon,
        color: 'green',
      },
    };
  }, [dashboardData, jobs]);

  // Table columns for recent documents
  const documentColumns = useMemo(() => [
    {
      key: 'name' as keyof any,
      header: 'Document',
      width: 250,
      render: (value: string, item: any) => (
        <div className="flex items-center">
          <DocumentTextIcon className="h-5 w-5 text-gray-400 mr-2" />
          <span className="font-medium truncate">{value}</span>
        </div>
      ),
    },
    {
      key: 'status' as keyof any,
      header: 'Status',
      width: 120,
      render: (value: string) => (
        <span
          className={`px-2 py-1 text-xs rounded-full ${
            value === 'completed'
              ? 'bg-green-100 text-green-800'
              : value === 'processing'
              ? 'bg-blue-100 text-blue-800'
              : value === 'failed'
              ? 'bg-red-100 text-red-800'
              : 'bg-gray-100 text-gray-800'
          }`}
        >
          {value}
        </span>
      ),
    },
    {
      key: 'createdAt' as keyof any,
      header: 'Created',
      width: 150,
      render: (value: string) => new Date(value).toLocaleDateString(),
    },
    {
      key: 'size' as keyof any,
      header: 'Size',
      width: 100,
      render: (value: number) => `${Math.round(value / 1024)} KB`,
    },
  ], []);

  // Quick action handlers
  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'upload':
        navigate('/upload');
        break;
      case 'chat':
        navigate('/chat');
        break;
      case 'analytics':
        navigate('/analytics');
        break;
      case 'settings':
        navigate('/settings');
        break;
      default:
        break;
    }
  };

  // Error state
  if (dashboardError) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Failed to load dashboard
          </h2>
          <p className="text-gray-600 mb-4">
            There was an error loading your dashboard data.
          </p>
          <button
            onClick={() => refetchDashboard()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
              <p className="text-gray-600 mt-1">
                Welcome back! Here's what's happening with your documents.
              </p>
            </div>
            
            {/* Connection Status */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <div
                  className={`w-2 h-2 rounded-full mr-2 ${
                    isConnected ? 'bg-green-500' : 'bg-red-500'
                  }`}
                />
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              
              {/* Time Range Selector */}
              <select
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm"
              >
                <option value="1d">Last 24 hours</option>
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
              </select>
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6 mb-8">
          {isDashboardLoading ? (
            Array.from({ length: 6 }).map((_, i) => (
              <OptimizedCard key={i} title="" loading />
            ))
          ) : (
            metrics && Object.entries(metrics).map(([key, metric]) => (
              <MetricCard
                key={key}
                title={key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                value={metric.value}
                change={metric.change}
                icon={metric.icon}
                color={metric.color as any}
                loading={isDashboardLoading}
              />
            ))
          )}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Quick Actions */}
          <div className="lg:col-span-1">
            <QuickActions onAction={handleQuickAction} />
          </div>

          {/* Processing Queue */}
          <div className="lg:col-span-2">
            <ProcessingQueue jobs={jobs.slice(0, 5)} />
          </div>
        </div>

        {/* Content Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Documents */}
          <OptimizedCard title="Recent Documents" className="h-96">
            {isDocumentsLoading ? (
              <LoadingSpinner />
            ) : (
              <VirtualizedTable
                data={recentDocuments || []}
                columns={documentColumns}
                height={300}
                onRowClick={(document) => navigate(`/documents/${document.id}`)}
                className="border-0"
              />
            )}
          </OptimizedCard>

          {/* System Status & Recent Activity */}
          <div className="space-y-6">
            <SystemStatus />
            <RecentActivity />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
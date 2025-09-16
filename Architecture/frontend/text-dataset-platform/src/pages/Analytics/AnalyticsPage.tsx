/**
 * Analytics Page Component
 * Comprehensive analytics dashboard with charts, metrics, and insights
 */

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Bar, Pie, Doughnut } from 'react-chartjs-2';

// Components
import { OptimizedCard } from '../../components/optimization/PerformanceOptimized';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import MetricCard from '../../components/dashboard/MetricCard';
import DateRangePicker from '../../components/ui/DateRangePicker';
import ExportButton from '../../components/analytics/ExportButton';

// Services
import { analyticsAPI } from '../../services/api/analytics';

// Types
import { AnalyticsData, TimeSeriesData, ChartConfig } from '../../types';

// Icons
import {
  ChartBarIcon,
  DocumentTextIcon,
  CloudArrowDownIcon,
  CurrencyDollarIcon,
  CheckCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface DateRange {
  startDate: Date;
  endDate: Date;
}

const AnalyticsPage: React.FC = () => {
  const [selectedDateRange, setSelectedDateRange] = useState<DateRange>({
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
    endDate: new Date(),
  });

  const [selectedMetric, setSelectedMetric] = useState<string>('processing_volume');

  // Fetch analytics data
  const {
    data: analyticsData,
    isLoading: isAnalyticsLoading,
    error: analyticsError,
    refetch: refetchAnalytics,
  } = useQuery({
    queryKey: ['analytics', 'dashboard', selectedDateRange],
    queryFn: () =>
      analyticsAPI.getDashboard({
        startDate: selectedDateRange.startDate.toISOString(),
        endDate: selectedDateRange.endDate.toISOString(),
        granularity: 'daily',
      }),
    refetchInterval: 60000, // Refetch every minute
  });

  // Fetch processing volume data
  const {
    data: processingVolumeData,
    isLoading: isVolumeLoading,
  } = useQuery({
    queryKey: ['analytics', 'processing-volume', selectedDateRange],
    queryFn: () =>
      analyticsAPI.getProcessingVolume({
        startDate: selectedDateRange.startDate.toISOString(),
        endDate: selectedDateRange.endDate.toISOString(),
        granularity: 'daily',
      }),
  });

  // Fetch entity distribution data
  const {
    data: entityDistributionData,
    isLoading: isEntityLoading,
  } = useQuery({
    queryKey: ['analytics', 'entity-distribution', selectedDateRange],
    queryFn: () =>
      analyticsAPI.getEntityDistribution({
        startDate: selectedDateRange.startDate.toISOString(),
        endDate: selectedDateRange.endDate.toISOString(),
      }),
  });

  // Fetch export activity data
  const {
    data: exportActivityData,
    isLoading: isExportLoading,
  } = useQuery({
    queryKey: ['analytics', 'export-activity', selectedDateRange],
    queryFn: () =>
      analyticsAPI.getExportActivity({
        startDate: selectedDateRange.startDate.toISOString(),
        endDate: selectedDateRange.endDate.toISOString(),
      }),
  });

  // Fetch cost tracking data
  const {
    data: costTrackingData,
    isLoading: isCostLoading,
  } = useQuery({
    queryKey: ['analytics', 'cost-tracking', selectedDateRange],
    queryFn: () =>
      analyticsAPI.getCostTracking({
        startDate: selectedDateRange.startDate.toISOString(),
        endDate: selectedDateRange.endDate.toISOString(),
      }),
  });

  // Calculate key metrics
  const keyMetrics = useMemo(() => {
    if (!analyticsData) return null;

    return {
      documentsProcessed: {
        value: analyticsData.kpis.documents_processed,
        change: analyticsData.kpis.documents_processed_change || 0,
        icon: DocumentTextIcon,
        color: 'blue',
      },
      projectsCount: {
        value: analyticsData.kpis.projects_count,
        change: analyticsData.kpis.projects_change || 0,
        icon: ChartBarIcon,
        color: 'green',
      },
      accuracyAverage: {
        value: `${Math.round(analyticsData.kpis.accuracy_avg || 0)}%`,
        change: analyticsData.kpis.accuracy_change || 0,
        icon: CheckCircleIcon,
        color: 'green',
      },
      costSaved: {
        value: `$${analyticsData.kpis.cost_saved || 0}`,
        change: analyticsData.kpis.cost_saved_change || 0,
        icon: CurrencyDollarIcon,
        color: 'green',
      },
      processingTime: {
        value: `${Math.round(analyticsData.kpis.avg_processing_time || 0)}s`,
        change: analyticsData.kpis.processing_time_change || 0,
        icon: ClockIcon,
        color: 'purple',
      },
      exportsCount: {
        value: exportActivityData?.total_exports || 0,
        change: exportActivityData?.export_change || 0,
        icon: CloudArrowDownIcon,
        color: 'yellow',
      },
    };
  }, [analyticsData, exportActivityData]);

  // Chart configurations
  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Date',
        },
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Count',
        },
      },
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false,
    },
  };

  // Processing volume chart data
  const processingVolumeChartData = useMemo(() => {
    if (!processingVolumeData?.time_series) return null;

    return {
      labels: processingVolumeData.time_series.map((point: any) => 
        new Date(point.date).toLocaleDateString()
      ),
      datasets: [
        {
          label: 'Documents Processed',
          data: processingVolumeData.time_series.map((point: any) => point.count),
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.4,
        },
        {
          label: 'Success Rate',
          data: processingVolumeData.time_series.map((point: any) => 
            Math.round((point.success_count / point.count) * 100)
          ),
          borderColor: 'rgb(16, 185, 129)',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: false,
          yAxisID: 'y1',
        },
      ],
    };
  }, [processingVolumeData]);

  // Entity distribution chart data
  const entityDistributionChartData = useMemo(() => {
    if (!entityDistributionData?.entity_types) return null;

    return {
      labels: entityDistributionData.entity_types.map((entity: any) => entity.type),
      datasets: [
        {
          data: entityDistributionData.entity_types.map((entity: any) => entity.count),
          backgroundColor: [
            '#3B82F6',
            '#10B981',
            '#F59E0B',
            '#EF4444',
            '#8B5CF6',
            '#EC4899',
            '#6B7280',
          ],
          borderWidth: 2,
        },
      ],
    };
  }, [entityDistributionData]);

  // Export activity chart data
  const exportActivityChartData = useMemo(() => {
    if (!exportActivityData?.export_counts) return null;

    return {
      labels: exportActivityData.export_counts.map((point: any) => 
        new Date(point.date).toLocaleDateString()
      ),
      datasets: [
        {
          label: 'Exports',
          data: exportActivityData.export_counts.map((point: any) => point.count),
          backgroundColor: 'rgba(245, 158, 11, 0.8)',
          borderColor: 'rgb(245, 158, 11)',
          borderWidth: 2,
        },
      ],
    };
  }, [exportActivityData]);

  // Loading state
  if (isAnalyticsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // Error state
  if (analyticsError) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <ChartBarIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Failed to load analytics
          </h2>
          <p className="text-gray-600 mb-4">
            There was an error loading your analytics data.
          </p>
          <button
            onClick={() => refetchAnalytics()}
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
              <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
              <p className="text-gray-600 mt-1">
                Comprehensive insights into your document processing and datasets
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <DateRangePicker
                startDate={selectedDateRange.startDate}
                endDate={selectedDateRange.endDate}
                onChange={setSelectedDateRange}
              />
              
              <ExportButton
                data={analyticsData}
                filename={`analytics-${selectedDateRange.startDate.toISOString().split('T')[0]}-${selectedDateRange.endDate.toISOString().split('T')[0]}`}
              />
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6 mb-8">
          {keyMetrics && Object.entries(keyMetrics).map(([key, metric]) => (
            <MetricCard
              key={key}
              title={key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
              value={metric.value}
              change={metric.change}
              icon={metric.icon}
              color={metric.color as any}
              loading={false}
            />
          ))}
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Processing Volume Chart */}
          <OptimizedCard title="Processing Volume Over Time">
            {isVolumeLoading ? (
              <div className="h-64 flex items-center justify-center">
                <LoadingSpinner />
              </div>
            ) : processingVolumeChartData ? (
              <div className="h-64">
                <Line data={processingVolumeChartData} options={chartOptions} />
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                No data available
              </div>
            )}
          </OptimizedCard>

          {/* Entity Distribution Chart */}
          <OptimizedCard title="Entity Type Distribution">
            {isEntityLoading ? (
              <div className="h-64 flex items-center justify-center">
                <LoadingSpinner />
              </div>
            ) : entityDistributionChartData ? (
              <div className="h-64 flex items-center justify-center">
                <Doughnut
                  data={entityDistributionChartData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'right',
                      },
                    },
                  }}
                />
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                No data available
              </div>
            )}
          </OptimizedCard>
        </div>

        {/* Secondary Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Export Activity Chart */}
          <OptimizedCard title="Export Activity">
            {isExportLoading ? (
              <div className="h-64 flex items-center justify-center">
                <LoadingSpinner />
              </div>
            ) : exportActivityChartData ? (
              <div className="h-64">
                <Bar data={exportActivityChartData} options={chartOptions} />
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                No export data available
              </div>
            )}
          </OptimizedCard>

          {/* Cost Tracking */}
          <OptimizedCard title="Cost Analysis">
            {isCostLoading ? (
              <div className="h-64 flex items-center justify-center">
                <LoadingSpinner />
              </div>
            ) : costTrackingData ? (
              <div className="h-64 p-4">
                <div className="grid grid-cols-2 gap-4 h-full">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      ${costTrackingData.total_spend || 0}
                    </div>
                    <div className="text-sm text-gray-600">Total Spend</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      ${costTrackingData.savings_calculated || 0}
                    </div>
                    <div className="text-sm text-gray-600">Money Saved</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      ${(costTrackingData.total_spend || 0) / (analyticsData?.kpis.documents_processed || 1)}
                    </div>
                    <div className="text-sm text-gray-600">Cost per Document</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      ${costTrackingData.projected_monthly || 0}
                    </div>
                    <div className="text-sm text-gray-600">Projected Monthly</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                No cost data available
              </div>
            )}
          </OptimizedCard>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
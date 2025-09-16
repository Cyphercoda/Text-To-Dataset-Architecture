import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  IconButton,
  Button,
} from '@mui/material';
import {
  TrendingUp,
  Description,
  Analytics,
  Dataset,
  Speed,
  AttachMoney,
  CloudUpload,
  Refresh,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from 'recharts';
import { useAppSelector, useAppDispatch } from '../../../store';
import { CHART_COLORS } from '../../../constants';

// Mock data for demonstration
const mockProcessingData = [
  { name: 'Mon', documents: 45, quality: 89 },
  { name: 'Tue', documents: 52, quality: 91 },
  { name: 'Wed', documents: 38, quality: 87 },
  { name: 'Thu', documents: 61, quality: 93 },
  { name: 'Fri', documents: 55, quality: 90 },
  { name: 'Sat', documents: 28, quality: 88 },
  { name: 'Sun', documents: 33, quality: 89 },
];

const mockQualityData = [
  { name: 'Excellent (90-100%)', value: 45, color: CHART_COLORS.QUALITY_EXCELLENT },
  { name: 'Good (75-89%)', value: 32, color: CHART_COLORS.QUALITY_GOOD },
  { name: 'Fair (60-74%)', value: 18, color: CHART_COLORS.QUALITY_FAIR },
  { name: 'Poor (<60%)', value: 5, color: CHART_COLORS.QUALITY_POOR },
];

const mockFormatData = [
  { name: 'JSON', value: 120 },
  { name: 'CSV', value: 85 },
  { name: 'Parquet', value: 45 },
  { name: 'HuggingFace', value: 25 },
];

interface MetricCardProps {
  title: string;
  value: string | number;
  change: string;
  icon: React.ReactNode;
  trend: 'up' | 'down' | 'neutral';
  color?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, icon, trend, color }) => {
  const trendColor = trend === 'up' ? 'success.main' : trend === 'down' ? 'error.main' : 'text.secondary';
  
  return (
    <Card sx={{ height: '100%', position: 'relative', overflow: 'visible' }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box sx={{ color: color || 'primary.main' }}>
            {icon}
          </Box>
          <Chip 
            label={change} 
            size="small" 
            sx={{ 
              color: trendColor,
              backgroundColor: `${trendColor}15`,
              fontWeight: 'bold'
            }} 
          />
        </Box>
        <Typography variant="h4" component="div" fontWeight="bold" mb={1}>
          {value}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {title}
        </Typography>
      </CardContent>
    </Card>
  );
};

const Dashboard: React.FC = () => {
  const { user } = useAppSelector(state => state.auth);
  const [isLoading, setIsLoading] = useState(false);

  // Mock dashboard metrics
  const metrics = {
    totalDocuments: 1247,
    documentsProcessedToday: 23,
    averageQualityScore: 89.5,
    successRate: 96.2,
    totalCostThisMonth: 142.50,
    processingTimeAverage: 12.3,
    storageUsed: 2.8,
    apiCallsUsed: 8542,
  };

  const handleRefresh = async () => {
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" fontWeight="bold">
            Welcome back, {user?.name?.split(' ')[0]}!
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Here's what's happening with your documents today.
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<CloudUpload />}
          onClick={() => {/* Open upload modal */}}
          size="large"
        >
          Upload Documents
        </Button>
      </Box>

      {/* Metrics Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Documents"
            value={metrics.totalDocuments.toLocaleString()}
            change="+12%"
            icon={<Description fontSize="large" />}
            trend="up"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Processed Today"
            value={metrics.documentsProcessedToday}
            change="+8%"
            icon={<Speed fontSize="large" />}
            trend="up"
            color="success.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Avg Quality Score"
            value={`${metrics.averageQualityScore}%`}
            change="+2.3%"
            icon={<Analytics fontSize="large" />}
            trend="up"
            color="info.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Monthly Cost"
            value={`$${metrics.totalCostThisMonth}`}
            change="-5%"
            icon={<AttachMoney fontSize="large" />}
            trend="down"
            color="warning.main"
          />
        </Grid>
      </Grid>

      {/* Charts Row */}
      <Grid container spacing={3} mb={4}>
        {/* Processing Trend Chart */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6" fontWeight="bold">
                Processing Activity
              </Typography>
              <IconButton onClick={handleRefresh} disabled={isLoading}>
                <Refresh />
              </IconButton>
            </Box>
            {isLoading && <LinearProgress sx={{ mb: 2 }} />}
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={mockProcessingData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Line 
                  yAxisId="left" 
                  type="monotone" 
                  dataKey="documents" 
                  stroke={CHART_COLORS.PRIMARY} 
                  strokeWidth={3}
                  name="Documents Processed"
                />
                <Line 
                  yAxisId="right" 
                  type="monotone" 
                  dataKey="quality" 
                  stroke={CHART_COLORS.SUCCESS} 
                  strokeWidth={3}
                  name="Quality Score %"
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Quality Distribution */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" mb={2}>
              Quality Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={mockQualityData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  dataKey="value"
                  label={({ name, value }) => `${value}%`}
                >
                  {mockQualityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Bottom Row */}
      <Grid container spacing={3}>
        {/* Dataset Formats */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" mb={2}>
              Popular Dataset Formats
            </Typography>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={mockFormatData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill={CHART_COLORS.SECONDARY} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" mb={2}>
              Recent Activity
            </Typography>
            <Box>
              {[
                { action: 'Document processed', file: 'contract_2024.pdf', time: '2 minutes ago', status: 'success' },
                { action: 'Dataset generated', file: 'training_data.json', time: '15 minutes ago', status: 'success' },
                { action: 'Processing failed', file: 'corrupted_file.doc', time: '1 hour ago', status: 'error' },
                { action: 'Upload completed', file: 'batch_documents.zip', time: '2 hours ago', status: 'success' },
                { action: 'Analysis completed', file: 'research_papers.pdf', time: '3 hours ago', status: 'success' },
              ].map((activity, index) => (
                <Box key={index} display="flex" alignItems="center" py={1}>
                  <Box
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      backgroundColor: activity.status === 'success' ? 'success.main' : 'error.main',
                      mr: 2,
                    }}
                  />
                  <Box flexGrow={1}>
                    <Typography variant="body2" fontWeight="medium">
                      {activity.action}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {activity.file}
                    </Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {activity.time}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
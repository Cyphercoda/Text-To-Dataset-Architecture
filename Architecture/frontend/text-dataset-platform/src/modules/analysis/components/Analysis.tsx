import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
} from '@mui/material';
import { Analytics as AnalyticsIcon } from '@mui/icons-material';

const Analysis: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" fontWeight="bold" mb={3}>
        Analysis & Visualization
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <Paper sx={{ p: 3, minHeight: 400 }}>
          <Typography variant="h6" gutterBottom>
            Document Analysis Results
          </Typography>
          <Box display="flex" alignItems="center" justifyContent="center" minHeight={300}>
            <Box textAlign="center">
              <AnalyticsIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="body1" color="text.secondary">
                Analysis and visualization components will be implemented here
              </Typography>
            </Box>
          </Box>
        </Paper>

        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          <Card sx={{ flex: 1, minWidth: 250 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Entity Recognition
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Entity visualization will be shown here
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ flex: 1, minWidth: 250 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Sentiment Analysis
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sentiment analysis results will be displayed here
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  );
};

export default Analysis;
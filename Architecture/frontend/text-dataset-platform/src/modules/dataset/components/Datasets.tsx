import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Card,
  CardContent,
} from '@mui/material';
import { Add, Dataset } from '@mui/icons-material';

const Datasets: React.FC = () => {
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Datasets
        </Typography>
        <Button variant="contained" startIcon={<Add />} size="large">
          Create Dataset
        </Button>
      </Box>

      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        <Paper sx={{ p: 3, minHeight: 400, flex: 2, minWidth: 500 }}>
          <Typography variant="h6" gutterBottom>
            Dataset Collection
          </Typography>
          <Box display="flex" alignItems="center" justifyContent="center" minHeight={300}>
            <Box textAlign="center">
              <Dataset sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="body1" color="text.secondary">
                Dataset management and export tools will be implemented here
              </Typography>
            </Box>
          </Box>
        </Paper>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, flex: 1, minWidth: 250 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Export Formats
              </Typography>
              <Typography variant="body2" color="text.secondary">
                JSON, CSV, Parquet, HuggingFace
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quality Metrics
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Dataset quality scoring will be shown here
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  );
};

export default Datasets;
import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Card,
  CardContent,
} from '@mui/material';
import { CloudUpload, Description } from '@mui/icons-material';

const Documents: React.FC = () => {
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Documents
        </Typography>
        <Button variant="contained" startIcon={<CloudUpload />} size="large">
          Upload Documents
        </Button>
      </Box>

      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        <Paper sx={{ p: 3, minHeight: 400, flex: 2, minWidth: 500 }}>
          <Typography variant="h6" gutterBottom>
            Document List
          </Typography>
          <Box display="flex" alignItems="center" justifyContent="center" minHeight={300}>
            <Box textAlign="center">
              <Description sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="body1" color="text.secondary">
                Document management interface will be implemented here
              </Typography>
            </Box>
          </Box>
        </Paper>

        <Card sx={{ flex: 1, minWidth: 250 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Quick Stats
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Document statistics and filters will be shown here
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

export default Documents;
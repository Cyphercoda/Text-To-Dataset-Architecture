import React from 'react';
import {
  Box,
  Typography,
  Paper,
} from '@mui/material';
import { Settings as SettingsIcon } from '@mui/icons-material';

const Settings: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" fontWeight="bold" mb={3}>
        Settings
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3, minHeight: 400 }}>
            <Typography variant="h6" gutterBottom>
              User Settings
            </Typography>
            <Box display="flex" alignItems="center" justifyContent="center" minHeight={300}>
              <Box textAlign="center">
                <SettingsIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="body1" color="text.secondary">
                  User settings and preferences will be implemented here
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Settings;
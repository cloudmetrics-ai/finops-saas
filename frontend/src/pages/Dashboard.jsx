import React, { useState, useEffect } from 'react';
import { Typography, Box, CircularProgress, Alert } from '@mui/material';
import { complianceApi } from '../api/compliance';
import ComplianceOverview from '../components/dashboard/ComplianceOverview';

const Dashboard = () => {
  const [complianceStatus, setComplianceStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchComplianceStatus = async () => {
      try {
        setLoading(true);
        const data = await complianceApi.getComplianceStatus();
        setComplianceStatus(data);
        setError(null);
      } catch (err) {
        setError('Failed to load compliance status. ' + (err.message || ''));
        console.error('Error fetching compliance status:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchComplianceStatus();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Cloud Resource Tagging Dashboard
      </Typography>
      
      {complianceStatus ? (
        <ComplianceOverview complianceStatus={complianceStatus} />
      ) : (
        <Alert severity="info">No compliance data available</Alert>
      )}
    </div>
  );
};

export default Dashboard;
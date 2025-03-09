import React, { useState, useEffect } from 'react';
import { Typography, Box, Button, CircularProgress, Alert } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';

const Resources = () => {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Placeholder for API call to fetch resources
    const fetchResources = async () => {
      try {
        setLoading(true);
        // Simulate API call with timeout
        await new Promise(resolve => setTimeout(resolve, 1000));
        setResources([
          { id: 'res-1', name: 'Web Server', type: 'ec2', provider: 'aws', compliance_status: 'compliant' },
          { id: 'res-2', name: 'Database', type: 'rds', provider: 'aws', compliance_status: 'non_compliant' },
          { id: 'res-3', name: 'Storage', type: 'storage-account', provider: 'azure', compliance_status: 'unknown' }
        ]);
        setError(null);
      } catch (err) {
        setError('Failed to load resources');
        console.error('Error fetching resources:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchResources();
  }, []);

  const handleRefresh = () => {
    setLoading(true);
    // You would call the actual API here
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  };

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
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Cloud Resources
        </Typography>
        <Button 
          variant="contained" 
          color="primary" 
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
        >
          Refresh Resources
        </Button>
      </Box>

      <Box mt={4}>
        {resources.length === 0 ? (
          <Alert severity="info">No resources found.</Alert>
        ) : (
          <pre>{JSON.stringify(resources, null, 2)}</pre>
        )}
      </Box>
    </div>
  );
};

export default Resources;
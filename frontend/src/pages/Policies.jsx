import React, { useState, useEffect } from 'react';
import { Typography, Box, Button, CircularProgress, Alert } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import AddIcon from '@mui/icons-material/Add';

const Policies = () => {
  const navigate = useNavigate();
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Placeholder for API call to fetch policies
    // Replace with actual API call when ready
    const fetchPolicies = async () => {
      try {
        setLoading(true);
        // Simulate API call with timeout
        await new Promise(resolve => setTimeout(resolve, 1000));
        setPolicies([
          { id: 1, name: 'AWS Resources Policy', active: true, required_tags: ['environment', 'owner'] },
          { id: 2, name: 'Azure Resources Policy', active: false, required_tags: ['cost-center', 'project'] }
        ]);
        setError(null);
      } catch (err) {
        setError('Failed to load policies');
        console.error('Error fetching policies:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchPolicies();
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
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Tagging Policies
        </Typography>
        <Button 
          variant="contained" 
          color="primary" 
          startIcon={<AddIcon />}
          onClick={() => navigate('/policies/new')}
        >
          Create New Policy
        </Button>
      </Box>

      <Box mt={4}>
        {policies.length === 0 ? (
          <Alert severity="info">No policies found. Create your first policy.</Alert>
        ) : (
          <pre>{JSON.stringify(policies, null, 2)}</pre>
        )}
      </Box>
    </div>
  );
};

export default Policies;
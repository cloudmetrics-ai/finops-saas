import React from 'react';
import { Card, CardContent, Typography, Box, Grid, Paper } from '@mui/material';

const ComplianceOverview = ({ complianceStatus }) => {
  if (!complianceStatus) {
    return null;
  }

  const { total_resources, compliant, non_compliant, unknown, exempt, compliance_rate } = complianceStatus;

  return (
    <Card>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          Compliance Overview
        </Typography>

        <Grid container spacing={3} sx={{ mt: 1 }}>
          <Grid item xs={12} sm={6} md={4}>
            <Paper elevation={2} sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h3" color="primary">
                {Math.round(compliance_rate)}%
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Overall Compliance Rate
              </Typography>
            </Paper>
          </Grid>
          
          <Grid item xs={12} sm={6} md={8}>
            <Paper elevation={2} sx={{ p: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Resource Status
              </Typography>
              <Box display="flex" justifyContent="space-between" mt={1}>
                <Typography>Total Resources: <strong>{total_resources}</strong></Typography>
                <Typography>Compliant: <strong style={{ color: 'green' }}>{compliant}</strong></Typography>
                <Typography>Non-Compliant: <strong style={{ color: 'red' }}>{non_compliant}</strong></Typography>
                <Typography>Unknown: <strong style={{ color: 'orange' }}>{unknown}</strong></Typography>
                <Typography>Exempt: <strong style={{ color: 'blue' }}>{exempt}</strong></Typography>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default ComplianceOverview;
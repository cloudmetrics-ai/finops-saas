import apiClient from './index';

export const complianceApi = {
  // Scan resources for compliance
  scanResources: async (cloudProvider = null) => {
    const params = cloudProvider ? { cloud_provider: cloudProvider } : {};
    const response = await apiClient.get('/compliance/scan', { params });
    return response.data;
  },
  
  // Evaluate compliance for all resources
  evaluateCompliance: async () => {
    const response = await apiClient.get('/compliance/evaluate');
    return response.data;
  },
  
  // Get overall compliance status
  getComplianceStatus: async () => {
    const response = await apiClient.get('/compliance/status');
    return response.data;
  }
};
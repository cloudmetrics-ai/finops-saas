import apiClient from './index';

export const resourcesApi = {
  // Get all resources with optional filters
  getResources: async (filters = {}) => {
    const response = await apiClient.get('/resources', { params: filters });
    return response.data;
  },
  
  // Get a specific resource by ID
  getResource: async (resourceId) => {
    const response = await apiClient.get(`/resources/${resourceId}`);
    return response.data;
  },
  
  // Get resource statistics
  getResourceStats: async () => {
    const response = await apiClient.get('/resources/stats');
    return response.data;
  },
  
  // Get resource types
  getResourceTypes: async () => {
    const response = await apiClient.get('/resources/types');
    return response.data;
  },
  
  // Get regions
  getRegions: async (cloudProvider) => {
    const params = cloudProvider ? { cloud_provider: cloudProvider } : {};
    const response = await apiClient.get('/resources/regions', { params });
    return response.data;
  }
};
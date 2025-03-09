import { resourcesApi } from './resources';
import { complianceApi } from './compliance';

// Simple function to test API clients
export const testApiConnections = async () => {
  try {
    console.log('Testing compliance status API...');
    const status = await complianceApi.getComplianceStatus();
    console.log('Compliance status:', status);
    
    console.log('Testing resources API...');
    const resources = await resourcesApi.getResources();
    console.log('Resources:', resources);
    
    return { success: true, data: { status, resources } };
  } catch (error) {
    console.error('API test failed:', error);
    return { success: false, error: error.message };
  }
};
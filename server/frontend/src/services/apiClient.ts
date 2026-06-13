/**
 * API Client configuration
 * Re-exports the main configured axios instance for use across the application
 */

import { api } from "./api";

// Export the main API instance as default
export default api;

// Also export as named export for flexibility
export { api as apiClient };

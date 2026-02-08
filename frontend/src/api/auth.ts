/**
 * Authentication API service
 */
import { apiClient } from './client';
import type { LoginRequest, LoginResponse, User, ApiResponse } from '../types';

export const authApi = {
  // Login
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/login/', credentials);
    return response.data;
  },

  // Logout
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout/');
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  },

  // Get current user
  me: async (): Promise<User> => {
    const response = await apiClient.get<ApiResponse<User>>('/auth/me/');
    return response.data.data;
  },

  // Check if user is authenticated
  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('auth_token');
  },

  // Get stored user data
  getUser: (): User | null => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
};

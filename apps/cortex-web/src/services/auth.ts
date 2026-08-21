import { api } from '../lib/api';
import type { components } from '@curos/types';

type LoginRequest = components['schemas']['LoginRequest'];
type TokenResponse = components['schemas']['TokenResponse'];
type RegisterRequest = components['schemas']['RegisterRequest'];
type UserResponse = components['schemas']['UserResponse'];

export const authService = {
  register: async (data: RegisterRequest) => {
    const response = await api.post<UserResponse>('/auth/register', data);
    return response.data;
  },

  login: async (data: LoginRequest) => {
    // API expects application/json based on LoginRequest schema
    const response = await api.post<TokenResponse>('/auth/login', data);
    return response.data;
  },
  
  getMe: async () => {
    const response = await api.get<components['schemas']['UserResponse']>('/auth/me');
    return response.data;
  },
};

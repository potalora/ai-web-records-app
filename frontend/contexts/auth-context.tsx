'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import apiClient, { User, LoginRequest, RegisterRequest, SessionResponse } from '@/lib/api-client';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'health_records_token';
const USER_KEY = 'health_records_user';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Initialize auth state from localStorage
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      const token = localStorage.getItem(TOKEN_KEY);
      const userData = localStorage.getItem(USER_KEY);

      if (token && userData) {
        const parsedUser = JSON.parse(userData);
        apiClient.setToken(token);
        
        // Validate the token with the backend
        try {
          const validation = await apiClient.validateSession();
          if (validation.valid) {
            setUser(parsedUser);
          } else {
            // Token is invalid, clear storage
            clearAuthData();
          }
        } catch (error) {
          console.warn('Session validation failed:', error);
          clearAuthData();
        }
      }
    } catch (error) {
      console.error('Failed to initialize auth:', error);
      clearAuthData();
    } finally {
      setLoading(false);
    }
  };

  const clearAuthData = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    apiClient.setToken(null);
    setUser(null);
  };

  const saveAuthData = (sessionData: SessionResponse) => {
    localStorage.setItem(TOKEN_KEY, sessionData.token);
    localStorage.setItem(USER_KEY, JSON.stringify(sessionData.user));
    apiClient.setToken(sessionData.token);
    setUser(sessionData.user);
  };

  const login = async (credentials: LoginRequest) => {
    try {
      setLoading(true);
      const sessionData = await apiClient.login(credentials);
      saveAuthData(sessionData);
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData: RegisterRequest) => {
    try {
      setLoading(true);
      const sessionData = await apiClient.register(userData);
      saveAuthData(sessionData);
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      setLoading(true);
      await apiClient.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearAuthData();
      setLoading(false);
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
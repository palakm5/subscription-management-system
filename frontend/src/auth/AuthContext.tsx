import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiRequest } from '../api/client';

export interface User {
  id: string;
  email: string;
  role: 'admin' | 'staff' | 'customer';
  is_active: boolean;
  created_at: string;
}

export interface Customer {
  id: string;
  user_id?: string;
  name: string;
  company?: string;
  phone?: string;
  billing_address: {
    line1: string;
    city: string;
    state: string;
    zip: string;
    country: string;
  };
  tax_id?: string;
}

interface AuthContextType {
  user: User | null;
  customer: Customer | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  signup: (data: any) => Promise<User>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  isAdmin: boolean;
  isStaff: boolean;
  isCustomer: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('brightloop_token'));
  const [loading, setLoading] = useState(true);

  const refreshProfile = async () => {
    const savedToken = localStorage.getItem('brightloop_token');
    if (!savedToken) {
      setUser(null);
      setCustomer(null);
      setLoading(false);
      return;
    }
    try {
      const res = await apiRequest('/auth/me');
      setUser(res.user);
      setCustomer(res.customer || null);
    } catch {
      localStorage.removeItem('brightloop_token');
      setToken(null);
      setUser(null);
      setCustomer(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshProfile();
  }, []);

  const login = async (email: string, password: string): Promise<User> => {
    const res = await apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem('brightloop_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    setCustomer(res.customer || null);
    return res.user;
  };

  const signup = async (data: any): Promise<User> => {
    const res = await apiRequest('/auth/signup', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    localStorage.setItem('brightloop_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    setCustomer(res.customer || null);
    return res.user;
  };

  const logout = async () => {
    try {
      await apiRequest('/auth/logout', { method: 'POST' });
    } catch {
      // ignore logout errors
    } finally {
      localStorage.removeItem('brightloop_token');
      setToken(null);
      setUser(null);
      setCustomer(null);
    }
  };

  const isAdmin = user?.role === 'admin';
  const isStaff = user?.role === 'staff' || isAdmin;
  const isCustomer = user?.role === 'customer';

  return (
    <AuthContext.Provider
      value={{
        user,
        customer,
        token,
        loading,
        login,
        signup,
        logout,
        refreshProfile,
        isAdmin,
        isStaff,
        isCustomer,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
};

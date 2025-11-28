import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1])); // Decode JWT payload
        if (payload.exp * 1000 > Date.now()) {
          setUser({ name: payload.user_id, department: payload.department });
          setIsAuthenticated(true);
        } else {
          logout();
        }
      } catch (err) {
        logout();
      }
    }
  }, []);

  const login = async (userId, password) => {
    try {
      const response = await axios.post(`${import.meta.env.VITE_API_URL}/login`, {
        user_id: userId,
        password,
      });
      localStorage.setItem('token', response.data.access_token);
      setUser({ name: userId, department: response.data.user.department });
      setIsAuthenticated(true);
    } catch (err) {
      throw new Error(err.response?.data?.detail || 'Login failed');
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

function Login() {
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const hour = new Date().getHours();
  let greeting = 'Good evening';
  if (hour >= 5 && hour < 12) greeting = 'Good morning';
  else if (hour >= 12 && hour < 17) greeting = 'Good afternoon';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await login(userId, password);
      navigate('/', { replace: true });
    } catch (err) {
      setError('Invalid credentials or server error. Please try again.');
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-blue-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="w-1/2 flex flex-col justify-center p-8">
        <img src="/logo.png" alt="IFSCA Company Logo" className="mx-auto mb-6 w-32 h-32 sm:w-40 sm:h-40 md:w-48 md:h-48 lg:w-56 lg:h-56" />
        <div className="card max-w-md mx-auto p-8">
          <h1 className="text-3xl font-urbanist font-semibold text-mainText dark:text-white text-center mb-2">
            IFSCA IntelliChat
          </h1>
          <p className="text-primary-gray text-center mb-6">Enter your credentials to proceed</p>
          {error && <p className="text-error-red text-center mb-4">{error}</p>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <input
                type="text"
                placeholder="User ID"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="w-full p-3 border border-primary-gray rounded-lg focus:ring-primary-blue dark:bg-primary-dark dark:text-white dark:border-gray-600 transition-colors"
                required
              />
            </div>
            <div>
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full p-3 border border-primary-gray rounded-lg focus:ring-primary-blue dark:bg-primary-dark dark:text-white dark:border-gray-600 transition-colors"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-primary-blue text-white p-3 rounded-lg hover:bg-secondary-blue transition-colors disabled:opacity-50"
              disabled={!userId || !password}
            >
              Log In
            </button>
          </form>
          <p className="text-xs text-primary-gray text-center mt-6 animate-fadeIn">
            Developed by Department of Information and Technology 👑 | IFSCA IntelliChat 2025
          </p>
        </div>
      </div>
      <div className="w-1/2 flex items-center justify-center p-8 bg-white/50 dark:bg-gray-800/50">
        <div className="text-center animate-fadeIn">
          <h2 className="text-4xl font-urbanist font-light text-primary-blue dark:text-primary-blue mb-4">
            {greeting}!
          </h2>
          <p className="text-lg text-mainText dark:text-white max-w-md">
            Welcome to IFSCA IntelliChat, your AI assistant for regulations, circulars, and more. Enter your credentials on the left to get started.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
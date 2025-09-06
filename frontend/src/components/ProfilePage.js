import React, { useEffect, useState } from 'react';
import { User, Mail, Calendar, LogOut, Loader } from 'lucide-react';
import { Button } from './ui/button';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ProfilePage = ({ onAuthComplete, onLogout }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    handleAuthCallback();
  }, []);

  const handleAuthCallback = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Check for session_id in URL fragment
      const fragment = window.location.hash.substring(1);
      const params = new URLSearchParams(fragment);
      const sessionId = params.get('session_id');

      if (!sessionId) {
        throw new Error('No session ID found in URL');
      }

      console.log('Processing auth callback with session ID:', sessionId);

      // Authenticate with backend using Emergent session ID
      const response = await axios.post(`${API}/auth/session`, {
        emergent_session_id: sessionId
      });

      if (response.data && response.data.user) {
        setUser(response.data.user);
        
        // Clear URL fragment
        window.location.hash = '';
        
        // Notify parent component of successful auth
        if (onAuthComplete) {
          onAuthComplete(response.data.user, response.data.session_token);
        }
        
        // Redirect to main app after brief delay
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
      } else {
        throw new Error('Invalid auth response');
      }

    } catch (error) {
      console.error('Auth callback error:', error);
      setError(error.message || 'Authentication failed');
      
      // Redirect to home after error
      setTimeout(() => {
        window.location.href = '/';
      }, 3000);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await axios.post(`${API}/auth/logout`);
      if (onLogout) {
        onLogout();
      }
      window.location.href = '/';
    } catch (error) {
      console.error('Logout error:', error);
      // Force logout anyway
      if (onLogout) {
        onLogout();
      }
      window.location.href = '/';
    }
  };

  if (isLoading) {
    return (
      <div className="profile-page">
        <div className="profile-loading">
          <Loader className="loading-spinner" />
          <h2>Completing sign in...</h2>
          <p>Please wait while we set up your account.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="profile-page">
        <div className="profile-error">
          <h2>Authentication Error</h2>
          <p>{error}</p>
          <p>Redirecting to home page...</p>
        </div>
      </div>
    );
  }

  if (user) {
    return (
      <div className="profile-page">
        <div className="profile-success">
          <div className="profile-avatar">
            {user.picture ? (
              <img src={user.picture} alt={user.name} className="avatar-img" />
            ) : (
              <User className="avatar-icon" />
            )}
          </div>
          
          <h2>Welcome, {user.name}!</h2>
          <div className="profile-info">
            <div className="info-item">
              <Mail className="info-icon" />
              <span>{user.email}</span>
            </div>
            <div className="info-item">
              <Calendar className="info-icon" />
              <span>Account created</span>
            </div>
          </div>
          
          <p className="profile-message">
            Authentication successful! Redirecting to your personalized Donna experience...
          </p>
          
          <div className="profile-actions">
            <Button 
              onClick={() => window.location.href = '/'}
              className="continue-button"
            >
              Continue to Donna
            </Button>
            
            <Button 
              onClick={handleLogout}
              variant="outline"
              className="logout-button"
            >
              <LogOut className="button-icon" />
              Sign Out
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default ProfilePage;
import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { User, Mail, Lock } from 'lucide-react';

const AuthModal = ({ open, onClose, onAuthSuccess }) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleEmergentLogin = () => {
    setIsLoading(true);
    
    try {
      // Get current app URL for redirect
      const redirectUrl = window.location.origin + '/profile';
      
      // Redirect to Emergent auth with our redirect URL
      const authUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
      window.location.href = authUrl;
      
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="auth-modal">
        <DialogHeader>
          <DialogTitle className="auth-title">
            <User className="auth-icon" />
            Welcome to Donna
          </DialogTitle>
        </DialogHeader>
        
        <div className="auth-content">
          <div className="auth-description">
            <p>Your personal AI assistant for health, career, and calendar management.</p>
            <p>Sign in to access your personalized data and get started.</p>
          </div>

          <div className="auth-methods">
            <Button
              onClick={handleEmergentLogin}
              disabled={isLoading}
              className="auth-button primary"
            >
              <Mail className="button-icon" />
              {isLoading ? 'Signing in...' : 'Sign in with Email'}
            </Button>
            
            <div className="auth-note">
              <p>Secure authentication powered by Emergent</p>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AuthModal;
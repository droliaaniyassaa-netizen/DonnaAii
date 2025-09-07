import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { User, Mail } from 'lucide-react';

const AuthModal = ({ open, onClose, onAuthSuccess }) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleGoogleAuth = () => {
    setIsLoading(true);
    
    try {
      // Get current app URL for redirect (using query parameter routing)
      const redirectUrl = window.location.origin + '/?page=profile';
      
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
            <p className="auth-main-message">
              Sign in with Google once and your schedule, progress, and goals stay synced. Ready for you to pick up right where you left off.
            </p>
          </div>

          <div className="auth-methods">
            {/* Google Auth - Primary and Only Option */}
            <div className="auth-method-content">
              <Button
                onClick={handleGoogleAuth}
                disabled={isLoading}
                className="auth-button primary"
              >
                <Mail className="button-icon" />
                {isLoading ? 'Signing in...' : 'Continue with Google'}
              </Button>
              <p className="auth-method-note">Quick and secure</p>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AuthModal;
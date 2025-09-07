import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { User, Mail, Lock, Eye, EyeOff } from 'lucide-react';

const AuthModal = ({ open, onClose, onAuthSuccess }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [authMode, setAuthMode] = useState('google'); // 'google' or 'manual'
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  });

  const handleEmergentLogin = () => {
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

  const handleManualSignup = async () => {
    setIsLoading(true);
    
    try {
      console.log('🔍 Starting manual signup...', formData);
      
      // Validate form data
      if (!formData.username || !formData.email || !formData.password) {
        alert('Please fill in all fields.');
        return;
      }
      
      // Call backend register endpoint
      const API = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      console.log('🔍 API URL:', API);
      
      const response = await fetch(`${API}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Important for cookies
        body: JSON.stringify(formData),
      });
      
      console.log('🔍 Response status:', response.status);
      
      const data = await response.json();
      console.log('🔍 Response data:', data);
      
      if (!response.ok) {
        // Handle specific error messages
        throw new Error(data.detail || 'Registration failed');
      }
      
      console.log('✅ Registration successful! Calling onAuthSuccess...');
      
      // Success! Call the auth success handler
      onAuthSuccess(data.user, data.session_token);
      
    } catch (error) {
      console.error('❌ Signup error:', error);
      alert(error.message || 'Signup failed. Please try again.');
    } finally {
      console.log('🔍 Setting loading to false...');
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
              I'd love to remember your plans and progress but without an account I'll forget once this chat ends.
            </p>
            <p className="auth-sub-message">
              Sign in with Google or a quick username and password, it only takes a moment, and I'll keep tracking your health, saving your goals and managing your schedule always ready to pick up where you left off.
            </p>
          </div>

          <div className="auth-methods">
            {/* Auth method selector */}
            <div className="auth-method-selector">
              <Button
                onClick={() => setAuthMode('google')}
                variant={authMode === 'google' ? 'default' : 'outline'}
                className={`method-selector ${authMode === 'google' ? 'active' : ''}`}
              >
                <Mail className="button-icon" />
                Google
              </Button>
              <Button
                onClick={() => setAuthMode('manual')}
                variant={authMode === 'manual' ? 'default' : 'outline'}
                className={`method-selector ${authMode === 'manual' ? 'active' : ''}`}
              >
                <User className="button-icon" />
                Username
              </Button>
            </div>

            {/* Google Auth */}
            {authMode === 'google' && (
              <div className="auth-method-content">
                <Button
                  onClick={handleEmergentLogin}
                  disabled={isLoading}
                  className="auth-button primary"
                >
                  <Mail className="button-icon" />
                  {isLoading ? 'Signing in...' : 'Continue with Google'}
                </Button>
                <p className="auth-method-note">Quick and secure</p>
              </div>
            )}

            {/* Manual Auth */}
            {authMode === 'manual' && (
              <div className="auth-method-content">
                <div className="manual-auth-form">
                  <div className="form-group">
                    <Input
                      type="text"
                      placeholder="Choose a username"
                      value={formData.username}
                      onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
                      className="auth-input"
                    />
                  </div>
                  <div className="form-group">
                    <Input
                      type="email"
                      placeholder="Your email"
                      value={formData.email}
                      onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                      className="auth-input"
                    />
                  </div>
                  <div className="form-group password-group">
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Create a password"
                      value={formData.password}
                      onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                      className="auth-input password-input"
                    />
                    <Button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="password-toggle"
                      variant="ghost"
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </Button>
                  </div>
                  <Button
                    onClick={handleManualSignup}
                    disabled={isLoading || !formData.username || !formData.email || !formData.password}
                    className="auth-button primary"
                  >
                    <User className="button-icon" />
                    {isLoading ? 'Creating account...' : 'Create Account'}
                  </Button>
                </div>
                <p className="auth-method-note">Takes 30 seconds</p>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AuthModal;
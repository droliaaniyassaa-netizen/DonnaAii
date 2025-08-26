import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Textarea } from './components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { Progress } from './components/ui/progress';
import { Calendar, MessageCircle, Target, Heart, Send, Mic, MicOff, Plus, Trash2, Clock, Star, TrendingUp, Settings } from 'lucide-react';
import SettingsModal from './components/SettingsModal';
import TimezoneIndicator from './components/TimezoneIndicator';
import { 
  combineDateTimeToUTC, 
  splitUTCDateTime, 
  formatInUserTimezone, 
  getCurrentInUserTimezone,
  handleDSTTransition 
} from './utils/timezone';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  // Chat state
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isVoiceRecording, setIsVoiceRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Calendar state
  const [events, setEvents] = useState([]);
  const [newEvent, setNewEvent] = useState({ title: '', description: '', date: '', time: '' });
  
  // Career state
  const [careerGoals, setCareerGoals] = useState([]);
  const [newGoal, setNewGoal] = useState({ goal: '', timeframe: '' });
  
  // Health state
  const [healthEntries, setHealthEntries] = useState([]);
  const [healthGoals, setHealthGoals] = useState([]);
  const [healthAnalytics, setHealthAnalytics] = useState({});
  const [newHealthEntry, setNewHealthEntry] = useState({ type: 'meal', description: '', date: '', time: '12:00' });
  const [newHealthGoal, setNewHealthGoal] = useState({ goal_type: 'weight_loss', target: '', current_progress: '' });
  
  // UI state
  const [activeTab, setActiveTab] = useState('chat');
  const [showSettings, setShowSettings] = useState(false);
  
  // Refs
  const messagesEndRef = useRef(null);

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  // Load initial data
  useEffect(() => {
    loadChatHistory();
    loadEvents();
    loadCareerGoals();
    loadHealthEntries();
    loadHealthGoals();
    loadHealthAnalytics();
    
    // Initialize default date/time for new entries
    const now = getCurrentInUserTimezone();
    const { date, time } = splitUTCDateTime(now);
    setNewEvent(prev => ({ ...prev, date, time: time || '10:00' }));
    setNewHealthEntry(prev => ({ ...prev, date, time: time || '12:00' }));
  }, []);

  // Chat functions
  const loadChatHistory = async () => {
    try {
      const response = await axios.get(`${API}/chat/history/default`);
      setMessages(response.data);
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;
    
    setIsLoading(true);
    
    try {
      const response = await axios.post(`${API}/chat`, {
        message: inputMessage,
        session_id: 'default'
      });
      
      setInputMessage('');
      await loadChatHistory(); // Reload to get latest messages
      
      // Refresh other tabs data if context might have changed
      loadEvents();
      loadHealthEntries();
      
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Voice recording (placeholder)
  const toggleVoiceRecording = () => {
    setIsVoiceRecording(!isVoiceRecording);
    // TODO: Implement speech-to-text
  };

  // Calendar functions
  const loadEvents = async () => {
    try {
      const response = await axios.get(`${API}/calendar/events`);
      setEvents(response.data);
    } catch (error) {
      console.error('Error loading events:', error);
    }
  };

  const createEvent = async () => {
    if (!newEvent.title || !newEvent.date || !newEvent.time) return;
    
    try {
      // Convert local date/time to UTC
      const utcDateTime = handleDSTTransition(newEvent.date, newEvent.time);
      if (!utcDateTime) {
        alert('Invalid date/time. Please check your input.');
        return;
      }
      
      const eventData = {
        title: newEvent.title,
        description: newEvent.description,
        datetime_utc: utcDateTime.toISOString(),
        reminder: true
      };
      
      await axios.post(`${API}/calendar/events`, eventData);
      setNewEvent({ title: '', description: '', date: '', time: '' });
      loadEvents();
    } catch (error) {
      console.error('Error creating event:', error);
      alert('Error creating event. Please try again.');
    }
  };

  const deleteEvent = async (eventId) => {
    try {
      await axios.delete(`${API}/calendar/events/${eventId}`);
      loadEvents();
    } catch (error) {
      console.error('Error deleting event:', error);
    }
  };

  // Career functions
  const loadCareerGoals = async () => {
    try {
      const response = await axios.get(`${API}/career/goals`);
      setCareerGoals(response.data);
    } catch (error) {
      console.error('Error loading career goals:', error);
    }
  };

  const createCareerGoal = async () => {
    if (!newGoal.goal || !newGoal.timeframe) return;
    
    try {
      await axios.post(`${API}/career/goals`, newGoal);
      setNewGoal({ goal: '', timeframe: '' });
      loadCareerGoals();
    } catch (error) {
      console.error('Error creating career goal:', error);
    }
  };

  const updateGoalProgress = async (goalId, progress) => {
    try {
      await axios.put(`${API}/career/goals/${goalId}/progress`, null, {
        params: { progress }
      });
      loadCareerGoals();
    } catch (error) {
      console.error('Error updating goal progress:', error);
    }
  };

  // Health functions
  const loadHealthEntries = async () => {
    try {
      const response = await axios.get(`${API}/health/entries`);
      setHealthEntries(response.data);
    } catch (error) {
      console.error('Error loading health entries:', error);
    }
  };

  const loadHealthGoals = async () => {
    try {
      const response = await axios.get(`${API}/health/goals`);
      setHealthGoals(response.data);
    } catch (error) {
      console.error('Error loading health goals:', error);
    }
  };

  const loadHealthAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/health/analytics`);
      setHealthAnalytics(response.data);
    } catch (error) {
      console.error('Error loading health analytics:', error);
    }
  };

  const createHealthEntry = async () => {
    if (!newHealthEntry.description || !newHealthEntry.date) return;
    
    try {
      // Convert local date/time to UTC
      const time = newHealthEntry.time || '12:00';
      const utcDateTime = handleDSTTransition(newHealthEntry.date, time);
      if (!utcDateTime) {
        alert('Invalid date/time. Please check your input.');
        return;
      }
      
      const entryData = {
        type: newHealthEntry.type,
        description: newHealthEntry.description,
        value: newHealthEntry.value,
        datetime_utc: utcDateTime.toISOString()
      };
      
      await axios.post(`${API}/health/entries`, entryData);
      setNewHealthEntry({ type: 'meal', description: '', date: '', time: '12:00' });
      loadHealthEntries();
      loadHealthAnalytics();
    } catch (error) {
      console.error('Error creating health entry:', error);
      alert('Error creating health entry. Please try again.');
    }
  };

  const createHealthGoal = async () => {
    if (!newHealthGoal.target || !newHealthGoal.current_progress) return;
    
    try {
      await axios.post(`${API}/health/goals`, newHealthGoal);
      setNewHealthGoal({ goal_type: 'weight_loss', target: '', current_progress: '' });
      loadHealthGoals();
    } catch (error) {
      console.error('Error creating health goal:', error);
    }
  };

  return (
    <div className="app-container">
      <div className="app-header">
        <div className="donna-title">
          <h1>Donna</h1>
          <p>Your intelligent daily companion</p>
        </div>
        <Button 
          variant="ghost" 
          size="sm" 
          className="settings-button"
          onClick={() => setShowSettings(true)}
        >
          <Settings className="settings-icon" />
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="main-tabs">
        <TabsList className="tabs-list">
          <TabsTrigger value="chat" className="tab-trigger">
            <MessageCircle className="tab-icon" />
            Chat
          </TabsTrigger>
          <TabsTrigger value="calendar" className="tab-trigger">
            <Calendar className="tab-icon" />
            Calendar
          </TabsTrigger>
          <TabsTrigger value="career" className="tab-trigger">
            <Target className="tab-icon" />
            Career
          </TabsTrigger>
          <TabsTrigger value="health" className="tab-trigger">
            <Heart className="tab-icon" />
            Health
          </TabsTrigger>
        </TabsList>

        {/* Chat Tab */}
        <TabsContent value="chat" className="chat-container">
          <Card className="chat-card">
            <CardHeader className="chat-header">
              <CardTitle className="chat-title">
                <MessageCircle className="header-icon" />
                Chat with Donna
              </CardTitle>
            </CardHeader>
            <CardContent className="chat-content">
              <div className="messages-container">
                {messages.map((message, index) => (
                  <div key={index} className={`message ${message.is_user ? 'user-message' : 'donna-message'}`}>
                    <div className="message-content">
                      <p>{message.message}</p>
                      <span className="message-time">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="message donna-message">
                    <div className="message-content loading">
                      <p>Donna is thinking...</p>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
              
              <div className="input-container">
                <Textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask Donna anything..."
                  className="chat-input"
                  rows={2}
                />
                <div className="input-actions">
                  <Button
                    onClick={toggleVoiceRecording}
                    variant={isVoiceRecording ? "destructive" : "outline"}
                    size="sm"
                    className="voice-button"
                  >
                    {isVoiceRecording ? <MicOff /> : <Mic />}
                  </Button>
                  <Button 
                    onClick={sendMessage} 
                    disabled={isLoading || !inputMessage.trim()}
                    className="send-button"
                  >
                    <Send className="send-icon" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Calendar Tab */}
        <TabsContent value="calendar" className="calendar-container">
          <TimezoneIndicator className="calendar-timezone" />
          <div className="calendar-grid">
            <Card className="calendar-card">
              <CardHeader>
                <CardTitle className="section-title">
                  <Calendar className="header-icon" />
                  Schedule New Event
                </CardTitle>
              </CardHeader>
              <CardContent className="create-form">
                <Input
                  placeholder="Event title"
                  value={newEvent.title}
                  onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                  className="form-input"
                />
                <Textarea
                  placeholder="Description (optional)"
                  value={newEvent.description}
                  onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                  className="form-input"
                />
                <div className="date-time-row">
                  <Input
                    type="date"
                    value={newEvent.date}
                    onChange={(e) => setNewEvent({ ...newEvent, date: e.target.value })}
                    className="form-input"
                  />
                  <Input
                    type="time"
                    value={newEvent.time}
                    onChange={(e) => setNewEvent({ ...newEvent, time: e.target.value })}
                    className="form-input"
                  />
                </div>
                <Button onClick={createEvent} className="create-button">
                  <Plus className="button-icon" />
                  Create Event
                </Button>
              </CardContent>
            </Card>

            <Card className="events-card">
              <CardHeader>
                <CardTitle className="section-title">
                  <Clock className="header-icon" />
                  Upcoming Events
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="events-list">
                  {events.map((event) => {
                    const { date, time } = splitUTCDateTime(event.datetime_utc);
                    return (
                      <div key={event.id} className="event-item">
                        <div className="event-info">
                          <h4 className="event-title">{event.title}</h4>
                          {event.description && <p className="event-description">{event.description}</p>}
                          <div className="event-datetime">
                            <Badge variant="secondary">{date}</Badge>
                            <Badge variant="outline">{time}</Badge>
                          </div>
                        </div>
                        <Button
                          onClick={() => deleteEvent(event.id)}
                          variant="ghost"
                          size="sm"
                          className="delete-button"
                        >
                          <Trash2 className="delete-icon" />
                        </Button>
                      </div>
                    );
                  })}
                  {events.length === 0 && (
                    <p className="empty-state">No events scheduled. Create your first event above!</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Career Tab */}
        <TabsContent value="career" className="career-container">
          <div className="career-grid">
            <Card className="goal-creation-card">
              <CardHeader>
                <CardTitle className="section-title">
                  <Target className="header-icon" />
                  Set Career Goal
                </CardTitle>
              </CardHeader>
              <CardContent className="create-form">
                <Textarea
                  placeholder="Describe your career goal (e.g., 'Become a manager in 6 months')"
                  value={newGoal.goal}
                  onChange={(e) => setNewGoal({ ...newGoal, goal: e.target.value })}
                  className="form-input"
                />
                <Input
                  placeholder="Timeframe (e.g., '6 months', '1 year')"
                  value={newGoal.timeframe}
                  onChange={(e) => setNewGoal({ ...newGoal, timeframe: e.target.value })}
                  className="form-input"
                />
                <Button onClick={createCareerGoal} className="create-button">
                  <Plus className="button-icon" />
                  Create Goal & Action Plan
                </Button>
              </CardContent>
            </Card>

            <div className="goals-list">
              {careerGoals.map((goal) => (
                <Card key={goal.id} className="goal-card">
                  <CardHeader>
                    <CardTitle className="goal-title">{goal.goal}</CardTitle>
                    <Badge variant="outline" className="timeframe-badge">{goal.timeframe}</Badge>
                  </CardHeader>
                  <CardContent>
                    <div className="progress-section">
                      <div className="progress-header">
                        <span>Progress: {goal.progress}%</span>
                        <Button
                          onClick={() => updateGoalProgress(goal.id, Math.min(100, goal.progress + 10))}
                          size="sm"
                          variant="outline"
                        >
                          +10%
                        </Button>
                      </div>
                      <Progress value={goal.progress} className="progress-bar" />
                    </div>
                    
                    {goal.action_plan.length > 0 && (
                      <div className="action-plan">
                        <h4 className="plan-title">Action Plan</h4>
                        <ul className="plan-list">
                          {goal.action_plan.slice(0, 5).map((step, index) => (
                            <li key={index} className="plan-item">{step}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    <div className="resources">
                      <h4 className="resources-title">Recommended Resources</h4>
                      <div className="resources-list">
                        {goal.resources.map((resource, index) => (
                          <Badge key={index} variant="secondary" className="resource-badge">
                            {resource}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
              {careerGoals.length === 0 && (
                <Card className="empty-card">
                  <CardContent className="empty-content">
                    <Star className="empty-icon" />
                    <p>No career goals yet. Set your first goal to get started with your action plan!</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Health Tab */}
        <TabsContent value="health" className="health-container">
          <div className="health-grid">
            <Card className="health-analytics-card">
              <CardHeader>
                <CardTitle className="section-title">
                  <TrendingUp className="header-icon" />
                  Weekly Analytics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="analytics-grid">
                  <div className="stat-item">
                    <span className="stat-label">Meals This Week</span>
                    <span className="stat-value">{healthAnalytics.meals_this_week || 0}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Water Today</span>
                    <span className="stat-value">{healthAnalytics.water_glasses_today || 0} glasses</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Workouts</span>
                    <span className="stat-value">{healthAnalytics.workouts_this_week || 0}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Sleep Entries</span>
                    <span className="stat-value">{healthAnalytics.average_sleep || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="health-logging-card">
              <CardHeader>
                <CardTitle className="section-title">
                  <Plus className="header-icon" />
                  Log Health Entry
                </CardTitle>
              </CardHeader>
              <CardContent className="create-form">
                <select
                  value={newHealthEntry.type}
                  onChange={(e) => setNewHealthEntry({ ...newHealthEntry, type: e.target.value })}
                  className="form-select"
                >
                  <option value="meal">Meal</option>
                  <option value="hydration">Hydration</option>
                  <option value="exercise">Exercise</option>
                  <option value="sleep">Sleep</option>
                </select>
                <Textarea
                  placeholder="Description (e.g., 'Had salmon and vegetables for lunch')"
                  value={newHealthEntry.description}
                  onChange={(e) => setNewHealthEntry({ ...newHealthEntry, description: e.target.value })}
                  className="form-input"
                />
                <Input
                  type="date"
                  value={newHealthEntry.date}
                  onChange={(e) => setNewHealthEntry({ ...newHealthEntry, date: e.target.value })}
                  className="form-input"
                />
                <Button onClick={createHealthEntry} className="create-button">
                  <Plus className="button-icon" />
                  Log Entry
                </Button>
              </CardContent>
            </Card>

            <Card className="health-goals-card">
              <CardHeader>
                <CardTitle className="section-title">
                  <Target className="header-icon" />
                  Health Goals
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="create-form">
                  <select
                    value={newHealthGoal.goal_type}
                    onChange={(e) => setNewHealthGoal({ ...newHealthGoal, goal_type: e.target.value })}
                    className="form-select"
                  >
                    <option value="weight_loss">Weight Loss</option>
                    <option value="muscle_gain">Muscle Gain</option>
                    <option value="maintain">Maintain</option>
                  </select>
                  <Input
                    placeholder="Target (e.g., 'Lose 10 pounds')"
                    value={newHealthGoal.target}
                    onChange={(e) => setNewHealthGoal({ ...newHealthGoal, target: e.target.value })}
                    className="form-input"
                  />
                  <Input
                    placeholder="Current progress"
                    value={newHealthGoal.current_progress}
                    onChange={(e) => setNewHealthGoal({ ...newHealthGoal, current_progress: e.target.value })}
                    className="form-input"
                  />
                  <Button onClick={createHealthGoal} className="create-button">
                    <Plus className="button-icon" />
                    Set Goal
                  </Button>
                </div>
                
                <div className="goals-display">
                  {healthGoals.map((goal) => (
                    <div key={goal.id} className="health-goal-item">
                      <Badge variant="outline" className="goal-type-badge">
                        {goal.goal_type.replace('_', ' ').toUpperCase()}
                      </Badge>
                      <p className="goal-target">{goal.target}</p>
                      <p className="goal-progress">Current: {goal.current_progress}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="health-entries-card">
              <CardHeader>
                <CardTitle className="section-title">Recent Entries</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="entries-list">
                  {healthEntries.slice(0, 10).map((entry) => (
                    <div key={entry.id} className="entry-item">
                      <Badge variant="secondary" className="entry-type-badge">
                        {entry.type}
                      </Badge>
                      <div className="entry-details">
                        <p className="entry-description">{entry.description}</p>
                        <span className="entry-date">{entry.date}</span>
                      </div>
                    </div>
                  ))}
                  {healthEntries.length === 0 && (
                    <p className="empty-state">No health entries yet. Start logging above!</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default App;
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
import EventCard from './components/EventCard';
import UpcomingToday from './components/UpcomingToday';
import EventCreationButton from './components/EventCreationButton';
import { 
  combineDateTimeToUTC, 
  splitUTCDateTime, 
  formatInUserTimezone, 
  getCurrentInUserTimezone,
  handleDSTTransition,
  parseISO,
  isToday
} from './utils/timezone';
import { 
  extractEventFromMessage, 
  isEventMessage, 
  getDefaultReminders,
  EVENT_CATEGORIES 
} from './utils/eventProcessing';
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
    setNewEvent(prev => ({ ...prev, date, time: time || '10:00', category: 'personal' }));
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
      // Enhanced event detection and creation
      const isEvent = isEventMessage(inputMessage);
      let eventCreated = false;
      
      if (isEvent) {
        const eventData = extractEventFromMessage(inputMessage);
        
        if (eventData && eventData.confidence > 0.3) { // Lower threshold for more inclusive detection
          // Auto-create event from chat
          const success = await createEventFromChat(eventData);
          eventCreated = success;
        }
      }
      
      // Send message to Donna with context about event creation
      const response = await axios.post(`${API}/chat`, {
        message: inputMessage,
        session_id: 'default',
        event_created: eventCreated // Let Donna know if an event was created
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

  // Enhanced create event from chat message
  const createEventFromChat = async (eventData) => {
    try {
      // Use current date/time if not specified, with timezone awareness
      if (!eventData.date) {
        const now = getCurrentInUserTimezone();
        eventData.date = formatInUserTimezone(now, 'yyyy-MM-dd');
      }
      
      // Handle timezone conversion properly
      const utcDateTime = handleDSTTransition(eventData.date, eventData.time);
      if (!utcDateTime) {
        console.warn('Could not create event from chat - invalid date/time');
        return false;
      }
      
      // Create event with default reminders
      const newEvent = {
        title: eventData.title,
        description: eventData.description || eventData.rawMessage,
        category: eventData.category,
        datetime_utc: utcDateTime.toISOString(),
        reminder: true // Always enable reminders for chat-created events
      };
      
      console.log('Creating event from chat:', newEvent);
      
      const response = await axios.post(`${API}/calendar/events`, newEvent);
      
      if (response.status === 200 || response.status === 201) {
        console.log('✅ Event created successfully from chat');
        return true;
      }
      
      return false;
      
    } catch (error) {
      console.error('Error creating event from chat:', error);
      return false;
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
      const allEvents = response.data;
      
      // Filter out past events for upcoming display (hide 2024 dates and past events)
      const now = getCurrentInUserTimezone();
      const upcomingEvents = allEvents.filter(event => {
        try {
          const eventDateTime = parseISO(event.datetime_utc);
          const currentYear = now.getFullYear();
          
          // Hide events from previous years (like 2024) and past events
          if (eventDateTime.getFullYear() < currentYear) {
            return false;
          }
          
          // Show future events (including today's events that haven't passed)
          return eventDateTime >= now || isToday(eventDateTime);
        } catch (error) {
          console.warn('Error parsing event date:', error);
          return false;
        }
      });
      
      setEvents(upcomingEvents);
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
        category: newEvent.category || 'personal', // Default category
        datetime_utc: utcDateTime.toISOString(),
        reminder: true
      };
      
      await axios.post(`${API}/calendar/events`, eventData);
      setNewEvent({ title: '', description: '', date: '', time: '', category: 'personal' });
      loadEvents();
    } catch (error) {
      console.error('Error creating event:', error);
      alert('Error creating event. Please try again.');
    }
  };

  const updateEvent = async (eventId, updateData) => {
    try {
      await axios.put(`${API}/calendar/events/${eventId}`, updateData);
      loadEvents();
    } catch (error) {
      console.error('Error updating event:', error);
      alert('Error updating event. Please try again.');
    }
  };

  // Helper function to check if event is today
  const isEventToday = (event) => {
    try {
      const eventDate = new Date(event.datetime_utc);
      const today = new Date();
      return eventDate.toDateString() === today.toDateString();
    } catch {
      return false;
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
                  onKeyDown={handleKeyPress}
                  placeholder="Ask Donna anything..."
                  className="chat-input"
                  rows={2}
                  disabled={false}
                  style={{ 
                    pointerEvents: 'auto',
                    zIndex: 1000,
                    position: 'relative'
                  }}
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
                    disabled={false}
                    className="send-button"
                    style={{
                      pointerEvents: 'auto',
                      cursor: 'pointer',
                      zIndex: 1001
                    }}
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
          
          {/* Upcoming Today Section */}
          <UpcomingToday events={events} onDelete={deleteEvent} />
          
          <div className="calendar-grid">
            {/* Small Event Creation Button */}
            <EventCreationButton
              newEvent={newEvent}
              setNewEvent={setNewEvent}
              onCreateEvent={createEvent}
            />

            {/* Events List */}
            <div className="events-grid">
              {events
                .filter(event => !isEventToday(event)) // Filter out today's events (shown above)
                .map((event, index) => (
                  <EventCard
                    key={event.id}
                    event={event}
                    className={`event-card-item ${index < 3 ? 'priority-event' : 'standard-event'}`}
                    onDelete={deleteEvent}
                    onUpdate={updateEvent}
                  />
                ))}
              {events.filter(event => !isEventToday(event)).length === 0 && (
                <Card className="empty-card">
                  <CardContent className="empty-content">
                    <Clock className="empty-icon" />
                    <p>No upcoming events. Create your first event above!</p>
                  </CardContent>
                </Card>
              )}
            </div>
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
          <TimezoneIndicator className="health-timezone" />
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
                <div className="date-time-row">
                  <Input
                    type="date"
                    value={newHealthEntry.date}
                    onChange={(e) => setNewHealthEntry({ ...newHealthEntry, date: e.target.value })}
                    className="form-input"
                  />
                  <Input
                    type="time"
                    value={newHealthEntry.time}
                    onChange={(e) => setNewHealthEntry({ ...newHealthEntry, time: e.target.value })}
                    className="form-input"
                  />
                </div>
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
                  {healthEntries.slice(0, 10).map((entry) => {
                    const formattedDate = formatInUserTimezone(entry.datetime_utc, 'MMM d, yyyy');
                    const formattedTime = formatInUserTimezone(entry.datetime_utc, 'h:mm a');
                    return (
                      <div key={entry.id} className="entry-item">
                        <Badge variant="secondary" className="entry-type-badge">
                          {entry.type}
                        </Badge>
                        <div className="entry-details">
                          <p className="entry-description">{entry.description}</p>
                          <span className="entry-date">{formattedDate} at {formattedTime}</span>
                        </div>
                      </div>
                    );
                  })}
                  {healthEntries.length === 0 && (
                    <p className="empty-state">No health entries yet. Start logging above!</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
      
      {/* Settings Modal */}
      <SettingsModal 
        open={showSettings} 
        onClose={() => setShowSettings(false)} 
      />
    </div>
  );
};

export default App;
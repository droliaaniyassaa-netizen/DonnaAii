import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Textarea } from './components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { Progress } from './components/ui/progress';
import { Calendar, MessageCircle, Target, Heart, Send, Mic, MicOff, Plus, Trash2, Clock, Star, TrendingUp, Settings, Sparkles } from 'lucide-react';
import SettingsModal from './components/SettingsModal';
import TimezoneIndicator from './components/TimezoneIndicator';
import EventCard from './components/EventCard';
import UpcomingToday from './components/UpcomingToday';
import MonthlyCalendar from './components/MonthlyCalendar';
import SmartSuggestions from './components/SmartSuggestions';
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
  const [activeResourceCard, setActiveResourceCard] = useState('ai-tools'); // Default active card
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false); // Loading state for plan generation
  
  // Health state
  const [healthEntries, setHealthEntries] = useState([]);
  const [healthGoals, setHealthGoals] = useState([]);
  const [healthAnalytics, setHealthAnalytics] = useState({});
  const [newHealthEntry, setNewHealthEntry] = useState({ type: 'meal', description: '', date: '', time: '12:00' });
  const [newHealthGoal, setNewHealthGoal] = useState({ goal_type: 'weight_loss', target: '', current_progress: '' });
  
  // UI state
  const [activeTab, setActiveTab] = useState('chat');
  const [activeCalendarView, setActiveCalendarView] = useState('upcoming'); // New state for calendar sub-tabs
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
      // Check if message looks like an event for better context to Donna
      let eventCreated = false;
      const isEvent = isEventMessage(inputMessage);
      
      // Note: Event creation is now handled by the backend via chat processing
      // The frontend just detects events to provide better context to Donna
      
      if (isEvent) {
        const eventData = extractEventFromMessage(inputMessage);
        if (eventData && eventData.confidence > 0.3) {
          eventCreated = true; // Mark as event for Donna context
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
    if (!newGoal.goal.trim() || isGeneratingPlan) return;
    
    setIsGeneratingPlan(true);
    
    try {
      const goalData = {
        goal: newGoal.goal,
        timeframe: '6 months' // Default timeframe
      };
      const response = await axios.post(`${API}/career/goals`, goalData);
      console.log('Career goal created:', response.data);
      setNewGoal({ goal: '', timeframe: '' });
      await loadCareerGoals(); // Wait for the goals to load
    } catch (error) {
      console.error('Error creating career goal:', error);
      alert('Error creating career goal. Please try again.');
    } finally {
      setIsGeneratingPlan(false);
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

  const resetCareerGoals = async () => {
    try {
      await axios.delete(`${API}/career/goals`);
      setCareerGoals([]);
      setNewGoal({ goal: '', timeframe: '' });
    } catch (error) {
      console.error('Error resetting career goals:', error);
      alert('Error resetting career goals. Please try again.');
    }
  };

  // Career goal creation with backend integration
  
  // Helper function to parse action plan step and extract title/description
  const parseActionPlanStep = (step) => {
    // Look for markdown bold title at the beginning: **Title**: Description
    const match = step.match(/^\*\*([^*]+)\*\*:?\s*(.*)/s);
    if (match) {
      return {
        title: match[1].trim(),
        description: match[2].trim()
      };
    }
    // If no title found, return the whole step as description
    return {
      title: null,
      description: step.trim()
    };
  };

  // Career Resources Data
  const careerResourcesData = {
    'career_growth': {
      aiTools: [
        { name: 'Otter.ai', description: 'Automated meeting notes and summaries', url: 'https://otter.ai' },
        { name: 'Notion AI', description: 'Organize and summarize projects', url: 'https://www.notion.so/product/ai' },
        { name: 'Grammarly Business', description: 'Professional communication polish', url: 'https://www.grammarly.com/business' },
        { name: 'Crystal Knows', description: 'Personality insights for better workplace interactions', url: 'https://www.crystalknows.com' },
        { name: 'Reclaim.ai', description: 'Smart calendar and focus time optimization', url: 'https://reclaim.ai' }
      ],
      books: [
        'The First 90 Days by Michael D. Watkins',
        'Power: Why Some People Have It and Others Don\'t by Jeffrey Pfeffer',
        'The Art of Strategy by Avinash K. Dixit & Barry Nalebuff', 
        'How to Win Friends and Influence People by Dale Carnegie',
        'Multipliers by Liz Wiseman'
      ],
      talks: [
        { title: 'Amy Cuddy: "Your Body Language Shapes Who You Are"', url: 'https://www.ted.com/talks/amy_cuddy_your_body_language_shapes_who_you_are' },
        { title: 'Sheryl Sandberg: "Why We Have Too Few Women Leaders"', url: 'https://www.ted.com/talks/sheryl_sandberg_why_we_have_too_few_women_leaders' },
        { title: 'Roselinde Torres: "What It Takes to Be a Great Leader"', url: 'https://www.ted.com/talks/roselinde_torres_what_it_takes_to_be_a_great_leader' },
        { title: 'Margaret Heffernan: "Dare to Disagree"', url: 'https://www.ted.com/talks/margaret_heffernan_dare_to_disagree' },
        { title: 'Adam Grant: "Are You a Giver or a Taker?"', url: 'https://www.ted.com/talks/adam_grant_are_you_a_giver_or_a_taker' },
        { title: 'Drew Dudley: "Everyday Leadership"', url: 'https://www.ted.com/talks/drew_dudley_everyday_leadership' }
      ]
    },
    'business_expansion': {
      aiTools: [
        { name: 'Jasper.ai', description: 'High-converting marketing copy', url: 'https://www.jasper.ai' },
        { name: 'Canva AI', description: 'Design campaigns with speed', url: 'https://www.canva.com/ai-image-generator/' },
        { name: 'AdCreative.ai', description: 'Generate tested ad creatives automatically', url: 'https://www.adcreative.ai' },
        { name: 'Tableau', description: 'Advanced data visualization for business strategy', url: 'https://www.tableau.com' },
        { name: 'Zapier', description: 'Workflow automation to scale operations', url: 'https://zapier.com' }
      ],
      books: [
        'Zero to One by Peter Thiel',
        'The Lean Startup by Eric Ries',
        'Blue Ocean Strategy by W. Chan Kim & Renée Mauborgne',
        'The Hard Thing About Hard Things by Ben Horowitz',
        'Measure What Matters by John Doerr'
      ],
      talks: [
        { title: 'Simon Sinek: "How Great Leaders Inspire Action"', url: 'https://www.ted.com/talks/simon_sinek_how_great_leaders_inspire_action' },
        { title: 'Bill Gross: "The Single Biggest Reason Why Startups Succeed"', url: 'https://www.ted.com/talks/bill_gross_the_single_biggest_reason_why_startups_succeed' },
        { title: 'Casey Gerald: "The Gospel of Doubt"', url: 'https://www.ted.com/talks/casey_gerald_the_gospel_of_doubt' },
        { title: 'Linda Hill: "How to Manage for Collective Creativity"', url: 'https://www.ted.com/talks/linda_hill_how_to_manage_for_collective_creativity' },
        { title: 'Martin Reeves: "How to Build a Business That Lasts 100 Years"', url: 'https://www.ted.com/talks/martin_reeves_how_to_build_a_business_that_lasts_100_years' },
        { title: 'Harish Manwani: "Profit\'s Not Always the Point"', url: 'https://www.ted.com/talks/harish_manwani_profit_s_not_always_the_point' }
      ]
    },
    'job_seeking': {
      aiTools: [
        { name: 'Kickresume', description: 'AI-powered résumé and cover letters', url: 'https://kickresume.com' },
        { name: 'Rezi', description: 'Tailored résumé optimization for ATS', url: 'https://rezi.ai' },
        { name: 'Jobscan', description: 'Match résumé to job descriptions', url: 'https://www.jobscan.co' },
        { name: 'LinkedIn Career Explorer', description: 'Skill mapping for emerging roles', url: 'https://linkedin.github.io/career-explorer/' },
        { name: 'Big Interview AI', description: 'Practice interviews with instant AI feedback', url: 'https://biginterview.com' }
      ],
      books: [
        'So Good They Can\'t Ignore You by Cal Newport',
        'The 2-Hour Job Search by Steve Dalton',
        'Never Eat Alone by Keith Ferrazzi',
        'Designing Your Life by Bill Burnett & Dave Evans',
        'What Color Is Your Parachute? by Richard N. Bolles'
      ],
      talks: [
        { title: 'Larry Smith: "Why You Will Fail to Have a Great Career"', url: 'https://www.ted.com/talks/larry_smith_why_you_will_fail_to_have_a_great_career' },
        { title: 'Regina Hartley: "Why the Best Hire Might Not Have the Perfect Resume"', url: 'https://www.ted.com/talks/regina_hartley_why_the_best_hire_might_not_have_the_perfect_resume' },
        { title: 'Angela Lee Duckworth: "Grit: The Power of Passion and Perseverance"', url: 'https://www.ted.com/talks/angela_lee_duckworth_grit_the_power_of_passion_and_perseverance' },
        { title: 'Julian Treasure: "How to Speak So That People Want to Listen"', url: 'https://www.ted.com/talks/julian_treasure_how_to_speak_so_that_people_want_to_listen' },
        { title: 'Celeste Headlee: "10 Ways to Have a Better Conversation"', url: 'https://www.ted.com/talks/celeste_headlee_10_ways_to_have_a_better_conversation' },
        { title: 'Emilie Wapnick: "Why Some of Us Don\'t Have One True Calling"', url: 'https://www.ted.com/talks/emilie_wapnick_why_some_of_us_don_t_have_one_true_calling' }
      ]
    }
  };

  // Function to detect goal category based on goal text
  const detectGoalCategory = (goalText) => {
    if (!goalText) return 'career_growth';
    
    const goal = goalText.toLowerCase();
    
    if (goal.includes('business') || goal.includes('startup') || goal.includes('company') || 
        goal.includes('scale') || goal.includes('expand') || goal.includes('entrepreneur') ||
        goal.includes('founder') || goal.includes('revenue') || goal.includes('market')) {
      return 'business_expansion';
    }
    
    if (goal.includes('job') || goal.includes('hire') || goal.includes('interview') || 
        goal.includes('internship') || goal.includes('graduate') || goal.includes('entry') ||
        goal.includes('resume') || goal.includes('career change') || goal.includes('transition')) {
      return 'job_seeking';
    }
    
    return 'career_growth'; // Default
  };

  // Get current resources based on goal
  const getCurrentResources = () => {
    if (careerGoals.length === 0) return careerResourcesData.career_growth;
    
    const goalCategory = detectGoalCategory(careerGoals[0]?.goal);
    return careerResourcesData[goalCategory] || careerResourcesData.career_growth;
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
          
          {/* Calendar Sub-tabs */}
          <div className="calendar-sub-tabs">
            <button
              className={`calendar-sub-tab ${activeCalendarView === 'upcoming' ? 'active' : ''}`}
              onClick={() => setActiveCalendarView('upcoming')}
            >
              Upcoming Events
            </button>
            <button
              className={`calendar-sub-tab ${activeCalendarView === 'monthly' ? 'active' : ''}`}
              onClick={() => setActiveCalendarView('monthly')}
            >
              Monthly View
            </button>
          </div>

          {/* Upcoming Events View */}
          {activeCalendarView === 'upcoming' && (
            <>
              {/* Upcoming Today Section */}
              <UpcomingToday events={events} onDelete={deleteEvent} />
              
              {/* Smart Suggestions - Donna's Intelligent Assistant */}
              <SmartSuggestions 
                events={events}
                onRescheduleEvent={updateEvent}
                onDeleteEvent={deleteEvent} 
                onRefreshEvents={loadEvents}
                newEvent={newEvent}
                setNewEvent={setNewEvent}
                onCreateEvent={createEvent}
              />
              
              <div className="calendar-grid">

                {/* Events List */}
                <div className="events-grid">
                  {events
                    .filter(event => {
                      // Show all non-today events, plus today events that aren't the next upcoming one
                      if (!isEventToday(event)) return true;
                      
                      // For today's events, show them if they're not the next upcoming event
                      const todayEvents = events.filter(e => isEventToday(e));
                      const nextEvent = todayEvents
                        .filter(e => new Date(e.datetime_utc) >= new Date())
                        .sort((a, b) => new Date(a.datetime_utc) - new Date(b.datetime_utc))[0];
                      
                      return event.id !== nextEvent?.id;
                    })
                    .map((event, index) => (
                      <EventCard
                        key={event.id}
                        event={event}
                        className={`event-card-item ${index < 3 ? 'priority-event' : 'standard-event'}`}
                        onDelete={deleteEvent}
                        onUpdate={updateEvent}
                      />
                    ))}
                  {events.filter(event => {
                    // Count events that would be shown (same logic as above)
                    if (!isEventToday(event)) return true;
                    const todayEvents = events.filter(e => isEventToday(e));
                    const nextEvent = todayEvents
                      .filter(e => new Date(e.datetime_utc) >= new Date())
                      .sort((a, b) => new Date(a.datetime_utc) - new Date(b.datetime_utc))[0];
                    return event.id !== nextEvent?.id;
                  }).length === 0 && (
                    <Card className="empty-card">
                      <CardContent className="empty-content">
                        <Clock className="empty-icon" />
                        <p>No upcoming events. Create your first event above!</p>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </div>
            </>
          )}

          {/* Monthly View */}
          {activeCalendarView === 'monthly' && (
            <MonthlyCalendar 
              events={events}
              onDeleteEvent={deleteEvent}
              onUpdateEvent={updateEvent}
            />
          )}
          
          {/* Timezone Indicator moved to bottom */}
          <TimezoneIndicator className="calendar-timezone-bottom" />
        </TabsContent>

        {/* Career Tab */}
        <TabsContent value="career" className="career-container">
          <div className="career-layout">
            {/* Sticky Goal Bar */}
            <div className="goal-bar-sticky">
              <Card className="goal-input-card">
                <CardContent className="goal-input-content">
                  <Textarea
                    placeholder="Become a Senior Software Engineer at Google"
                    value={newGoal.goal}
                    onChange={(e) => setNewGoal({ ...newGoal, goal: e.target.value })}
                    className="career-goal-input"
                    rows={2}
                  />
                  <Button 
                    onClick={createCareerGoal} 
                    className="generate-plan-btn"
                    disabled={!newGoal.goal.trim() || isGeneratingPlan}
                  >
                    {isGeneratingPlan ? (
                      <>
                        <div className="spinner"></div>
                        Generating plan...
                      </>
                    ) : (
                      'Generate plan'
                    )}
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Sample Action Plan - First Time Experience */}
            {careerGoals.length === 0 && (
              <>
                {/* Sample Plan Message */}
                <div className="sample-plan-message">
                  <p className="sample-message-text">
                    👋 Here's a sample action plan to show you what Donna can do. Enter your own goal above to get a personalized plan tailored just for you!
                  </p>
                </div>

                {/* Sample Action Plan Card */}
                <Card className="action-plan-card">
                  <CardHeader className="action-plan-header">
                    <CardTitle className="action-plan-title">
                      <Target className="title-icon" />
                      Donna's Action Plan
                      <span className="sample-badge">Sample</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="action-plan-content">
                    <div className="action-steps">
                      <div className="action-step">
                        <div className="step-header">
                          <div className="step-number">1</div>
                          <div className="step-content">
                            <h4 className="step-title">Strategic Skill Assessment</h4>
                            <p className="step-description">Identify the top 3 skills required for your target role by analyzing job postings and speaking with current professionals in that position. Create a skills gap analysis to prioritize your development efforts.</p>
                          </div>
                        </div>
                      </div>
                      
                      <div className="action-step">
                        <div className="step-header">
                          <div className="step-number">2</div>
                          <div className="step-content">
                            <h4 className="step-title">Visibility & Relationship Building</h4>
                            <p className="step-description">Schedule monthly one-on-ones with key stakeholders and decision-makers. Share your career aspirations and ask for specific feedback on areas for improvement.</p>
                          </div>
                        </div>
                      </div>

                      <div className="action-step">
                        <div className="step-header">
                          <div className="step-number">3</div>
                          <div className="step-content">
                            <h4 className="step-title">High-Impact Project Leadership</h4>
                            <p className="step-description">Volunteer to lead a cross-functional project that aligns with company priorities. Document and communicate the measurable impact of your leadership.</p>
                          </div>
                        </div>
                      </div>

                      <div className="action-step">
                        <div className="step-header">
                          <div className="step-number">4</div>
                          <div className="step-content">
                            <h4 className="step-title">External Credibility Building</h4>
                            <p className="step-description">Establish thought leadership through industry articles, conference speaking, or professional certifications that demonstrate your expertise beyond your current role.</p>
                            <div className="smart-tool-line">
                              <span className="smart-tool-label">Smart Tool:</span>
                              <span className="smart-tool-suggestion">LinkedIn Learning Analytics</span>
                              <Button variant="link" className="try-this-btn">Try this</Button>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="action-step">
                        <div className="step-header">
                          <div className="step-number">5</div>
                          <div className="step-content">
                            <h4 className="step-title">Strategic Timing & Execution</h4>
                            <p className="step-description">Create a promotion timeline aligned with company review cycles and budget planning. Present your case with quantified achievements and a clear vision for your expanded role.</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}

            {/* Action Plan Card */}
            {careerGoals.length > 0 && (
              <Card className="action-plan-card">
                <CardHeader className="action-plan-header">
                  <CardTitle className="action-plan-title">
                    <Target className="title-icon" />
                    Donna's Action Plan
                  </CardTitle>
                </CardHeader>
                <CardContent className="action-plan-content">
                  <div className="action-steps">
                    {careerGoals[0]?.action_plan && careerGoals[0].action_plan.length > 0 ? (
                      careerGoals[0].action_plan.map((step, index) => (
                        <div key={index + 1} className="action-step">
                          <div className="step-header">
                            <div className="step-number">{index + 1}</div>
                            <div className="step-content">
                              {(() => {
                                const parsed = parseActionPlanStep(step);
                                return (
                                  <>
                                    {parsed.title && (
                                      <h4 className="step-title">{parsed.title}</h4>
                                    )}
                                    <p className="step-description">{parsed.description}</p>
                                  </>
                                );
                              })()}
                              {index === 3 && (
                                <div className="smart-tool-line">
                                  <span className="smart-tool-label">Smart Tool:</span>
                                  <span className="smart-tool-suggestion">LinkedIn Learning Analytics</span>
                                  <Button variant="link" className="try-this-btn">Try this</Button>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))
                    ) : isGeneratingPlan ? (
                      <div className="loading-plan">
                        <div className="loading-spinner"></div>
                        <p>Donna is crafting your personalized action plan...</p>
                        <p className="loading-subtext">This may take a few seconds</p>
                      </div>
                    ) : (
                      <div className="loading-plan">
                        <p>Enter your career goal above and click "Generate plan"</p>
                      </div>
                    )}
                  </div>
                  <div className="action-plan-buttons">
                    <Button variant="outline" className="copy-plan-btn">
                      <Calendar className="button-icon" />
                      Copy Plan
                    </Button>
                    <Button variant="outline" className="save-brag-btn">
                      <Star className="button-icon" />
                      Save to Brag Sheet
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Resource Cards Row */}
            {careerGoals.length > 0 && (() => {
              const resources = getCurrentResources();
              return (
                <div className="resource-cards-row">
                  {/* AI Tools Card */}
                  <Card 
                    className={`resource-card ai-tools-card ${activeResourceCard === 'ai-tools' ? 'active' : ''}`}
                    onClick={() => setActiveResourceCard('ai-tools')}
                  >
                    <CardHeader>
                      <CardTitle className="resource-title">
                        <Sparkles className="resource-icon" />
                        AI Tools
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="resource-content">
                      <p className="resource-hint">
                        {activeResourceCard === 'ai-tools' ? 'Click any tool to try it out' : 'Click to explore AI tools for your goals'}
                      </p>
                      <div className="resource-list">
                        {resources.aiTools.map((tool, index) => (
                          <a 
                            key={index}
                            href={tool.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="resource-item clickable"
                            onClick={(e) => e.stopPropagation()}
                            title={tool.description}
                          >
                            {tool.name}
                          </a>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Books Card */}
                  <Card 
                    className={`resource-card books-card ${activeResourceCard === 'books' ? 'active' : ''}`}
                    onClick={() => setActiveResourceCard('books')}
                  >
                    <CardHeader>
                      <CardTitle className="resource-title">
                        <Target className="resource-icon" />
                        Books
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="resource-content">
                      <p className="resource-hint">
                        {activeResourceCard === 'books' ? 'Curated for your specific goal' : 'Essential reading for your journey'}  
                      </p>
                      <div className="resource-list">
                        {resources.books.map((book, index) => (
                          <div key={index} className="resource-item">{book}</div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Talks/Videos Card */}
                  <Card 
                    className={`resource-card talks-card ${activeResourceCard === 'talks' ? 'active' : ''}`}
                    onClick={() => setActiveResourceCard('talks')}
                  >
                    <CardHeader>
                      <CardTitle className="resource-title">
                        <Calendar className="resource-icon" />
                        Talks & Videos
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="resource-content">
                      <p className="resource-hint">
                        {activeResourceCard === 'talks' ? 'Click any talk to watch on TED' : 'Inspiring talks to shift your perspective'}
                      </p>
                      <div className="resource-list">
                        {resources.talks.map((talk, index) => (
                          <a 
                            key={index}
                            href={talk.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="resource-item clickable"
                            onClick={(e) => e.stopPropagation()}
                            title="Watch on TED"
                          >
                            {talk.title}
                          </a>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              );
            })()}

            {/* Small Reset Button - Always visible at bottom */}
            <div className="career-reset-section">
              <button 
                className="reset-career-btn"
                onClick={resetCareerGoals}
                disabled={isGeneratingPlan}
                title="Clear all career goals and start fresh"
              >
                ↻ Start Fresh
              </button>
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
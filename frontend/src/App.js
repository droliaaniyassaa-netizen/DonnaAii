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
  const [healthStats, setHealthStats] = useState({
    calories: 1250,
    protein: 45,
    hydration: 1500,
    sleep: 7.5
  });
  const [healthTargets, setHealthTargets] = useState({
    calories: 2200,
    protein: 120,
    hydration: 2500,
    sleep: 8
  });
  const [mealInput, setMealInput] = useState('');
  const [customHydration, setCustomHydration] = useState('');
  const [sleepTime, setSleepTime] = useState('');
  const [wakeTime, setWakeTime] = useState('');
  const [sleepAmPm, setSleepAmPm] = useState('PM');
  const [wakeAmPm, setWakeAmPm] = useState('AM');
  const [showGoalModal, setShowGoalModal] = useState(false);
  const [goalStep, setGoalStep] = useState('select'); // 'select', 'weight', 'custom'
  const [selectedGoalType, setSelectedGoalType] = useState('');
  const [currentWeight, setCurrentWeight] = useState('');
  const [customGoals, setCustomGoals] = useState({
    calories: '',
    protein: '',
    hydration: '',
    sleep: ''
  });
  
  // Health state
  const [healthEntries, setHealthEntries] = useState([]);
  const [healthGoals, setHealthGoals] = useState([]);
  const [healthAnalytics, setHealthAnalytics] = useState({});
  const [newHealthEntry, setNewHealthEntry] = useState({ type: 'meal', description: '', date: '', time: '12:00' });
  const [newHealthGoal, setNewHealthGoal] = useState({ goal_type: 'weight_loss', target: '', current_progress: '' });
  
  // UI state
  const [activeTab, setActiveTab] = useState('health');
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

  // Health logging functions
  const logMeal = () => {
    if (!mealInput.trim()) return;
    
    // Simple approximation logic (can be enhanced with AI later)
    const estimatedCalories = estimateCalories(mealInput);
    const estimatedProtein = estimateProtein(mealInput);
    
    setHealthStats(prev => ({
      ...prev,
      calories: prev.calories + estimatedCalories,
      protein: prev.protein + estimatedProtein
    }));
    
    setMealInput('');
  };

  const addHydration = (amount) => {
    setHealthStats(prev => ({
      ...prev,
      hydration: prev.hydration + amount
    }));
    setCustomHydration('');
  };

  const logSleepFromTimes = () => {
    if (!sleepTime || !wakeTime) return;
    
    const hours = calculateSleepHours(sleepTime, wakeTime);
    if (hours > 0) {
      setHealthStats(prev => ({
        ...prev,
        sleep: hours
      }));
      setSleepTime('');
      setWakeTime('');
      setSleepAmPm('PM');
      setWakeAmPm('AM');
    }
  };

  // Simple estimation functions (can be enhanced with AI)
  const estimateCalories = (meal) => {
    const mealLower = meal.toLowerCase();
    if (mealLower.includes('salad')) return 150;
    if (mealLower.includes('roti') || mealLower.includes('bread')) return 100;
    if (mealLower.includes('rice')) return 200;
    if (mealLower.includes('chicken')) return 250;
    if (mealLower.includes('dal')) return 120;
    return 100; // Default estimate
  };

  const estimateProtein = (meal) => {
    const mealLower = meal.toLowerCase();
    if (mealLower.includes('chicken')) return 25;
    if (mealLower.includes('dal')) return 8;
    if (mealLower.includes('egg')) return 12;
    if (mealLower.includes('paneer')) return 15;
    return 5; // Default estimate
  };





  // Goal calculation functions - Scientifically accurate
  const calculateGoalTargets = (goalType, weightKg) => {
    const weight = parseFloat(weightKg);
    if (!weight || weight <= 0) {
      return null;
    }

    let targets = {
      hydration: Math.round(35 * weight), // ml - 35ml per kg is standard
      sleep: 8 // default 8 hours for all goals
    };

    switch (goalType) {
      case 'maintain':
        targets.calories = Math.round(30 * weight); // ~30 kcal per kg for maintenance
        targets.protein = Math.round(1.4 * weight); // 1.4g per kg for maintenance
        break;
      
      case 'lose':
        let loseCalories = Math.round(25 * weight); // ~25 kcal per kg for weight loss
        let maintainCalories = Math.round(30 * weight);
        
        // Safety rails: never drop more than 750 kcal below maintain or under 1200 kcal total
        if (maintainCalories - loseCalories > 750) {
          loseCalories = maintainCalories - 750;
        }
        if (loseCalories < 1200) {
          loseCalories = 1200;
        }
        
        targets.calories = loseCalories;
        targets.protein = Math.round(2.0 * weight); // Higher protein during weight loss - 2.0g per kg
        break;
      
      case 'gain':
        let gainCalories = Math.round(33 * weight); // ~33 kcal per kg for muscle gain
        let maintainCals = Math.round(30 * weight);
        
        // Safety rail: don't push more than 350 kcal surplus
        if (gainCalories - maintainCals > 350) {
          gainCalories = maintainCals + 350;
        }
        
        targets.calories = gainCalories;
        targets.protein = Math.round(2.0 * weight); // High protein for muscle synthesis - 2.0g per kg
        break;
      
      default:
        return null;
    }

    return targets;
  };

  const handleGoalSubmit = () => {
    
    if (selectedGoalType === 'custom') {
      // Handle custom goals
      let finalTargets = { ...customGoals };
      
      // Fill in blanks with maintain weight logic if weight is provided
      if (currentWeight) {
        const weight = parseFloat(currentWeight);

        if (weight > 0) {
          if (!finalTargets.calories) finalTargets.calories = Math.round(30 * weight);
          if (!finalTargets.protein) finalTargets.protein = Math.round(1.4 * weight);
          if (!finalTargets.hydration) finalTargets.hydration = Math.round(35 * weight);
          if (!finalTargets.sleep) finalTargets.sleep = 8;
        }
      }
      
      setHealthTargets({
        calories: parseInt(finalTargets.calories) || 2000,
        protein: parseInt(finalTargets.protein) || 100,
        hydration: parseInt(finalTargets.hydration) || 2500,
        sleep: parseFloat(finalTargets.sleep) || 8
      });
    } else {
      // Handle preset goals
      const targets = calculateGoalTargets(selectedGoalType, currentWeight);
      if (targets) {
        console.log('Calculated targets:', targets);
        const newTargets = {
          calories: targets.calories,
          protein: targets.protein,
          hydration: targets.hydration,
          sleep: targets.sleep
        };
        console.log('Setting new health targets:', newTargets);
        setHealthTargets(newTargets);
      }
    }
    
    // Close modal and reset state
    setShowGoalModal(false);
    setGoalStep('select');
    setSelectedGoalType('');
    setCurrentWeight('');
    setCustomGoals({ calories: '', protein: '', hydration: '', sleep: '' });
  };

  const calculateSleepHours = (sleepTime, wakeTime) => {
    const [sleepHour, sleepMin] = sleepTime.split(':').map(Number);
    const [wakeHour, wakeMin] = wakeTime.split(':').map(Number);
    
    // Convert to 24-hour format based on AM/PM
    let sleep24Hour = sleepHour;
    let wake24Hour = wakeHour;
    
    // Convert sleep time to 24-hour format
    if (sleepAmPm === 'PM' && sleepHour !== 12) {
      sleep24Hour = sleepHour + 12;
    } else if (sleepAmPm === 'AM' && sleepHour === 12) {
      sleep24Hour = 0;
    }
    
    // Convert wake time to 24-hour format
    if (wakeAmPm === 'PM' && wakeHour !== 12) {
      wake24Hour = wakeHour + 12;
    } else if (wakeAmPm === 'AM' && wakeHour === 12) {
      wake24Hour = 0;
    }
    
    let sleepMinutes = sleep24Hour * 60 + sleepMin;
    let wakeMinutes = wake24Hour * 60 + wakeMin;
    
    // Handle overnight sleep (e.g., sleep at 11 PM, wake at 7 AM)
    if (wakeMinutes <= sleepMinutes) {
      wakeMinutes += 24 * 60; // Add 24 hours to wake time
    }
    
    return (wakeMinutes - sleepMinutes) / 60;
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
                    Here's a sample action plan to show you what Donna can do. Enter your own goal above to get a personalized plan tailored just for you!
                  </p>
                </div>

                {/* Sample Goal Display */}
                <div className="sample-goal-display">
                  <p className="sample-goal-text">
                    <strong>Sample Goal:</strong> "How can I get promoted from associate to team lead this year?"
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
                            <h4 className="step-title">Map the Decision Makers</h4>
                            <p className="step-description">Identify your manager, their manager, and one peer with strong informal influence in leadership decisions. Study their communication styles, priorities, and current challenges. Position your contributions to directly support their visible wins.</p>
                            <p className="step-insight">
                              <span className="insight-label">Insight:</span> Promotions happen when the right three people talk about you. Design your output for their radar, not the whole office.
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      <div className="action-step">
                        <div className="step-header">
                          <div className="step-number">2</div>
                          <div className="step-content">
                            <h4 className="step-title">Deploy Leadership Signal Tools</h4>
                            <p className="step-description">Implement a team productivity tool (like Notion for project tracking or Slack automation for status updates) that makes your leadership capabilities visible daily. Every time the team benefits from your system, they associate you with solutions.</p>
                            <p className="step-insight">
                              <span className="insight-label">Insight:</span> Every time the team saves effort with your tool, they unconsciously credit you. That repetition builds relevance faster than any self-promotion.
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="action-step">
                        <div className="step-header">
                          <div className="step-number">3</div>
                          <div className="step-content">
                            <h4 className="step-title">Own Cross-Functional Wins</h4>
                            <p className="step-description">Volunteer for one high-visibility project that requires coordinating with other departments. Focus on projects tied to company KPIs or executive priorities. Document your role in driving measurable outcomes and collaboration success.</p>
                            <p className="step-insight">
                              <span className="insight-label">Insight:</span> Leadership sees coordination as the hardest skill to scale. When you can make other departments work together, you look like management material.
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="action-step">
                        <div className="step-header">
                          <div className="step-number">4</div>
                          <div className="step-content">
                            <h4 className="step-title">Build External Authority</h4>
                            <p className="step-description">Write one industry article or speak at a professional event within 90 days. Share strategic insights from your work (without confidential details). When leadership sees you representing the company externally, your internal credibility multiplies.</p>
                            <p className="step-insight">
                              <span className="insight-label">Insight:</span> When leadership sees you representing the company externally, they start viewing you as a brand ambassador, not just an employee.
                            </p>
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
                            <h4 className="step-title">Execute the Strategic Ask</h4>
                            <p className="step-description">Create a "promotion proposal" document with quantified achievements, expanded responsibilities you've already taken on, and specific value you'll deliver as team lead. Time your ask 4-6 weeks before annual reviews when budgets and roles are being planned.</p>
                            <p className="step-insight">
                              <span className="insight-label">Insight:</span> The ask becomes less "please promote me" and more "here's the logical next step to expand impact." That tone is taken seriously.
                            </p>
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

            {/* Resource Cards Row - Both Sample and User Goals */}
            {(() => {
              const resources = careerGoals.length > 0 ? getCurrentResources() : careerResourcesData.career_growth;
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
                        {careerGoals.length === 0 && <span className="sample-badge-small">Sample</span>}
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
                        {careerGoals.length === 0 && <span className="sample-badge-small">Sample</span>}
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
                        {careerGoals.length === 0 && <span className="sample-badge-small">Sample</span>}
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

        {/* Health Tab - Complete Redesign */}
        <TabsContent value="health" className="health-container">
          <div className="health-content">
            
            {/* Set Goals Button - Top Position */}
            <div className="health-goals-header">
              <Button onClick={() => setShowGoalModal(true)} className="luxury-set-goals-btn">
                Set Goals
              </Button>
            </div>
            
            {/* Sophisticated Circular Progress Stats */}
            <div className="health-stats-grid">
              
              {/* Calories */}
              <div className="sophisticated-stat">
                <div className="segmented-circle">
                  <svg className="segmented-ring" width="160" height="160" viewBox="0 0 140 140">
                    {Array.from({length: 60}, (_, i) => {
                      const angle = (i * 6) * (Math.PI / 180);
                      const progress = healthStats.calories / healthTargets.calories;
                      const isActive = i <= (progress * 60);
                      const x1 = 70 + 55 * Math.cos(angle - Math.PI / 2);
                      const y1 = 70 + 55 * Math.sin(angle - Math.PI / 2);
                      const x2 = 70 + 45 * Math.cos(angle - Math.PI / 2);
                      const y2 = 70 + 45 * Math.sin(angle - Math.PI / 2);
                      
                      let segmentColor = 'rgba(75, 85, 99, 0.3)';
                      if (isActive) {
                        if (i < 15) segmentColor = 'rgba(245, 158, 11, 0.9)';
                        else if (i < 30) segmentColor = 'rgba(251, 146, 60, 0.9)';
                        else if (i < 45) segmentColor = 'rgba(249, 115, 22, 0.9)';
                        else segmentColor = 'rgba(234, 88, 12, 0.9)';
                      }
                      
                      return (
                        <line
                          key={i}
                          x1={x1} y1={y1} x2={x2} y2={y2}
                          stroke={segmentColor}
                          strokeWidth="3"
                          strokeLinecap="round"
                        />
                      );
                    })}
                  </svg>
                  <div className="stat-center">
                    <div className="stat-value">{healthStats.calories}kcal</div>
                    <div className="stat-subtitle">Calories</div>
                  </div>
                </div>
              </div>

              {/* Protein */}
              <div className="sophisticated-stat">
                <div className="segmented-circle">
                  <svg className="segmented-ring" width="160" height="160" viewBox="0 0 140 140">
                    {Array.from({length: 60}, (_, i) => {
                      const angle = (i * 6) * (Math.PI / 180);
                      const progress = healthStats.protein / healthTargets.protein;
                      const isActive = i <= (progress * 60);
                      const x1 = 70 + 55 * Math.cos(angle - Math.PI / 2);
                      const y1 = 70 + 55 * Math.sin(angle - Math.PI / 2);
                      const x2 = 70 + 45 * Math.cos(angle - Math.PI / 2);
                      const y2 = 70 + 45 * Math.sin(angle - Math.PI / 2);
                      
                      let segmentColor = 'rgba(75, 85, 99, 0.3)';
                      if (isActive) {
                        if (i < 15) segmentColor = 'rgba(168, 85, 247, 0.9)';
                        else if (i < 30) segmentColor = 'rgba(139, 92, 246, 0.9)';
                        else if (i < 45) segmentColor = 'rgba(99, 102, 241, 0.9)';
                        else segmentColor = 'rgba(59, 130, 246, 0.9)';
                      }
                      
                      return (
                        <line
                          key={i}
                          x1={x1} y1={y1} x2={x2} y2={y2}
                          stroke={segmentColor}
                          strokeWidth="3"
                          strokeLinecap="round"
                        />
                      );
                    })}
                  </svg>
                  <div className="stat-center">
                    <div className="stat-value">{healthStats.protein}g</div>
                    <div className="stat-subtitle">Protein</div>
                  </div>
                </div>
              </div>

              {/* Hydration */}
              <div className="sophisticated-stat">
                <div className="segmented-circle">
                  <svg className="segmented-ring" width="160" height="160" viewBox="0 0 140 140">
                    {Array.from({length: 60}, (_, i) => {
                      const angle = (i * 6) * (Math.PI / 180);
                      const progress = healthStats.hydration / healthTargets.hydration;
                      const isActive = i <= (progress * 60);
                      const x1 = 70 + 55 * Math.cos(angle - Math.PI / 2);
                      const y1 = 70 + 55 * Math.sin(angle - Math.PI / 2);
                      const x2 = 70 + 45 * Math.cos(angle - Math.PI / 2);
                      const y2 = 70 + 45 * Math.sin(angle - Math.PI / 2);
                      
                      let segmentColor = 'rgba(75, 85, 99, 0.3)';
                      if (isActive) {
                        if (i < 15) segmentColor = 'rgba(14, 165, 233, 0.9)';
                        else if (i < 30) segmentColor = 'rgba(6, 182, 212, 0.9)';
                        else if (i < 45) segmentColor = 'rgba(20, 184, 166, 0.9)';
                        else segmentColor = 'rgba(16, 185, 129, 0.9)';
                      }
                      
                      return (
                        <line
                          key={i}
                          x1={x1} y1={y1} x2={x2} y2={y2}
                          stroke={segmentColor}
                          strokeWidth="3"
                          strokeLinecap="round"
                        />
                      );
                    })}
                  </svg>
                  <div className="stat-center">
                    <div className="stat-value">{healthStats.hydration}ml</div>
                    <div className="stat-subtitle">Water</div>
                  </div>
                </div>
              </div>

              {/* Sleep */}
              <div className="sophisticated-stat">
                <div className="segmented-circle">
                  <svg className="segmented-ring" width="160" height="160" viewBox="0 0 140 140">
                    {Array.from({length: 60}, (_, i) => {
                      const angle = (i * 6) * (Math.PI / 180);
                      const progress = healthStats.sleep / healthTargets.sleep;
                      const isActive = i <= (progress * 60);
                      const x1 = 70 + 55 * Math.cos(angle - Math.PI / 2);
                      const y1 = 70 + 55 * Math.sin(angle - Math.PI / 2);
                      const x2 = 70 + 45 * Math.cos(angle - Math.PI / 2);
                      const y2 = 70 + 45 * Math.sin(angle - Math.PI / 2);
                      
                      let segmentColor = 'rgba(75, 85, 99, 0.3)';
                      if (isActive) {
                        if (i < 15) segmentColor = 'rgba(34, 197, 94, 0.9)';
                        else if (i < 30) segmentColor = 'rgba(22, 163, 74, 0.9)';
                        else if (i < 45) segmentColor = 'rgba(21, 128, 61, 0.9)';
                        else segmentColor = 'rgba(22, 101, 52, 0.9)';
                      }
                      
                      return (
                        <line
                          key={i}
                          x1={x1} y1={y1} x2={x2} y2={y2}
                          stroke={segmentColor}
                          strokeWidth="3"
                          strokeLinecap="round"
                        />
                      );
                    })}
                  </svg>
                  <div className="stat-center">
                    <div className="stat-value">{healthStats.sleep}h</div>
                    <div className="stat-subtitle">Sleep</div>
                  </div>
                </div>
              </div>

            </div>

            {/* Sleek Logging Section */}
            <div className="health-logging-section">
              
              {/* Log Sleep - Moved to top */}
              <div className="sleek-logging-block">
                <h3 className="logging-label">
                  Log Sleep
                  <div className="section-icon moon-icon"></div>
                </h3>
                <div className="sleep-time-inputs">
                  <div className="time-input-group">
                    <label className="time-label">Slept at:</label>
                    <div className="time-input-with-ampm">
                      <Input
                        type="time"
                        value={sleepTime}
                        onChange={(e) => setSleepTime(e.target.value)}
                        className="time-input"
                      />
                      <div className="ampm-toggle">
                        <button
                          type="button"
                          className={`ampm-btn ${sleepAmPm === 'AM' ? 'active' : ''}`}
                          onClick={() => setSleepAmPm('AM')}
                        >
                          AM
                        </button>
                        <button
                          type="button"
                          className={`ampm-btn ${sleepAmPm === 'PM' ? 'active' : ''}`}
                          onClick={() => setSleepAmPm('PM')}
                        >
                          PM
                        </button>
                      </div>
                    </div>
                  </div>
                  <div className="time-input-group">
                    <label className="time-label">Woke up at:</label>
                    <div className="time-input-with-ampm">
                      <Input
                        type="time"
                        value={wakeTime}
                        onChange={(e) => setWakeTime(e.target.value)}
                        className="time-input"
                      />
                      <div className="ampm-toggle">
                        <button
                          type="button"
                          className={`ampm-btn ${wakeAmPm === 'AM' ? 'active' : ''}`}
                          onClick={() => setWakeAmPm('AM')}
                        >
                          AM
                        </button>
                        <button
                          type="button"
                          className={`ampm-btn ${wakeAmPm === 'PM' ? 'active' : ''}`}
                          onClick={() => setWakeAmPm('PM')}
                        >
                          PM
                        </button>
                      </div>
                    </div>
                  </div>
                  <Button onClick={logSleepFromTimes} className="sleek-log-btn sleep-btn">
                    Log Sleep
                  </Button>
                </div>
              </div>

              {/* Log Meals */}
              <div className="sleek-logging-block">
                <h3 className="logging-label">
                  Log Meals
                  <div className="section-icon meal-icon"></div>
                </h3>
                <div className="meal-input-container">
                  <Textarea
                    placeholder="Describe your meal (e.g., 'bowl of salad', '2 rotis with dal')"
                    value={mealInput}
                    onChange={(e) => setMealInput(e.target.value)}
                    className="sleek-textarea"
                  />
                  <Button onClick={logMeal} className="sleek-log-btn meal-btn">
                    Log Meal
                  </Button>
                </div>
              </div>

              {/* Log Hydration */}
              <div className="sleek-logging-block">
                <h3 className="logging-label">
                  Log Hydration
                  <div className="section-icon hydration-icon"></div>
                </h3>
                <div className="hydration-controls">
                  <div className="hydration-buttons">
                    <Button onClick={() => addHydration(250)} className="sleek-hydration-btn">
                      + Glass (250ml)
                    </Button>
                    <Button onClick={() => addHydration(500)} className="sleek-hydration-btn">
                      + Bottle (500ml)
                    </Button>
                  </div>
                  <div className="custom-hydration">
                    <Input
                      type="number"
                      placeholder="Custom ml"
                      value={customHydration}
                      onChange={(e) => setCustomHydration(e.target.value)}
                      className="sleek-input"
                    />
                    <Button onClick={() => addHydration(parseInt(customHydration) || 0)} className="sleek-log-btn hydration-btn">
                      Add
                    </Button>
                  </div>
                </div>
              </div>

            </div>



          </div>
        </TabsContent>
      </Tabs>
      
      {/* Settings Modal */}
      <SettingsModal 
        open={showSettings} 
        onClose={() => setShowSettings(false)} 
      />

      {/* Goal Setting Modal */}
      {showGoalModal && (
        <div className="goal-modal-overlay">
          <div className="goal-modal-content">
            <div className="goal-modal-header">
              <h3 className="goal-modal-title">Set Your Health Goals</h3>
              <button 
                className="goal-modal-close"
                onClick={() => {
                  setShowGoalModal(false);
                  setGoalStep('select');
                  setSelectedGoalType('');
                  setCurrentWeight('');
                  setCustomGoals({ calories: '', protein: '', hydration: '', sleep: '' });
                }}
              >
                ×
              </button>
            </div>

            <div className="goal-modal-body">
              {goalStep === 'select' && (
                <div className="goal-options">
                  <div className="goal-options-grid">
                    <button
                      className="goal-option-card"
                      onClick={() => {
                        setSelectedGoalType('lose');
                        setGoalStep('weight');
                      }}
                    >
                      <div className="goal-option-indicator lose-indicator"></div>
                      <div className="goal-option-title">Lose Weight</div>
                      <div className="goal-option-desc">Optimized calorie deficit for safe weight loss</div>
                    </button>

                    <button
                      className="goal-option-card"
                      onClick={() => {
                        setSelectedGoalType('gain');
                        setGoalStep('weight');
                      }}
                    >
                      <div className="goal-option-indicator gain-indicator"></div>
                      <div className="goal-option-title">Gain Muscle</div>
                      <div className="goal-option-desc">Higher protein & calories for muscle growth</div>
                    </button>

                    <button
                      className="goal-option-card"
                      onClick={() => {
                        setSelectedGoalType('maintain');
                        setGoalStep('weight');
                      }}
                    >
                      <div className="goal-option-indicator maintain-indicator"></div>
                      <div className="goal-option-title">Maintain Weight</div>
                      <div className="goal-option-desc">Balanced nutrition for current weight</div>
                    </button>

                    <button
                      className="goal-option-card"
                      onClick={() => {
                        setSelectedGoalType('custom');
                        setGoalStep('custom');
                      }}
                    >
                      <div className="goal-option-indicator custom-indicator"></div>
                      <div className="goal-option-title">Custom Goals</div>
                      <div className="goal-option-desc">Set your own personalized targets</div>
                    </button>
                  </div>
                </div>
              )}

              {goalStep === 'weight' && (
                <div className="goal-weight-input">
                  <div className="weight-input-section">
                    <label className="weight-label">Current Weight (kg)</label>
                    <Input
                      type="number"
                      value={currentWeight}
                      onChange={(e) => setCurrentWeight(e.target.value)}
                      className="weight-input"
                      placeholder="70"
                    />
                    <div className="weight-explanation">
                      Weight is needed so I can calculate your personal targets based on your goal.
                    </div>
                  </div>
                  
                  <div className="goal-actions">
                    <Button 
                      onClick={() => setGoalStep('select')}
                      className="goal-btn-secondary"
                    >
                      Back
                    </Button>
                    <Button 
                      onClick={() => {
                        console.log('Calculate button clicked!');
                        handleGoalSubmit();
                      }}
                      className="goal-btn-primary"
                      disabled={!currentWeight}
                    >
                      Calculate Targets
                    </Button>
                  </div>
                </div>
              )}

              {goalStep === 'custom' && (
                <div className="goal-custom-input">
                  <div className="custom-goals-grid">
                    <div className="custom-goal-field">
                      <label className="custom-label">Daily Calories</label>
                      <Input
                        type="number"
                        value={customGoals.calories}
                        onChange={(e) => setCustomGoals(prev => ({ ...prev, calories: e.target.value }))}
                        className="custom-input"
                        placeholder="2000"
                      />
                    </div>
                    
                    <div className="custom-goal-field">
                      <label className="custom-label">Protein (g)</label>  
                      <Input
                        type="number"
                        value={customGoals.protein}
                        onChange={(e) => setCustomGoals(prev => ({ ...prev, protein: e.target.value }))}
                        className="custom-input"
                        placeholder="100"
                      />
                    </div>
                    
                    <div className="custom-goal-field">
                      <label className="custom-label">Water (ml)</label>
                      <Input
                        type="number"
                        value={customGoals.hydration}
                        onChange={(e) => setCustomGoals(prev => ({ ...prev, hydration: e.target.value }))}
                        className="custom-input"
                        placeholder="2500"
                      />
                    </div>
                    
                    <div className="custom-goal-field">
                      <label className="custom-label">Sleep (hours)</label>
                      <Input
                        type="number"
                        step="0.5"
                        value={customGoals.sleep}
                        onChange={(e) => setCustomGoals(prev => ({ ...prev, sleep: e.target.value }))}
                        className="custom-input"
                        placeholder="8"
                      />
                    </div>
                  </div>

                  <div className="weight-input-section" style={{ marginTop: '1.5rem' }}>
                    <label className="weight-label">Current Weight (kg) <span style={{ opacity: 0.6 }}>(optional)</span></label>
                    <Input
                      type="number"
                      value={currentWeight}
                      onChange={(e) => setCurrentWeight(e.target.value)}
                      className="weight-input"
                      placeholder="70"
                    />
                    <div className="weight-explanation">
                      If provided, I'll fill in any blank fields with calculated values.
                    </div>
                  </div>
                  
                  <div className="goal-actions">
                    <Button 
                      onClick={() => setGoalStep('select')}
                      className="goal-btn-secondary"
                    >
                      Back
                    </Button>
                    <Button 
                      onClick={handleGoalSubmit}
                      className="goal-btn-primary"
                    >
                      Set Custom Goals
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
    </div>
  );
};

export default App;
// Advanced event processing for Donna's intelligent calendar
import { combineDateTimeToUTC, getCurrentInUserTimezone } from './timezone';
import { parseISO, addDays, addWeeks, isValid, format } from 'date-fns';

// Event categories with color schemes
export const EVENT_CATEGORIES = {
  PERSONAL: {
    id: 'personal',
    name: 'Personal',
    color: 'rgba(139, 95, 191, 0.15)',
    borderColor: 'rgba(139, 95, 191, 0.3)',
    textColor: 'rgba(139, 95, 191, 0.9)',
    keywords: ['birthday', 'anniversary', 'family', 'personal', 'celebration', 'party', 'dinner', 'lunch', 'date', 'vacation', 'holiday']
  },
  WORK: {
    id: 'work',
    name: 'Work',
    color: 'rgba(184, 134, 11, 0.15)',
    borderColor: 'rgba(184, 134, 11, 0.3)',
    textColor: 'rgba(184, 134, 11, 0.9)',
    keywords: ['meeting', 'conference', 'project', 'deadline', 'presentation', 'interview', 'work', 'office', 'client', 'team', 'standup', 'review']
  },
  APPOINTMENTS: {
    id: 'appointments',
    name: 'Appointments',
    color: 'rgba(32, 178, 170, 0.15)',
    borderColor: 'rgba(32, 178, 170, 0.3)',
    textColor: 'rgba(32, 178, 170, 0.9)',
    keywords: ['doctor', 'dentist', 'appointment', 'checkup', 'medical', 'hospital', 'clinic', 'therapy', 'consultation', 'salon', 'haircut', 'massage']
  },
  ACTIVITIES: {
    id: 'activities',
    name: 'Activities',
    color: 'rgba(102, 205, 170, 0.15)',
    borderColor: 'rgba(102, 205, 170, 0.3)',
    textColor: 'rgba(102, 205, 170, 0.9)',
    keywords: ['gym', 'workout', 'exercise', 'yoga', 'run', 'fitness', 'sport', 'training', 'class', 'lesson', 'practice', 'activity']
  }
};

// Time-related keywords and their mappings
const TIME_PATTERNS = {
  // Relative days
  'today': 0,
  'tomorrow': 1,
  'next week': 7,
  'next monday': 'next_monday',
  'next tuesday': 'next_tuesday',
  'next wednesday': 'next_wednesday',
  'next thursday': 'next_thursday',
  'next friday': 'next_friday',
  'next saturday': 'next_saturday',
  'next sunday': 'next_sunday',
  
  // Times
  'morning': '09:00',
  'afternoon': '14:00',
  'evening': '18:00',
  'night': '20:00',
  'noon': '12:00',
  'midnight': '00:00'
};

// Advanced natural language processing for event extraction
export const extractEventFromMessage = (message) => {
  const text = message.toLowerCase().trim();
  
  // Initialize event object
  const eventData = {
    title: '',
    description: message,
    category: 'personal',
    date: null,
    time: '12:00', // Default to 12 PM
    rawMessage: message,
    confidence: 0
  };
  
  try {
    // Extract title (first part before date/time indicators)
    let title = extractEventTitle(text);
    eventData.title = title || 'Event';
    
    // Extract and parse date
    const dateInfo = extractDate(text);
    if (dateInfo.date) {
      eventData.date = dateInfo.date;
      eventData.confidence += 0.4;
    }
    
    // Extract time
    const timeInfo = extractTime(text);
    if (timeInfo.time) {
      eventData.time = timeInfo.time;
      eventData.confidence += 0.3;
    }
    
    // Categorize event
    const category = categorizeEvent(text);
    eventData.category = category;
    eventData.confidence += 0.3;
    
    return eventData;
  } catch (error) {
    console.warn('Error processing event message:', error);
    return null;
  }
};

// Extract event title from message
const extractEventTitle = (text) => {
  // Remove time and date patterns to get clean title
  let cleanText = text;
  
  // Remove time patterns
  cleanText = cleanText.replace(/\b(\d{1,2}):(\d{2})\s?(am|pm)?\b/gi, '');
  cleanText = cleanText.replace(/\b(morning|afternoon|evening|night|noon|midnight)\b/gi, '');
  
  // Remove date patterns
  cleanText = cleanText.replace(/\b(today|tomorrow|next week)\b/gi, '');
  cleanText = cleanText.replace(/\b(next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b/gi, '');
  cleanText = cleanText.replace(/\b(\d{1,2}\/\d{1,2}\/?\d{0,4})\b/g, '');
  cleanText = cleanText.replace(/\b(\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec))\b/gi, '');
  
  // Remove common scheduling words
  cleanText = cleanText.replace(/\b(i have|i have a|schedule|book|appointment|meeting)\b/gi, '');
  cleanText = cleanText.replace(/\b(at|on|for)\s*$/gi, '');
  
  // Clean up and capitalize
  cleanText = cleanText.trim().replace(/\s+/g, ' ');
  
  if (cleanText.length > 0) {
    return cleanText.charAt(0).toUpperCase() + cleanText.slice(1);
  }
  
  return 'Event';
};

// Extract date from message
const extractDate = (text) => {
  const now = getCurrentInUserTimezone();
  
  // Check for relative dates
  if (text.includes('today')) {
    return { date: format(now, 'yyyy-MM-dd'), confidence: 0.9 };
  }
  
  if (text.includes('tomorrow')) {
    return { date: format(addDays(now, 1), 'yyyy-MM-dd'), confidence: 0.9 };
  }
  
  if (text.includes('next week')) {
    return { date: format(addWeeks(now, 1), 'yyyy-MM-dd'), confidence: 0.7 };
  }
  
  // Check for specific weekdays
  const weekdayMatch = text.match(/next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)/i);
  if (weekdayMatch) {
    const targetDay = weekdayMatch[1].toLowerCase();
    const targetDate = getNextWeekday(now, targetDay);
    return { date: format(targetDate, 'yyyy-MM-dd'), confidence: 0.8 };
  }
  
  // Check for date formats (MM/DD, MM/DD/YYYY)
  const dateMatch = text.match(/\b(\d{1,2})\/(\d{1,2})\/?\d{0,4}\b/);
  if (dateMatch) {
    try {
      const month = parseInt(dateMatch[1]);
      const day = parseInt(dateMatch[2]);
      const year = now.getFullYear();
      
      if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
        const dateStr = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
        return { date: dateStr, confidence: 0.8 };
      }
    } catch (error) {
      console.warn('Error parsing date:', error);
    }
  }
  
  // Check for month day format (Aug 27, 27 Aug)
  const monthDayMatch = text.match(/\b(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i);
  if (monthDayMatch) {
    try {
      const day = parseInt(monthDayMatch[1]);
      const month = getMonthNumber(monthDayMatch[2].toLowerCase());
      const year = now.getFullYear();
      
      const dateStr = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
      return { date: dateStr, confidence: 0.8 };
    } catch (error) {
      console.warn('Error parsing month/day:', error);
    }
  }
  
  return { date: null, confidence: 0 };
};

// Extract time from message
const extractTime = (text) => {
  // Check for specific time formats (3:30 PM, 15:30, 3pm)
  const timeMatch = text.match(/\b(\d{1,2}):?(\d{2})?\s?(am|pm)\b/i);
  if (timeMatch) {
    let hours = parseInt(timeMatch[1]);
    const minutes = timeMatch[2] ? parseInt(timeMatch[2]) : 0;
    const ampm = timeMatch[3] ? timeMatch[3].toLowerCase() : null;
    
    if (ampm === 'pm' && hours !== 12) hours += 12;
    if (ampm === 'am' && hours === 12) hours = 0;
    
    const timeStr = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    return { time: timeStr, confidence: 0.9 };
  }
  
  // Check for hour-only format (3pm, 15h)
  const hourMatch = text.match(/\b(\d{1,2})\s?(pm|am)\b/i);
  if (hourMatch) {
    let hours = parseInt(hourMatch[1]);
    const ampm = hourMatch[2].toLowerCase();
    
    if (ampm === 'pm' && hours !== 12) hours += 12;
    if (ampm === 'am' && hours === 12) hours = 0;
    
    const timeStr = `${hours.toString().padStart(2, '0')}:00`;
    return { time: timeStr, confidence: 0.8 };
  }
  
  // Check for relative times
  for (const [keyword, time] of Object.entries(TIME_PATTERNS)) {
    if (text.includes(keyword) && time.includes(':')) {
      return { time, confidence: 0.6 };
    }
  }
  
  return { time: null, confidence: 0 };
};

// Categorize event based on keywords
const categorizeEvent = (text) => {
  let bestMatch = 'personal';
  let bestScore = 0;
  
  for (const [categoryId, category] of Object.entries(EVENT_CATEGORIES)) {
    let score = 0;
    
    for (const keyword of category.keywords) {
      if (text.includes(keyword)) {
        score += 1;
      }
    }
    
    if (score > bestScore) {
      bestScore = score;
      bestMatch = categoryId;
    }
  }
  
  return bestMatch;
};

// Helper function to get next occurrence of a weekday
const getNextWeekday = (date, targetDay) => {
  const days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
  const currentDay = date.getDay();
  const targetIndex = days.indexOf(targetDay.toLowerCase());
  
  let daysToAdd = targetIndex - currentDay;
  if (daysToAdd <= 0) daysToAdd += 7; // Next week
  
  return addDays(date, daysToAdd);
};

// Helper function to convert month name to number
const getMonthNumber = (monthName) => {
  const months = {
    jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6,
    jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12
  };
  return months[monthName.toLowerCase()] || 1;
};

// Check if message is likely an event scheduling request
export const isEventMessage = (message) => {
  const text = message.toLowerCase();
  
  // Event indicators
  const eventIndicators = [
    'meeting', 'appointment', 'schedule', 'book', 'i have',
    'tomorrow', 'today', 'next week', 'next', 'at', 'pm', 'am',
    'doctor', 'dentist', 'gym', 'workout', 'lunch', 'dinner',
    'birthday', 'anniversary'
  ];
  
  return eventIndicators.some(indicator => text.includes(indicator));
};

// Generate default reminders for event category
export const getDefaultReminders = (category) => {
  const baseReminders = [
    { time: 12 * 60, label: '12 hours before' }, // 12 hours in minutes
    { time: 2 * 60, label: '2 hours before' }    // 2 hours in minutes
  ];
  
  // Customize reminders based on category
  switch (category) {
    case 'appointments':
      return [
        { time: 24 * 60, label: '1 day before' },
        { time: 2 * 60, label: '2 hours before' }
      ];
    case 'work':
      return [
        { time: 60, label: '1 hour before' },
        { time: 15, label: '15 minutes before' }
      ];
    case 'activities':
      return [
        { time: 4 * 60, label: '4 hours before' },
        { time: 30, label: '30 minutes before' }
      ];
    default:
      return baseReminders;
  }
};
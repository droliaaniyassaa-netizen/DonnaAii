// Advanced event processing for Donna's intelligent calendar
import { combineDateTimeToUTC, getCurrentInUserTimezone } from './timezone';
import { parseISO, addDays, addWeeks, addHours, addMinutes, isValid, format } from 'date-fns';

// SINGLE SOURCE OF TRUTH: Event categories with EXACT color mapping
// This is the authoritative definition used everywhere in the application
export const EVENT_CATEGORIES = {
  PERSONAL: {
    id: 'personal',
    name: 'Personal',
    color: 'rgba(168, 85, 247, 1)', // Purple - Solid for left border
    backgroundColor: 'rgba(168, 85, 247, 0.15)', // Purple - Transparent for badge
    borderColor: 'rgba(168, 85, 247, 0.3)',
    textColor: 'rgba(196, 181, 253, 1)',
    glowColor: 'rgba(168, 85, 247, 0.3)',
    keywords: ['birthday', 'anniversary', 'family', 'personal', 'celebration', 'party', 'dinner', 'lunch', 'date', 'vacation', 'holiday', 'social', 'friend', 'visit']
  },
  WORK: {
    id: 'work', 
    name: 'Work',
    color: 'rgba(59, 130, 246, 1)', // Blue - Solid for left border
    backgroundColor: 'rgba(59, 130, 246, 0.15)', // Blue - Transparent for badge
    borderColor: 'rgba(59, 130, 246, 0.3)',
    textColor: 'rgba(147, 197, 253, 1)',
    glowColor: 'rgba(59, 130, 246, 0.3)',
    keywords: ['meeting', 'conference', 'project', 'deadline', 'presentation', 'interview', 'work', 'office', 'client', 'team', 'standup', 'review', 'boss', 'call', 'zoom']
  },
  APPOINTMENTS: {
    id: 'appointments',
    name: 'Appointments', 
    color: 'rgba(20, 184, 166, 1)', // Teal - Solid for left border
    backgroundColor: 'rgba(20, 184, 166, 0.15)', // Teal - Transparent for badge
    borderColor: 'rgba(20, 184, 166, 0.3)',
    textColor: 'rgba(153, 246, 228, 1)',
    glowColor: 'rgba(20, 184, 166, 0.3)',
    keywords: ['doctor', 'dentist', 'appointment', 'checkup', 'medical', 'hospital', 'clinic', 'therapy', 'consultation', 'salon', 'haircut', 'massage', 'dermat', 'dermatologist']
  },
  REGULAR_ACTIVITIES: {
    id: 'regular_activities',
    name: 'Activities',
    color: 'rgba(245, 158, 11, 1)', // Amber - Solid for left border  
    backgroundColor: 'rgba(245, 158, 11, 0.15)', // Amber - Transparent for badge
    borderColor: 'rgba(245, 158, 11, 0.3)',
    textColor: 'rgba(253, 230, 138, 1)',
    glowColor: 'rgba(245, 158, 11, 0.3)',
    keywords: ['gym', 'workout', 'exercise', 'yoga', 'run', 'fitness', 'sport', 'training', 'class', 'lesson', 'practice', 'activity', 'swimming', 'cycling']
  },
  REMINDERS: {
    id: 'reminders',
    name: 'Reminders',
    color: 'rgba(34, 197, 94, 1)', // Green - Solid for left border
    backgroundColor: 'rgba(34, 197, 94, 0.15)', // Green - Transparent for badge
    borderColor: 'rgba(34, 197, 94, 0.3)', 
    textColor: 'rgba(134, 239, 172, 1)',
    glowColor: 'rgba(34, 197, 94, 0.3)',
    keywords: ['reminder', 'meds', 'medication', 'call', 'email', 'pay', 'bill', 'pickup', 'buy', 'remember', 'task', 'todo', 'remind me']
  }
};

// Fallback category - always use PERSONAL (purple) instead of grey
export const DEFAULT_CATEGORY = EVENT_CATEGORIES.PERSONAL;

// Advanced natural language processing for event extraction - ENHANCED
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
    
    // Extract and parse date with enhanced logic
    const dateInfo = extractDateAdvanced(text);
    if (dateInfo.date) {
      eventData.date = dateInfo.date;
      eventData.confidence += 0.4;
    } else {
      // DEFAULT TO TODAY if no date specified
      const now = getCurrentInUserTimezone();
      eventData.date = format(now, 'yyyy-MM-dd');
      eventData.confidence += 0.2; // Lower confidence for default
    }
    
    // Extract time with enhanced logic
    const timeInfo = extractTimeAdvanced(text, eventData.date);
    if (timeInfo.time) {
      eventData.time = timeInfo.time;
      eventData.confidence += 0.3;
      // If time has passed today and no explicit date, move to tomorrow
      if (timeInfo.movedToTomorrow) {
        const tomorrow = addDays(getCurrentInUserTimezone(), 1);
        eventData.date = format(tomorrow, 'yyyy-MM-dd');
      }
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
  cleanText = cleanText.replace(/\b(morning|afternoon|evening|night|noon|midnight|tonight|today|tomorrow)\b/gi, '');
  
  // Remove date patterns
  cleanText = cleanText.replace(/\b(next week|this week|next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b/gi, '');
  cleanText = cleanText.replace(/\b(\d{1,2}\/\d{1,2}\/?\d{0,4})\b/g, '');
  cleanText = cleanText.replace(/\b(\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec))\b/gi, '');
  
  // Remove common scheduling words
  cleanText = cleanText.replace(/\b(i have|schedule|book|appointment|meeting|remind me to)\b/gi, '');
  cleanText = cleanText.replace(/\b(at|on|for)\s*$/gi, '');
  
  // Clean up and capitalize
  cleanText = cleanText.trim().replace(/\s+/g, ' ');
  
  if (cleanText.length > 0) {
    return cleanText.charAt(0).toUpperCase() + cleanText.slice(1);
  }
  
  return 'Event';
};

// ENHANCED date extraction with sophisticated natural language processing
const extractDateAdvanced = (text) => {
  const now = getCurrentInUserTimezone();
  
  // TODAY variations
  if (text.match(/\b(today|this morning|this afternoon|this evening|tonight|later today)\b/i)) {
    return { date: format(now, 'yyyy-MM-dd'), confidence: 0.9 };
  }
  
  // TOMORROW variations  
  if (text.match(/\b(tomorrow|tomorrow morning|tomorrow afternoon|tomorrow evening|tomorrow night)\b/i)) {
    return { date: format(addDays(now, 1), 'yyyy-MM-dd'), confidence: 0.9 };
  }
  
  // DAY AFTER TOMORROW
  if (text.match(/\b(day after tomorrow|the day after tomorrow)\b/i)) {
    return { date: format(addDays(now, 2), 'yyyy-MM-dd'), confidence: 0.9 };
  }
  
  // THIS WEEK + weekday (this Friday, this Monday, etc.)
  const thisWeekdayMatch = text.match(/\bthis\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b/i);
  if (thisWeekdayMatch) {
    const targetDay = thisWeekdayMatch[1].toLowerCase();
    const targetDate = getThisWeekday(now, targetDay);
    return { date: format(targetDate, 'yyyy-MM-dd'), confidence: 0.85 };
  }
  
  // NEXT WEEK + weekday (next Friday, next Monday, etc.)
  const nextWeekdayMatch = text.match(/\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b/i);
  if (nextWeekdayMatch) {
    const targetDay = nextWeekdayMatch[1].toLowerCase();
    const targetDate = getNextWeekday(now, targetDay);
    return { date: format(targetDate, 'yyyy-MM-dd'), confidence: 0.85 };
  }
  
  // NEXT WEEK (general)
  if (text.match(/\bnext week\b/i)) {
    return { date: format(addWeeks(now, 1), 'yyyy-MM-dd'), confidence: 0.7 };
  }
  
  // IN X HOURS/MINUTES (calculate from current time)
  const inHoursMatch = text.match(/\bin\s+(\d+)\s+hours?\b/i);
  if (inHoursMatch) {
    const hours = parseInt(inHoursMatch[1]);
    const futureTime = addHours(now, hours);
    return { date: format(futureTime, 'yyyy-MM-dd'), confidence: 0.8 };
  }
  
  const inMinutesMatch = text.match(/\bin\s+(\d+)\s+minutes?\b/i);
  if (inMinutesMatch) {
    const minutes = parseInt(inMinutesMatch[1]);
    const futureTime = addMinutes(now, minutes);
    return { date: format(futureTime, 'yyyy-MM-dd'), confidence: 0.8 };
  }
  
  // SPECIFIC DATE FORMATS (MM/DD, MM/DD/YYYY, Dec 25, etc.)
  const dateMatch = text.match(/\b(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?\b/);
  if (dateMatch) {
    try {
      const month = parseInt(dateMatch[1]);
      const day = parseInt(dateMatch[2]);
      const year = dateMatch[3] ? parseInt(dateMatch[3]) : now.getFullYear();
      
      // Handle 2-digit years
      const fullYear = year < 100 ? (year < 50 ? 2000 + year : 1900 + year) : year;
      
      if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
        const dateStr = `${fullYear}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
        return { date: dateStr, confidence: 0.8 };
      }
    } catch (error) {
      console.warn('Error parsing date:', error);
    }
  }
  
  // MONTH DAY format (Aug 27, 27 Aug, December 15, etc.)
  const monthDayMatch = text.match(/\b(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december)\b/i);
  if (monthDayMatch) {
    try {
      const day = parseInt(monthDayMatch[1]);
      const monthStr = monthDayMatch[2].toLowerCase();
      const month = getMonthNumber(monthStr.substring(0, 3));
      const year = now.getFullYear();
      
      const dateStr = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
      return { date: dateStr, confidence: 0.8 };
    } catch (error) {
      console.warn('Error parsing month/day:', error);
    }
  }
  
  return { date: null, confidence: 0 };
};

// ENHANCED time extraction with sophistication - FIXED
const extractTimeAdvanced = (text, eventDate) => {
  const now = getCurrentInUserTimezone();
  const isToday = eventDate === format(now, 'yyyy-MM-dd');
  
  console.log('🔍 Time parsing debug:', { text, eventDate, isToday });
  
  // SPECIFIC TIME FORMATS - IMPROVED REGEX (3:30 PM, 15:30, 3pm, 9pm, etc.)
  const timeMatch = text.match(/\b(\d{1,2})(?::(\d{2}))?\s*?(am|pm|AM|PM)\b/i);
  if (timeMatch) {
    let hours = parseInt(timeMatch[1]);
    const minutes = timeMatch[2] ? parseInt(timeMatch[2]) : 0;
    const ampm = timeMatch[3] ? timeMatch[3].toLowerCase() : null;
    
    console.log('🔍 Time match found:', { hours, minutes, ampm, rawMatch: timeMatch[0] });
    
    // Convert to 24-hour format
    if (ampm === 'pm' && hours !== 12) {
      hours += 12;
    }
    if (ampm === 'am' && hours === 12) {
      hours = 0;
    }
    
    const timeStr = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    console.log('🔍 Converted time:', timeStr);
    
    // Check if time has passed today
    const movedToTomorrow = isToday && checkIfTimePassed(timeStr);
    
    return { time: timeStr, confidence: 0.9, movedToTomorrow };
  }
  
  // ALTERNATIVE: Look for time with "at" keyword specifically (at 9pm, at 3:30, etc.)
  const atTimeMatch = text.match(/\bat\s+(\d{1,2})(?::(\d{2}))?\s*?(am|pm|AM|PM)\b/i);
  if (atTimeMatch) {
    let hours = parseInt(atTimeMatch[1]);
    const minutes = atTimeMatch[2] ? parseInt(atTimeMatch[2]) : 0;
    const ampm = atTimeMatch[3] ? atTimeMatch[3].toLowerCase() : null;
    
    console.log('🔍 "At" time match found:', { hours, minutes, ampm, rawMatch: atTimeMatch[0] });
    
    // Convert to 24-hour format
    if (ampm === 'pm' && hours !== 12) {
      hours += 12;
    }
    if (ampm === 'am' && hours === 12) {
      hours = 0;
    }
    
    const timeStr = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    console.log('🔍 Converted "at" time:', timeStr);
    
    // Check if time has passed today
    const movedToTomorrow = isToday && checkIfTimePassed(timeStr);
    
    return { time: timeStr, confidence: 0.95, movedToTomorrow };
  }
  
  // 24-hour format (15:30, 09:45)
  const time24Match = text.match(/\b(\d{1,2}):(\d{2})\b/);
  if (time24Match) {
    const hours = parseInt(time24Match[1]);
    const minutes = parseInt(time24Match[2]);
    
    if (hours >= 0 && hours <= 23 && minutes >= 0 && minutes <= 59) {
      const timeStr = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
      const movedToTomorrow = isToday && checkIfTimePassed(timeStr);
      
      console.log('🔍 24-hour time found:', timeStr);
      
      return { time: timeStr, confidence: 0.8, movedToTomorrow };
    }
  }
  
  // RELATIVE TIME PHRASES
  const timeKeywords = {
    'morning': '09:00',
    'this morning': '09:00', 
    'noon': '12:00',
    'lunch': '12:00',
    'afternoon': '14:00',
    'this afternoon': '14:00',
    'evening': '18:00', 
    'this evening': '18:00',
    'tonight': '19:00',
    'night': '20:00',
    'midnight': '00:00'
  };
  
  for (const [keyword, time] of Object.entries(timeKeywords)) {
    if (text.includes(keyword)) {
      const movedToTomorrow = isToday && checkIfTimePassed(time);
      console.log('🔍 Keyword time found:', { keyword, time });
      return { time, confidence: 0.6, movedToTomorrow };
    }
  }
  
  console.log('🔍 No time found, using default 12:00');
  return { time: null, confidence: 0, movedToTomorrow: false };
};

// Categorize event based on keywords - ALWAYS returns valid category, never null/grey
const categorizeEvent = (text) => {
  let bestMatch = DEFAULT_CATEGORY.id; // Fallback to Personal (purple) instead of grey
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
      bestMatch = category.id;
    }
  }
  
  return bestMatch;
};

// Helper function to get this week's occurrence of a weekday
const getThisWeekday = (date, targetDay) => {
  const days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
  const currentDay = date.getDay();
  const targetIndex = days.indexOf(targetDay.toLowerCase());
  
  let daysToAdd = targetIndex - currentDay;
  if (daysToAdd < 0) daysToAdd += 7; // This week or next week if day has passed
  
  return addDays(date, daysToAdd);
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

// Helper function to check if a time has already passed today
const checkIfTimePassed = (timeStr) => {
  const now = getCurrentInUserTimezone();
  const currentTime = format(now, 'HH:mm');
  return timeStr < currentTime;
};

// Enhanced event message detection with more keywords
export const isEventMessage = (message) => {
  const text = message.toLowerCase();
  
  // Enhanced event indicators
  const eventIndicators = [
    'meeting', 'appointment', 'schedule', 'book', 'i have',
    'tomorrow', 'today', 'tonight', 'next week', 'next', 'at', 'pm', 'am',
    'doctor', 'dentist', 'gym', 'workout', 'lunch', 'dinner',
    'birthday', 'anniversary', 'remind me', 'reminder',
    'call', 'visit', 'party', 'celebration', 'conference'
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
    case 'regular_activities':
      return [
        { time: 4 * 60, label: '4 hours before' },
        { time: 30, label: '30 minutes before' }
      ];
    default:
      return baseReminders;
  }
};
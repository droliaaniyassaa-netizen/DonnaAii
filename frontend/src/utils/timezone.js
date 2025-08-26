// Timezone utilities for Donna
import { formatInTimeZone, zonedTimeToUtc, utcToZonedTime } from 'date-fns-tz';
import { isValid, parseISO } from 'date-fns';

// Get system timezone
export const getSystemTimezone = () => {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
};

// Get user's preferred timezone from localStorage or default to system
export const getUserTimezone = () => {
  const stored = localStorage.getItem('donna_timezone');
  return stored || getSystemTimezone();
};

// Save user's timezone preference
export const saveUserTimezone = (timezone) => {
  localStorage.setItem('donna_timezone', timezone);
};

// Convert local datetime to UTC for storage
export const toUTC = (dateTime, timezone = null) => {
  const userTz = timezone || getUserTimezone();
  
  if (!dateTime) return null;
  
  // If it's already a Date object
  if (dateTime instanceof Date) {
    return zonedTimeToUtc(dateTime, userTz);
  }
  
  // If it's a string, parse it first
  try {
    const parsed = parseISO(dateTime);
    if (isValid(parsed)) {
      return zonedTimeToUtc(parsed, userTz);
    }
  } catch (error) {
    console.warn('Failed to parse datetime:', dateTime, error);
  }
  
  return null;
};

// Convert UTC datetime to user's timezone for display
export const fromUTC = (utcDateTime, timezone = null) => {
  const userTz = timezone || getUserTimezone();
  
  if (!utcDateTime) return null;
  
  try {
    // Handle different input formats
    let date;
    if (utcDateTime instanceof Date) {
      date = utcDateTime;
    } else if (typeof utcDateTime === 'string') {
      date = parseISO(utcDateTime);
    } else {
      return null;
    }
    
    if (!isValid(date)) return null;
    
    return utcToZonedTime(date, userTz);
  } catch (error) {
    console.warn('Failed to convert from UTC:', utcDateTime, error);
    return null;
  }
};

// Format datetime in user's timezone
export const formatInUserTimezone = (utcDateTime, formatString = 'yyyy-MM-dd HH:mm', timezone = null) => {
  const userTz = timezone || getUserTimezone();
  
  if (!utcDateTime) return '';
  
  try {
    let date;
    if (utcDateTime instanceof Date) {
      date = utcDateTime;
    } else if (typeof utcDateTime === 'string') {
      date = parseISO(utcDateTime);
    } else {
      return '';
    }
    
    if (!isValid(date)) return '';
    
    return formatInTimeZone(date, userTz, formatString);
  } catch (error) {
    console.warn('Failed to format datetime:', utcDateTime, error);
    return '';
  }
};

// Get current datetime in user's timezone
export const getCurrentInUserTimezone = (timezone = null) => {
  const userTz = timezone || getUserTimezone();
  return utcToZonedTime(new Date(), userTz);
};

// Combine date and time inputs into a UTC datetime
export const combineDateTimeToUTC = (dateStr, timeStr, timezone = null) => {
  const userTz = timezone || getUserTimezone();
  
  if (!dateStr || !timeStr) return null;
  
  try {
    // Create datetime string in local timezone
    const dateTimeStr = `${dateStr}T${timeStr}`;
    const localDate = parseISO(dateTimeStr);
    
    if (!isValid(localDate)) return null;
    
    // Convert to UTC
    return zonedTimeToUtc(localDate, userTz);
  } catch (error) {
    console.warn('Failed to combine date/time:', { dateStr, timeStr }, error);
    return null;
  }
};

// Split UTC datetime into separate date and time strings for inputs
export const splitUTCDateTime = (utcDateTime, timezone = null) => {
  const userTz = timezone || getUserTimezone();
  
  if (!utcDateTime) return { date: '', time: '' };
  
  try {
    let date;
    if (utcDateTime instanceof Date) {
      date = utcDateTime;
    } else if (typeof utcDateTime === 'string') {
      date = parseISO(utcDateTime);
    } else {
      return { date: '', time: '' };
    }
    
    if (!isValid(date)) return { date: '', time: '' };
    
    return {
      date: formatInTimeZone(date, userTz, 'yyyy-MM-dd'),
      time: formatInTimeZone(date, userTz, 'HH:mm')
    };
  } catch (error) {
    console.warn('Failed to split datetime:', utcDateTime, error);
    return { date: '', time: '' };
  }
};

// Get timezone display name
export const getTimezoneDisplayName = (timezone = null) => {
  const tz = timezone || getUserTimezone();
  
  try {
    const now = new Date();
    const formatter = new Intl.DateTimeFormat('en-US', {
      timeZone: tz,
      timeZoneName: 'short'
    });
    
    const parts = formatter.formatToParts(now);
    const timeZoneName = parts.find(part => part.type === 'timeZoneName')?.value;
    
    // Return both timezone ID and short name
    return {
      id: tz,
      name: timeZoneName || tz,
      display: `${tz.replace(/_/g, ' ')} (${timeZoneName || 'Local'})`
    };
  } catch (error) {
    console.warn('Failed to get timezone display name:', tz, error);
    return {
      id: tz,
      name: tz,
      display: tz.replace(/_/g, ' ')
    };
  }
};

// Handle DST transitions gracefully
export const handleDSTTransition = (dateStr, timeStr, timezone = null) => {
  const userTz = timezone || getUserTimezone();
  
  try {
    const utcDate = combineDateTimeToUTC(dateStr, timeStr, userTz);
    
    if (!utcDate) {
      // If parsing failed, might be in DST gap
      console.warn('Time may be in DST transition gap:', { dateStr, timeStr });
      
      // Try moving forward by 1 hour as fallback
      const [hours, minutes] = timeStr.split(':');
      const adjustedHours = String((parseInt(hours) + 1) % 24).padStart(2, '0');
      const adjustedTime = `${adjustedHours}:${minutes}`;
      
      return combineDateTimeToUTC(dateStr, adjustedTime, userTz);
    }
    
    return utcDate;
  } catch (error) {
    console.warn('DST handling error:', error);
    return null;
  }
};

// Common timezone list for selector
export const COMMON_TIMEZONES = [
  'America/New_York',
  'America/Chicago', 
  'America/Denver',
  'America/Los_Angeles',
  'America/Toronto',
  'America/Vancouver',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Europe/Rome',
  'Europe/Madrid',
  'Europe/Amsterdam',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Asia/Hong_Kong',
  'Asia/Singapore',
  'Asia/Mumbai',
  'Asia/Dubai',
  'Australia/Sydney',
  'Australia/Melbourne',
  'Pacific/Auckland',
  'America/Sao_Paulo',
  'America/Mexico_City',
  'Africa/Cairo',
  'Africa/Johannesburg'
];

// Get all available timezones (comprehensive list)
export const getAllTimezones = () => {
  try {
    // Get all IANA timezone identifiers
    const timezones = Intl.supportedValuesOf('timeZone');
    return timezones.sort();
  } catch (error) {
    // Fallback to common timezones if not supported
    console.warn('Full timezone list not supported, using common timezones');
    return COMMON_TIMEZONES.sort();
  }
};
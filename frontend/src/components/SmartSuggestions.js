import React, { useState, useMemo, useEffect } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Clock, X, Calendar, Sparkles, Eye, EyeOff, Plus } from 'lucide-react';
import { EVENT_CATEGORIES } from '../utils/eventProcessing';

// Smart Suggestions - Donna's Intelligent Calendar Assistant
const SmartSuggestions = ({ events, onRescheduleEvent, onDeleteEvent, onRefreshEvents, newEvent, setNewEvent, onCreateEvent, className = "" }) => {
  const [showInsights, setShowInsights] = useState(true);
  const [dismissedSuggestions, setDismissedSuggestions] = useState(new Set());
  const [selectedSuggestion, setSelectedSuggestion] = useState(null);
  const [showSlotsModal, setShowSlotsModal] = useState(false);
  const [userSettings, setUserSettings] = useState({ weekend_mode: 'relaxed' });
  const [showEventCreation, setShowEventCreation] = useState(false);

  // Load user settings on mount
  useEffect(() => {
    const loadUserSettings = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/user/settings/default`);
        if (response.ok) {
          const settings = await response.json();
          setUserSettings(settings);
        }
      } catch (error) {
        console.error('Failed to load user settings:', error);
      }
    };
    
    loadUserSettings();
  }, []);

  // Telemetry logging helper
  const logTelemetry = async (eventType, suggestionType, suggestionId, action = null, metadata = {}, latencyMs = null) => {
    try {
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/telemetry/log`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: 'default', // TODO: Use actual session ID from app context
          event_type: eventType,
          suggestion_type: suggestionType,
          suggestion_id: suggestionId,
          action,
          metadata,
          latency_ms: latencyMs
        })
      });
    } catch (error) {
      console.error('Failed to log telemetry:', error);
    }
  };

  // Helper: Check if event is a "real" event (not reminder)
  const isRealEvent = (event) => {
    const title = event.title?.toLowerCase() || '';
    const category = event.category?.toLowerCase() || '';
    
    // Exclude reminders and holidays
    if (category === 'reminders') return false;
    if (title.includes('reminder') || title.includes('note') || 
        title.includes('to-do') || title.includes('checklist')) return false;
    
    return true;
  };

  // Helper: Check if event is flexible (can be rescheduled)
  const isFlexibleEvent = (event) => {
    const title = event.title?.toLowerCase() || '';
    const category = event.category?.toLowerCase() || '';
    
    // Flexible categories and keywords
    const flexibleKeywords = [
      'gym', 'workout', 'yoga', 'exercise', 'fitness',
      'reading', 'walk', 'chores', 'coffee', 'meditation',
      'personal', 'hobby', 'shopping', 'errands'
    ];
    
    return flexibleKeywords.some(keyword => 
      title.includes(keyword) || category === 'regular_activities'
    );
  };

  // Helper: Get day window based on weekday/weekend and user preference
  const getDayWindow = (date) => {
    const d = new Date(date);
    const isWeekend = [0, 6].includes(d.getDay()); // 0 Sun, 6 Sat
    const start = new Date(d);
    const end = new Date(d);
    
    if (isWeekend) {
      // Weekend hours depend on user's weekend_mode setting
      if (userSettings.weekend_mode === 'active') {
        // Active weekend: earlier start, later end
        start.setHours(7, 0, 0, 0);
        end.setHours(22, 0, 0, 0);
      } else {
        // Relaxed weekend: later start, earlier end
        start.setHours(9, 0, 0, 0);
        end.setHours(19, 0, 0, 0);
      }
    } else {
      // Weekday hours remain the same
      start.setHours(7, 0, 0, 0);
      end.setHours(21, 0, 0, 0);
    }
    
    return { start, end };
  };

  // Helper: Check if time ranges overlap
  const rangesOverlap = (start1, end1, start2, end2) => {
    return start1 < end2 && start2 < end1;
  };

  // Helper: Check if slot is clear with 15-min buffer
  const isSlotClear = (start, end, eventsList) => {
    const padStart = new Date(start.getTime() - 15 * 60000); // 15 min before
    const padEnd = new Date(end.getTime() + 15 * 60000);     // 15 min after
    
    return !eventsList.some(ev => {
      if (!isRealEvent(ev)) return false; // Ignore reminders
      const eventStart = new Date(ev.datetime_utc);
      const eventEnd = new Date(eventStart.getTime() + 60 * 60000); // Assume 60min
      return rangesOverlap(padStart, padEnd, eventStart, eventEnd);
    });
  };

  // Find available slots for rescheduling
  const findAvailableSlots = (candidateEvent, targetDate) => {
    const slots = [];
    const now = new Date();
    
    // Search today's remaining hours
    const today = new Date(targetDate);
    const { start: todayStart, end: todayEnd } = getDayWindow(today);
    
    // Only search from current time if it's today
    const searchStart = new Date(Math.max(
      todayStart.getTime(),
      targetDate.toDateString() === now.toDateString() ? now.getTime() : todayStart.getTime()
    ));

    // Search today - CREATE SLOTS IN LOCAL TIMEZONE
    for (let time = new Date(searchStart); time < todayEnd; time.setMinutes(time.getMinutes() + 30)) {
      const slotEnd = new Date(time.getTime() + 60 * 60000); // 60 min slot
      if (slotEnd <= todayEnd && isSlotClear(time, slotEnd, events)) {
        slots.push({
          start: new Date(time), // Keep in local timezone
          end: new Date(slotEnd), // Keep in local timezone  
          label: `Today ${time.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`
        });
        if (slots.length >= 4) break;
      }
    }

    // Search tomorrow morning if we need more slots
    if (slots.length < 4) {
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);
      const { start: tomorrowStart } = getDayWindow(tomorrow);
      const tomorrowNoon = new Date(tomorrowStart);
      tomorrowNoon.setHours(12, 0, 0, 0);

      for (let time = new Date(tomorrowStart); time < tomorrowNoon; time.setMinutes(time.getMinutes() + 30)) {
        const slotEnd = new Date(time.getTime() + 60 * 60000);
        if (isSlotClear(time, slotEnd, events)) {
          slots.push({
            start: new Date(time), // Keep in local timezone
            end: new Date(slotEnd), // Keep in local timezone
            label: `Tomorrow ${time.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`
          });
          if (slots.length >= 4) break;
        }
      }
    }

    // Search up to 48h ahead if still need slots
    if (slots.length < 4) {
      for (let day = 2; day <= 2 && slots.length < 4; day++) {
        const futureDay = new Date(today);
        futureDay.setDate(futureDay.getDate() + day);
        const { start: dayStart, end: dayEnd } = getDayWindow(futureDay);

        for (let time = new Date(dayStart); time < dayEnd && slots.length < 4; time.setMinutes(time.getMinutes() + 30)) {
          const slotEnd = new Date(time.getTime() + 60 * 60000);
          if (slotEnd <= dayEnd && isSlotClear(time, slotEnd, events)) {
            const dayName = futureDay.toLocaleDateString('en-US', { weekday: 'short' });
            slots.push({
              start: new Date(time), // Keep in local timezone
              end: new Date(slotEnd), // Keep in local timezone
              label: `${dayName} ${time.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`
            });
          }
        }
      }
    }

    return slots.slice(0, 4); // Max 4 slots
  };

  // Helper: Detect dense blocks (3+ events in 5 hours)
  const detectDenseBlock = (dayEvents, checkDate) => {
    if (dayEvents.length < 3) return null;
    
    // Sort events by time
    const sortedEvents = dayEvents
      .map(event => ({
        ...event,
        start: new Date(event.datetime_utc),
        end: new Date(new Date(event.datetime_utc).getTime() + 60 * 60000) // Assume 1 hour duration
      }))
      .sort((a, b) => a.start - b.start);
    
    // Check for 3+ events within any rolling 5-hour window
    for (let i = 0; i <= sortedEvents.length - 3; i++) {
      for (let j = i + 2; j < sortedEvents.length; j++) {
        const firstEvent = sortedEvents[i];
        const lastEvent = sortedEvents[j];
        const timeSpan = (lastEvent.end - firstEvent.start) / (1000 * 60 * 60); // hours
        
        if (timeSpan <= 5) {
          // Count how many events are in this window
          const eventsInWindow = sortedEvents.filter(event => 
            event.start >= firstEvent.start && event.end <= lastEvent.end
          );
          
          if (eventsInWindow.length >= 3) {
            return {
              events: eventsInWindow,
              eventCount: eventsInWindow.length,
              timeSpan: `${Math.round(timeSpan * 10) / 10}h`,
              startTime: firstEvent.start,
              endTime: lastEvent.end
            };
          }
        }
      }
    }
    
    return null;
  };

  // Get Donna's sassy nudge messages for dense blocks
  const getDenseBlockMessage = (eventCount, timeSpan) => {
    const messages = [
      "Three back-to-backs? Carry a small snack! A protein bar, a sandwich and an energy drink. You'll thank me later.",
      `${eventCount} events in ${timeSpan}? That's ambitious. Pack some water and maybe a phone charger.`,
      "Packed schedule today. Quick tip: use bathroom breaks strategically.",
      "Dense day ahead. Consider prepping snacks and staying hydrated between meetings.",
      `${eventCount} events back-to-back? Bold move. Don't forget to eat something.`
    ];
    
    // Return a message based on event count or random selection
    if (eventCount === 3) {
      return messages[0]; // Signature "Three back-to-backs" message
    }
    
    return messages[Math.min(eventCount - 2, messages.length - 1)] || messages[1];
  };

  // Detect overbooked days and dense blocks, generate suggestions
  const suggestions = useMemo(() => {
    const suggestionsMap = new Map();
    const today = new Date();
    
    // Check next 3 days (72 hours ahead) for overbooked
    for (let i = 0; i < 3; i++) {
      const checkDate = new Date(today);
      checkDate.setDate(today.getDate() + i);
      const dateStr = checkDate.toDateString();
      
      // Skip if already dismissed
      if (dismissedSuggestions.has(dateStr)) continue;
      
      // Get events for this day
      const dayEvents = events.filter(event => {
        const eventDate = new Date(event.datetime_utc);
        return eventDate.toDateString() === dateStr && isRealEvent(event);
      });
      
      // Check for dense blocks (3+ events in 5 hours) - only on day of, after 6am
      const isToday = checkDate.toDateString() === today.toDateString();
      const isAfter6AM = today.getHours() >= 6;
      
      if (isToday && isAfter6AM && dayEvents.length >= 3) {
        const denseBlock = detectDenseBlock(dayEvents, checkDate);
        if (denseBlock && !dismissedSuggestions.has(`dense_${dateStr}`)) {
          const displayDayName = 'Today';
          const suggestionId = `dense_suggestion_${dateStr}`;
          
          suggestionsMap.set(`dense_${dateStr}`, {
            id: suggestionId,
            type: 'dense_block',
            date: checkDate,
            dayName: displayDayName,
            eventCount: denseBlock.events.length,
            timeSpan: denseBlock.timeSpan,
            suggestionType: 'dense_nudge'
          });

          // Log impression telemetry for dense block
          logTelemetry('impression', 'dense_block', suggestionId, null, {
            event_count: denseBlock.events.length,
            time_span: denseBlock.timeSpan,
            day: displayDayName
          });
        }
      }
      
      // Check if overbooked (6+ real events) for rescheduling suggestions
      if (dayEvents.length >= 6) {
        // Find flexible events (prefer non-gym first)
        const flexibleEvents = dayEvents.filter(isFlexibleEvent);
        const gymEvents = flexibleEvents.filter(e => {
          const title = e.title?.toLowerCase() || '';
          return title.includes('gym') || title.includes('workout') || title.includes('yoga');
        });
        const nonGymFlexible = flexibleEvents.filter(e => !gymEvents.includes(e));
        
        let candidateEvent = null;
        let suggestionType = 'reschedule';
        
        if (nonGymFlexible.length > 0) {
          candidateEvent = nonGymFlexible[0]; // Pick first non-gym flexible
        } else if (gymEvents.length > 0) {
          candidateEvent = gymEvents[0]; // Fallback to gym
        } else {
          // No flexible events, ask user to pick
          suggestionType = 'user_pick';
        }
        
        const dayName = checkDate.toLocaleDateString('en-US', { weekday: 'long' });
        const isToday = checkDate.toDateString() === today.toDateString();
        const displayDayName = isToday ? 'Today' : dayName;
        const suggestionId = `suggestion_${dateStr}`;
        
        suggestionsMap.set(dateStr, {
          id: suggestionId,
          type: 'overbooked',
          date: checkDate,
          dayName: displayDayName,
          eventCount: dayEvents.length,
          candidateEvent,
          suggestionType,
          availableSlots: candidateEvent ? findAvailableSlots(candidateEvent, checkDate) : []
        });

        // Log impression telemetry for overbooked day
        logTelemetry('impression', 'overbooked', suggestionId, null, {
          event_count: dayEvents.length,
          has_flexible_events: flexibleEvents.length > 0,
          suggestion_type: suggestionType,
          day: displayDayName
        });
      }
    }
    
    return Array.from(suggestionsMap.values());
  }, [events, dismissedSuggestions, userSettings]);

  // Handle dismissing a suggestion
  const handleDismiss = (suggestion) => {
    const startTime = performance.now();
    
    if (suggestion.type === 'dense_block') {
      setDismissedSuggestions(prev => new Set([...prev, `dense_${suggestion.date.toDateString()}`]));
    } else {
      setDismissedSuggestions(prev => new Set([...prev, suggestion.date.toDateString()]));
    }

    // Log dismiss telemetry
    const latency = Math.round(performance.now() - startTime);
    logTelemetry(
      'dismiss', 
      suggestion.type, 
      suggestion.id, 
      'dismiss',
      { 
        suggestion_type: suggestion.suggestionType,
        day: suggestion.dayName 
      },
      latency
    );
  };

  // Handle showing slots modal
  const handleShowSlots = (suggestion) => {
    setSelectedSuggestion(suggestion);
    setShowSlotsModal(true);
  };

  // Handle rescheduling to a slot
  const handleRescheduleToSlot = async (slot) => {
    if (!selectedSuggestion?.candidateEvent) return;
    
    const startTime = performance.now();
    
    try {
      // Delete the old event first
      await onDeleteEvent(selectedSuggestion.candidateEvent.id);
      
      // Create new event at the new time - KEEP LOCAL TIME, DON'T DOUBLE CONVERT
      const newEvent = {
        title: selectedSuggestion.candidateEvent.title,
        description: selectedSuggestion.candidateEvent.description || '',
        category: selectedSuggestion.candidateEvent.category,
        datetime_utc: slot.start.toISOString(), // slot.start is already in correct timezone
        reminder: selectedSuggestion.candidateEvent.reminder || true
      };
      
      // Create the new event
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/calendar/events`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newEvent)
      });
      
      if (response.ok) {
        // Close modal and dismiss suggestion
        setShowSlotsModal(false);
        handleDismiss(selectedSuggestion);
        setSelectedSuggestion(null);
        
        console.log(`✅ Successfully rescheduled ${newEvent.title} to ${slot.label}`);
        
        // Log successful reschedule telemetry
        const latency = Math.round(performance.now() - startTime);
        logTelemetry(
          'action_success',
          selectedSuggestion.type,
          selectedSuggestion.id,
          'reschedule',
          {
            event_title: newEvent.title,
            new_slot: slot.label,
            old_time: selectedSuggestion.candidateEvent.datetime_utc,
            new_time: slot.start.toISOString()
          },
          latency
        );
        
        // Refresh events without page reload
        if (onRefreshEvents) {
          onRefreshEvents();
        }
        
      } else {
        throw new Error('Failed to create rescheduled event');
      }
      
    } catch (error) {
      console.error('Failed to reschedule event:', error);
      
      // Log failed reschedule telemetry
      const latency = Math.round(performance.now() - startTime);
      logTelemetry(
        'action_failure',
        selectedSuggestion.type,
        selectedSuggestion.id,
        'reschedule',
        {
          error: error.message,
          event_title: selectedSuggestion.candidateEvent.title
        },
        latency
      );
      
      // Show error feedback
      alert('Failed to reschedule event. Please try again.');
    }
  };

  if (!showInsights || suggestions.length === 0) {
    return showInsights ? (
      <div className="insights-toggle">
        <Button
          variant="ghost" 
          size="sm"
          onClick={() => setShowInsights(false)}
          className="hide-insights-btn"
        >
          <EyeOff className="insights-icon" />
          Hide insights
        </Button>
      </div>
    ) : (
      <div className="insights-toggle">
        <Button
          variant="ghost"
          size="sm" 
          onClick={() => setShowInsights(true)}
          className="show-insights-btn"
        >
          <Eye className="insights-icon" />
          Show insights
        </Button>
      </div>
    );
  }

  return (
    <div className={`smart-suggestions-container ${className}`}>
      {/* Insights Header with Schedule Event and Hide Insights */}
      <div className="insights-header">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowEventCreation(true)}
          className="schedule-event-btn"
        >
          <Plus className="insights-icon" />
          Schedule Event
        </Button>
        
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowInsights(false)} 
          className="hide-insights-btn"
        >
          <EyeOff className="insights-icon" />
          Hide insights
        </Button>
      </div>

      {/* Suggestion Cards */}
      {suggestions.map(suggestion => (
        <Card key={suggestion.id} className="smart-suggestion-card">
          <CardContent className="suggestion-content">
            {/* Donna's signature sparkle */}
            <Sparkles className="donna-signature" />
            
            <div className="suggestion-main">
              <div className="suggestion-message">
                {suggestion.suggestionType === 'dense_nudge' ? (
                  <span>
                    {getDenseBlockMessage(suggestion.eventCount, suggestion.timeSpan)}
                  </span>
                ) : suggestion.suggestionType === 'user_pick' ? (
                  <span>
                    {suggestion.dayName} seems overbooked! Pick an event you're flexible with, 
                    and I'll find optional slots to reschedule it.
                  </span>
                ) : (
                  <span>
                    {suggestion.dayName} looks overbooked! Want me to move "{suggestion.candidateEvent?.title}" 
                    for you? I've found {suggestion.availableSlots.length} free slots.
                  </span>
                )}
              </div>
              
              <div className="suggestion-actions">
                {suggestion.suggestionType === 'dense_nudge' ? (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDismiss(suggestion)}
                    className="action-btn dismiss"
                  >
                    Got it
                  </Button>
                ) : suggestion.suggestionType === 'user_pick' ? (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleShowSlots(suggestion)}
                      className="action-btn primary"
                    >
                      Pick event
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDismiss(suggestion)}
                      className="action-btn dismiss"
                    >
                      Keep as is
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      variant="outline" 
                      size="sm"
                      onClick={() => handleShowSlots(suggestion)}
                      className="action-btn primary"
                    >
                      <Clock className="action-icon" />
                      See slots
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDismiss(suggestion)}
                      className="action-btn dismiss"
                    >
                      Keep as is
                    </Button>
                  </>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Slots Modal */}
      {showSlotsModal && selectedSuggestion && (
        <div className="slots-modal-overlay" onClick={() => setShowSlotsModal(false)}>
          <div className="slots-modal-content" onClick={(e) => e.stopPropagation()}>
            <Card className="slots-modal-card">
              <CardContent className="slots-modal-body">
                <div className="modal-header">
                  <h3 className="modal-title">
                    {selectedSuggestion.suggestionType === 'user_pick' ? 
                      'Pick an event to reschedule' : 
                      `Reschedule "${selectedSuggestion.candidateEvent?.title}"`
                    }
                  </h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowSlotsModal(false)}
                    className="close-modal-btn"
                  >
                    <X className="close-icon" />
                  </Button>
                </div>
                
                <div className="available-slots">
                  {selectedSuggestion.availableSlots.map((slot, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      onClick={() => handleRescheduleToSlot(slot)}
                      className="slot-btn"
                    >
                      <Calendar className="slot-icon" />
                      <span className="slot-time">
                        {slot.label} - {slot.end.toLocaleTimeString('en-US', { 
                          hour: 'numeric', 
                          minute: '2-digit' 
                        })}
                      </span>
                    </Button>
                  ))}
                  
                  {selectedSuggestion.availableSlots.length === 0 && (
                    <div className="no-slots">
                      <p>No free slots found. Consider:</p>
                      <Button variant="outline" className="slot-btn">Cancel event</Button>
                      <Button variant="outline" className="slot-btn">Double-book anyway</Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default SmartSuggestions;
import React, { useState, useMemo, useEffect } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Clock, X, Calendar, Sparkles, Eye, EyeOff } from 'lucide-react';

// Smart Suggestions - Donna's Intelligent Calendar Assistant
const SmartSuggestions = ({ events, onRescheduleEvent, onDeleteEvent, className = "" }) => {
  const [showInsights, setShowInsights] = useState(true);
  const [dismissedSuggestions, setDismissedSuggestions] = useState(new Set());
  const [selectedSuggestion, setSelectedSuggestion] = useState(null);
  const [showSlotsModal, setShowSlotsModal] = useState(false);

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

  // Helper: Get day window based on weekday/weekend
  const getDayWindow = (date) => {
    const d = new Date(date);
    const isWeekend = [0, 6].includes(d.getDay()); // 0 Sun, 6 Sat
    const start = new Date(d);
    const end = new Date(d);
    
    if (isWeekend) {
      start.setHours(8, 0, 0, 0);
      end.setHours(20, 0, 0, 0);
    } else {
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

    // Search today
    for (let time = new Date(searchStart); time < todayEnd; time.setMinutes(time.getMinutes() + 30)) {
      const slotEnd = new Date(time.getTime() + 60 * 60000); // 60 min slot
      if (slotEnd <= todayEnd && isSlotClear(time, slotEnd, events)) {
        slots.push({
          start: new Date(time),
          end: new Date(slotEnd),
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
            start: new Date(time),
            end: new Date(slotEnd),
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
              start: new Date(time),
              end: new Date(slotEnd),
              label: `${dayName} ${time.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`
            });
          }
        }
      }
    }

    return slots.slice(0, 4); // Max 4 slots
  };

  // Detect overbooked days and generate suggestions
  const suggestions = useMemo(() => {
    const suggestionsMap = new Map();
    const today = new Date();
    
    // Check next 3 days (72 hours ahead)
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
      
      // Check if overbooked (6+ real events)
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
        
        suggestionsMap.set(dateStr, {
          id: `suggestion_${dateStr}`,
          date: checkDate,
          dayName: displayDayName,
          eventCount: dayEvents.length,
          candidateEvent,
          suggestionType,
          availableSlots: candidateEvent ? findAvailableSlots(candidateEvent, checkDate) : []
        });
      }
    }
    
    return Array.from(suggestionsMap.values());
  }, [events, dismissedSuggestions]);

  // Handle dismissing a suggestion
  const handleDismiss = (suggestion) => {
    setDismissedSuggestions(prev => new Set([...prev, suggestion.date.toDateString()]));
  };

  // Handle showing slots modal
  const handleShowSlots = (suggestion) => {
    setSelectedSuggestion(suggestion);
    setShowSlotsModal(true);
  };

  // Handle rescheduling to a slot
  const handleRescheduleToSlot = async (slot) => {
    if (!selectedSuggestion?.candidateEvent) return;
    
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
        
        // NO PAGE RELOAD - let React update naturally
        // The parent component will refresh events automatically
        
      } else {
        throw new Error('Failed to create rescheduled event');
      }
      
    } catch (error) {
      console.error('Failed to reschedule event:', error);
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
      {/* Insights Toggle */}
      <div className="insights-header">
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
                {suggestion.suggestionType === 'user_pick' ? (
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
                {suggestion.suggestionType === 'user_pick' ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleShowSlots(suggestion)}
                    className="action-btn primary"
                  >
                    Pick event
                  </Button>
                ) : (
                  <Button
                    variant="outline" 
                    size="sm"
                    onClick={() => handleShowSlots(suggestion)}
                    className="action-btn primary"
                  >
                    <Clock className="action-icon" />
                    See slots
                  </Button>
                )}
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDismiss(suggestion)}
                  className="action-btn dismiss"
                >
                  Keep as is
                </Button>
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
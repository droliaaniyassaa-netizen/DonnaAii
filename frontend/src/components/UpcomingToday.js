import React from 'react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Clock, Sunrise, Star } from 'lucide-react';
import { EVENT_CATEGORIES } from '../utils/eventProcessing';
import { formatInUserTimezone, getCurrentInUserTimezone } from '../utils/timezone';
import { isToday, parseISO, isFuture, isPast } from 'date-fns';

const UpcomingToday = ({ events, className = "" }) => {
  const now = getCurrentInUserTimezone();
  
  // Filter events for today and get the NEXT upcoming event
  const todayEvents = events.filter(event => {
    try {
      const eventDate = parseISO(event.datetime_utc);
      return isToday(eventDate);
    } catch {
      return false;
    }
  }).sort((a, b) => {
    // Sort by time
    const timeA = new Date(a.datetime_utc).getTime();
    const timeB = new Date(b.datetime_utc).getTime();
    return timeA - timeB;
  });

  // Find the NEXT upcoming event (closest to current time, but in the future)
  const nextEvent = todayEvents.find(event => {
    try {
      const eventDateTime = parseISO(event.datetime_utc);
      return isFuture(eventDateTime);
    } catch {
      return false;
    }
  }) || todayEvents[0]; // Fallback to first event if no future events

  if (todayEvents.length === 0) {
    return (
      <Card className={`today-card empty-today ${className}`}>
        <CardContent className="today-content">
          <div className="today-header">
            <div className="today-title-section">
              <Sunrise className="today-main-icon" />
              <div className="today-title-text">
                <h3 className="today-title">Today</h3>
                <p className="today-subtitle">Clear schedule ahead</p>
              </div>
            </div>
            <div className="today-accent"></div>
          </div>
          
          <div className="empty-today-content">
            <div className="empty-illustration">
              <div className="empty-glow"></div>
              <Star className="empty-star" />
            </div>
            <p className="empty-message">No events scheduled for today</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={`today-card ${className}`}>
      <CardContent className="today-content">
        <div className="today-header">
          <div className="today-title-section">
            <Clock className="today-main-icon" />
            <div className="today-title-text">
              <h3 className="today-title">Today</h3>
              <p className="today-subtitle">Next: {nextEvent ? formatInUserTimezone(nextEvent.datetime_utc, 'h:mm a') : 'No upcoming events'}</p>
            </div>
          </div>
          <div className="today-accent"></div>
        </div>
        
        <div className="today-events-container">
          {todayEvents.map((event, index) => {
            const category = EVENT_CATEGORIES[event.category?.toUpperCase()] || EVENT_CATEGORIES.PERSONAL;
            const eventTime = formatInUserTimezone(event.datetime_utc, 'h:mm a');
            const isNext = event.id === nextEvent?.id; // Mark the next upcoming event
            const eventDateTime = parseISO(event.datetime_utc);
            const hasHappened = isPast(eventDateTime);
            
            return (
              <div 
                key={event.id} 
                className={`today-event ${isNext ? 'next-event' : ''} ${hasHappened ? 'past-event' : ''}`}
              >
                <div className="event-time-display">
                  <span className="event-time-text">{eventTime}</span>
                </div>
                
                <div className="event-content">
                  <div className="event-main-info">
                    <h4 className="event-name">{event.title}</h4>
                    {event.description && (
                      <p className="event-note">{event.description}</p>
                    )}
                  </div>
                  
                  <Badge 
                    className="event-category-tag"
                    data-category={event.category?.toLowerCase() || 'personal'}
                  >
                    {category.name}
                  </Badge>
                </div>
                
                {isNext && !hasHappened && (
                  <div className="next-badge">
                    <span>Next</span>
                  </div>
                )}
                
                <div 
                  className="event-accent-bar"
                  data-category={event.category?.toLowerCase() || 'personal'}
                ></div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

export default UpcomingToday;
import React from 'react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Clock, Sunrise, Star } from 'lucide-react';
import { EVENT_CATEGORIES } from '../utils/eventProcessing';
import { formatInUserTimezone, getCurrentInUserTimezone } from '../utils/timezone';
import { isToday, parseISO } from 'date-fns';

const UpcomingToday = ({ events, className = "" }) => {
  const now = getCurrentInUserTimezone();
  
  // Filter events for today
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
              <p className="today-subtitle">{todayEvents.length} {todayEvents.length === 1 ? 'event' : 'events'}</p>
            </div>
          </div>
          <div className="today-accent"></div>
        </div>
        
        <div className="today-events-container">
          {todayEvents.map((event, index) => {
            const category = EVENT_CATEGORIES[event.category?.toUpperCase()] || EVENT_CATEGORIES.PERSONAL;
            const eventTime = formatInUserTimezone(event.datetime_utc, 'h:mm a');
            const isNext = index === 0; // First event is "next"
            
            return (
              <div 
                key={event.id} 
                className={`today-event ${isNext ? 'next-event' : ''}`}
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
                    style={{
                      backgroundColor: category.color,
                      borderColor: category.borderColor,
                      color: category.textColor,
                    }}
                  >
                    {category.name}
                  </Badge>
                </div>
                
                {isNext && (
                  <div className="next-badge">
                    <span>Next</span>
                  </div>
                )}
                
                <div 
                  className="event-accent-bar"
                  style={{ backgroundColor: category.borderColor }}
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
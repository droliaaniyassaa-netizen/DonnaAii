import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Clock, Calendar, Sunrise } from 'lucide-react';
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
      <Card className={`upcoming-today-card empty ${className}`}>
        <CardContent className="upcoming-today-content">
          <div className="empty-today">
            <Sunrise className="empty-icon" />
            <div className="empty-text">
              <h4 className="empty-title">Free Day Ahead</h4>
              <p className="empty-subtitle">No events scheduled for today</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={`upcoming-today-card ${className}`}>
      <CardHeader className="upcoming-today-header">
        <CardTitle className="upcoming-today-title">
          <Calendar className="today-icon" />
          <span>Today</span>
          <Badge variant="secondary" className="events-count">
            {todayEvents.length} {todayEvents.length === 1 ? 'event' : 'events'}
          </Badge>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="upcoming-today-content">
        <div className="today-events-list">
          {todayEvents.map((event, index) => {
            const category = EVENT_CATEGORIES[event.category?.toUpperCase()] || EVENT_CATEGORIES.PERSONAL;
            const eventTime = formatInUserTimezone(event.datetime_utc, 'h:mm a');
            const isNext = index === 0; // First event is "next"
            
            return (
              <div 
                key={event.id} 
                className={`today-event-item ${isNext ? 'next-event' : ''}`}
                style={{
                  borderLeftColor: category.borderColor,
                  backgroundColor: category.color,
                }}
              >
                <div className="event-time-badge">
                  <Clock className="time-icon" />
                  <span className="time-text">{eventTime}</span>
                </div>
                
                <div className="event-info">
                  <h5 className="event-title">{event.title}</h5>
                  {event.description && (
                    <p className="event-description">{event.description}</p>
                  )}
                </div>
                
                <Badge 
                  variant="outline" 
                  className="category-indicator"
                  style={{
                    borderColor: category.borderColor,
                    color: category.textColor,
                    backgroundColor: 'rgba(255, 255, 255, 0.05)'
                  }}
                >
                  {category.name}
                </Badge>
                
                {isNext && (
                  <div className="next-indicator">
                    <span className="next-text">Next</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
        
        <div className="today-summary">
          <div className="summary-stats">
            <div className="stat-item">
              <span className="stat-number">{todayEvents.length}</span>
              <span className="stat-label">Total</span>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-item">
              <span className="stat-number">
                {todayEvents.filter(e => (e.category || 'personal') === 'work').length}
              </span>
              <span className="stat-label">Work</span>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-item">
              <span className="stat-number">
                {todayEvents.filter(e => (e.category || 'personal') === 'personal').length}
              </span>
              <span className="stat-label">Personal</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default UpcomingToday;
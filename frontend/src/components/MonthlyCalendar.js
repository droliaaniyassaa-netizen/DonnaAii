import React, { useState, useMemo } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from 'lucide-react';
import { EVENT_CATEGORIES } from '../utils/eventProcessing';
import EventCard from './EventCard';

// Monthly Calendar Component - Futuristic Glassmorphic Design
const MonthlyCalendar = ({ events, onDeleteEvent, onUpdateEvent }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedEvent, setSelectedEvent] = useState(null);

  // Navigation functions
  const navigateMonth = (direction) => {
    setCurrentDate(prev => {
      const newDate = new Date(prev);
      newDate.setMonth(prev.getMonth() + direction);
      return newDate;
    });
  };

  // Generate calendar grid
  const calendarData = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    // First day of the month
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    
    // Start from Sunday of the first week
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    // Generate 6 weeks of days
    const weeks = [];
    let currentWeekDate = new Date(startDate);
    
    for (let week = 0; week < 6; week++) {
      const weekDays = [];
      for (let day = 0; day < 7; day++) {
        const date = new Date(currentWeekDate);
        const isCurrentMonth = date.getMonth() === month;
        const isToday = date.toDateString() === new Date().toDateString();
        
        // Get events for this date
        const dayEvents = events.filter(event => {
          const eventDate = new Date(event.datetime_utc);
          return eventDate.toDateString() === date.toDateString();
        });

        weekDays.push({
          date: new Date(date),
          dayNumber: date.getDate(),
          isCurrentMonth,
          isToday,
          events: dayEvents
        });
        
        currentWeekDate.setDate(currentWeekDate.getDate() + 1);
      }
      weeks.push(weekDays);
    }
    
    return weeks;
  }, [currentDate, events]);

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  const handleEventClick = (event, e) => {
    e.stopPropagation();
    setSelectedEvent(event);
  };

  const closeEventModal = () => {
    setSelectedEvent(null);
  };

  return (
    <div className="monthly-calendar-container">
      {/* Calendar Header - Futuristic Navigation */}
      <div className="monthly-header">
        <div className="month-navigation">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigateMonth(-1)}
            className="nav-button prev-button"
          >
            <ChevronLeft className="nav-icon" />
          </Button>
          
          <div className="current-month">
            <CalendarIcon className="month-icon" />
            <h2 className="month-title">
              {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
            </h2>
          </div>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigateMonth(1)}
            className="nav-button next-button"
          >
            <ChevronRight className="nav-icon" />
          </Button>
        </div>

        {/* Futuristic Stats Bar */}
        <div className="calendar-stats">
          <div className="stat-item">
            <span className="stat-label">Events</span>
            <span className="stat-value">{events.length}</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-item">
            <span className="stat-label">This Month</span>
            <span className="stat-value">
              {events.filter(e => {
                const eventDate = new Date(e.datetime_utc);
                return eventDate.getMonth() === currentDate.getMonth() && 
                       eventDate.getFullYear() === currentDate.getFullYear();
              }).length}
            </span>
          </div>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="calendar-grid-container">
        {/* Day Headers */}
        <div className="day-headers">
          {dayNames.map(day => (
            <div key={day} className="day-header">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar Weeks */}
        <div className="calendar-weeks">
          {calendarData.map((week, weekIndex) => (
            <div key={weekIndex} className="calendar-week">
              {week.map((day, dayIndex) => (
                <div
                  key={`${weekIndex}-${dayIndex}`}
                  className={`calendar-day ${day.isCurrentMonth ? 'current-month' : 'other-month'} ${day.isToday ? 'today' : ''}`}
                >
                  {/* Day Number with Holographic Effect */}
                  <div className="day-number">
                    <span className="day-text">{day.dayNumber}</span>
                    {day.isToday && <div className="today-pulse"></div>}
                  </div>

                  {/* Events Container */}
                  <div className="day-events">
                    {day.events.slice(0, 3).map((event, eventIndex) => {
                      const category = EVENT_CATEGORIES[event.category?.toUpperCase()] || EVENT_CATEGORIES.PERSONAL;
                      return (
                        <div
                          key={event.id}
                          className="mini-event"
                          data-category={event.category?.toLowerCase() || 'personal'}
                          onClick={(e) => handleEventClick(event, e)}
                          title={`${event.title} - ${new Date(event.datetime_utc).toLocaleTimeString('en-US', {hour: 'numeric', minute: '2-digit'})}`}
                        >
                          <div className="event-indicator"></div>
                          <span className="event-title-mini">{event.title}</span>
                        </div>
                      );
                    })}
                    {day.events.length > 3 && (
                      <div className="more-events">
                        +{day.events.length - 3} more
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* Event Modal - Same as existing EventCard modal */}
      {selectedEvent && (
        <div className="event-modal-overlay" onClick={closeEventModal}>
          <div className="event-modal-content" onClick={(e) => e.stopPropagation()}>
            <EventCard
              event={selectedEvent}
              onDelete={onDeleteEvent}
              onUpdate={onUpdateEvent}
              className="modal-event-card"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default MonthlyCalendar;
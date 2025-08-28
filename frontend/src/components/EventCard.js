import React, { useState } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Trash2, Clock, Bell, Edit3, Save, X, Calendar as CalendarIcon, Check } from 'lucide-react';
import { EVENT_CATEGORIES } from '../utils/eventProcessing';
import { formatInUserTimezone, splitUTCDateTime } from '../utils/timezone';

const EventCard = ({ event, onDelete, onUpdate, className = "" }) => {
  const [isFlipped, setIsFlipped] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    title: event.title,
    description: event.description || '',
    category: event.category || 'personal'
  });

  const category = EVENT_CATEGORIES[event.category?.toUpperCase()] || EVENT_CATEGORIES.PERSONAL;
  const { date, time } = splitUTCDateTime(event.datetime_utc);
  const formattedDate = formatInUserTimezone(event.datetime_utc, 'MMM d, yyyy');
  const formattedTime = formatInUserTimezone(event.datetime_utc, 'h:mm a');
  const dayOfWeek = formatInUserTimezone(event.datetime_utc, 'EEEE');

  const handleFlip = () => {
    setIsFlipped(!isFlipped);
    setIsEditing(false);
  };

  const handleEdit = (e) => {
    e.stopPropagation();
    setIsEditing(true);
  };

  const handleSave = async (e) => {
    e.stopPropagation();
    try {
      await onUpdate(event.id, editData);
      setIsEditing(false);
      setIsFlipped(false); // Close the card after saving
    } catch (error) {
      console.error('Error updating event:', error);
    }
  };

  const handleCancel = (e) => {
    e.stopPropagation();
    setEditData({
      title: event.title,
      description: event.description || '',
      category: event.category || 'personal'
    });
    setIsEditing(false);
    setIsFlipped(false); // Close the card
  };

  const handleDelete = (e) => {
    e.stopPropagation();
    onDelete(event.id);
  };

  // Check if event is in the past
  const eventDateTime = new Date(event.datetime_utc);
  const now = new Date();
  const isPastEvent = eventDateTime < now;

  return (
    <div 
      className={`event-card-container ${isFlipped ? 'flipped' : ''} ${className}`}
      data-category={event.category?.toLowerCase() || 'personal'}
    >
      <div className={`event-card ${isFlipped ? 'flipped' : ''} ${isPastEvent ? 'past' : ''}`}>
        {/* Front Face */}
        <Card 
          className="event-card-face event-card-front"
          onClick={handleFlip}
        >
          <CardContent className="event-card-content">
            <div className="event-card-header">
              <div className="event-time-section">
                <div className="event-time">{formattedTime}</div>
                <div className="event-date">{formattedDate}</div>
              </div>
              <Badge 
                className="event-category-badge"
              >
                {category.name}
              </Badge>
            </div>
            
            <div className="event-main-content">
              <h3 className="event-title">{event.title}</h3>
              {event.description && (
                <p className="event-description">{event.description}</p>
              )}
            </div>
            
            <div className="event-card-footer">
              <div className="event-day">{dayOfWeek}</div>
              <div className="event-indicators">
                {event.reminder && (
                  <div className="reminder-indicator">
                    <Bell className="reminder-icon" />
                  </div>
                )}
                <div className="flip-indicator">
                  <span className="flip-text">Tap to edit</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Back Face */}
        <Card 
          className="event-card-face event-card-back"
        >
          <CardContent className="event-card-content">
            <div className="event-edit-header">
              <h4 className="edit-title">Edit Event</h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCancel}
                className="close-edit-button"
              >
                <X className="close-icon" />
              </Button>
            </div>

            {isEditing ? (
              <div className="event-edit-form">
                <Input
                  value={editData.title}
                  onChange={(e) => setEditData({ ...editData, title: e.target.value })}
                  placeholder="Event title"
                  className="edit-input"
                />
                
                <textarea
                  value={editData.description}
                  onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                  placeholder="Description (optional)"
                  className="edit-textarea"
                  rows={3}
                />
                
                <select
                  value={editData.category}
                  onChange={(e) => setEditData({ ...editData, category: e.target.value })}
                  className="edit-select"
                >
                  {Object.entries(EVENT_CATEGORIES).map(([key, cat]) => (
                    <option key={key} value={key.toLowerCase()}>
                      {cat.name}
                    </option>
                  ))}
                </select>

                <div className="edit-actions">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCancel}
                    className="cancel-button"
                  >
                    <X className="action-icon" />
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleSave}
                    className="save-button"
                  >
                    <Save className="action-icon" />
                    Save
                  </Button>
                </div>
              </div>
            ) : (
              <div className="event-details">
                <div className="detail-section">
                  <CalendarIcon className="detail-icon" />
                  <div className="detail-content">
                    <div className="detail-label">When</div>
                    <div className="detail-value">{formattedDate} at {formattedTime}</div>
                  </div>
                </div>

                <div className="detail-section">
                  <Clock className="detail-icon" />
                  <div className="detail-content">
                    <div className="detail-label">Reminders</div>
                    <div className="detail-value">
                      {event.reminder ? '12h & 2h before' : 'None'}
                    </div>
                  </div>
                </div>

                {event.description && (
                  <div className="detail-section">
                    <Edit3 className="detail-icon" />
                    <div className="detail-content">
                      <div className="detail-label">Notes</div>
                      <div className="detail-value">{event.description}</div>
                    </div>
                  </div>
                )}

                <div className="event-actions">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleEdit}
                    className="edit-button"
                  >
                    <Edit3 className="action-icon" />
                    Edit
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleDelete}
                    className="delete-button"
                  >
                    <Trash2 className="action-icon" />
                    Delete
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default EventCard;
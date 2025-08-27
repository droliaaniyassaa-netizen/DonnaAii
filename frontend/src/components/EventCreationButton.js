import React, { useState } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Plus, X, Calendar, Sparkles } from 'lucide-react';
import { EVENT_CATEGORIES } from '../utils/eventProcessing';

const EventCreationButton = ({ newEvent, setNewEvent, onCreateEvent, className = "" }) => {
  const [isFlipped, setIsFlipped] = useState(false);

  const handleFlip = () => {
    setIsFlipped(!isFlipped);
  };

  const handleCreate = () => {
    onCreateEvent();
    setIsFlipped(false);
  };

  const handleCancel = () => {
    setIsFlipped(false);
  };

  return (
    <div className={`event-creation-container ${className}`}>
      <div className={`event-creation-card ${isFlipped ? 'flipped' : ''}`}>
        {/* Front Face - Compact Button */}
        <Card className="creation-card-face creation-card-front" onClick={handleFlip}>
          <CardContent className="creation-front-content">
            <div className="creation-button-content">
              <div className="creation-icon-wrapper">
                <Plus className="creation-plus-icon" />
                <Sparkles className="creation-sparkle-icon" />
              </div>
              <div className="creation-text">
                <span className="creation-title">Schedule Event</span>
                <span className="creation-subtitle">Tap to create</span>
              </div>
            </div>
            <div className="creation-glow"></div>
          </CardContent>
        </Card>

        {/* Back Face - Creation Form */}
        <Card className="creation-card-face creation-card-back">
          <CardContent className="creation-back-content">
            <div className="creation-form-header">
              <div className="creation-header-content">
                <Calendar className="creation-header-icon" />
                <h4 className="creation-form-title">New Event</h4>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCancel}
                className="creation-close-button"
              >
                <X className="creation-close-icon" />
              </Button>
            </div>

            <div className="creation-form">
              <Input
                placeholder="Event title"
                value={newEvent.title}
                onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                className="creation-input"
              />
              
              <select
                value={newEvent.category || 'personal'}
                onChange={(e) => setNewEvent({ ...newEvent, category: e.target.value })}
                className="creation-select"
              >
                {Object.entries(EVENT_CATEGORIES).map(([key, category]) => (
                  <option key={key} value={key.toLowerCase()}>
                    {category.name}
                  </option>
                ))}
              </select>
              
              <div className="creation-datetime-row">
                <Input
                  type="date"
                  value={newEvent.date}
                  onChange={(e) => setNewEvent({ ...newEvent, date: e.target.value })}
                  className="creation-input creation-date"
                />
                <Input
                  type="time"
                  value={newEvent.time}
                  onChange={(e) => setNewEvent({ ...newEvent, time: e.target.value })}
                  className="creation-input creation-time"
                />
              </div>
              
              <Textarea
                placeholder="Description (optional)"
                value={newEvent.description}
                onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                className="creation-textarea"
                rows={2}
              />

              <div className="creation-actions">
                <Button
                  variant="ghost"
                  onClick={handleCancel}
                  className="creation-cancel-btn"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreate}
                  className="creation-submit-btn"
                  disabled={!newEvent.title || !newEvent.date || !newEvent.time}
                >
                  <Plus className="creation-submit-icon" />
                  Create Event
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default EventCreationButton;
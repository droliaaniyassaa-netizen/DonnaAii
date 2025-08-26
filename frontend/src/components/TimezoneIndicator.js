import React from 'react';
import { Clock } from 'lucide-react';
import { Badge } from './ui/badge';
import { getTimezoneDisplayName } from '../utils/timezone';

const TimezoneIndicator = ({ className = "" }) => {
  const timezoneInfo = getTimezoneDisplayName();
  
  return (
    <div className={`timezone-indicator ${className}`}>
      <Clock className="timezone-indicator-icon" />
      <span className="timezone-indicator-text">
        All times shown in {timezoneInfo.name}
      </span>
    </div>
  );
};

export default TimezoneIndicator;
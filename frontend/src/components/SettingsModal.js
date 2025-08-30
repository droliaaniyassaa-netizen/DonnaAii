import React, { useState, useEffect, useMemo } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from './ui/command';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { Check, ChevronsUpDown, Search, Clock, Globe } from 'lucide-react';
import { cn } from '../lib/utils';
import { 
  getUserTimezone, 
  saveUserTimezone, 
  getSystemTimezone,
  getTimezoneDisplayName,
  getAllTimezones,
  COMMON_TIMEZONES 
} from '../utils/timezone';

const SettingsModal = ({ open, onClose }) => {
  const [selectedTimezone, setSelectedTimezone] = useState(getUserTimezone());
  const [searchQuery, setSearchQuery] = useState('');
  const [timezoneOpen, setTimezoneOpen] = useState(false);
  const [weekendMode, setWeekendMode] = useState('relaxed');
  const [loading, setLoading] = useState(false);
  
  const systemTimezone = getSystemTimezone();
  const allTimezones = getAllTimezones();

  // Load user settings on open
  useEffect(() => {
    if (open) {
      loadUserSettings();
    }
  }, [open]);

  const loadUserSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/user/settings/default`);
      if (response.ok) {
        const settings = await response.json();
        setWeekendMode(settings.weekend_mode || 'relaxed');
        if (settings.timezone) {
          setSelectedTimezone(settings.timezone);
        }
      }
    } catch (error) {
      console.error('Failed to load user settings:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Filter timezones based on search
  const filteredTimezones = useMemo(() => {
    if (!searchQuery) {
      // Show common timezones first, then all others
      const common = COMMON_TIMEZONES.filter(tz => allTimezones.includes(tz));
      const others = allTimezones.filter(tz => !COMMON_TIMEZONES.includes(tz));
      return { common, others };
    }
    
    const query = searchQuery.toLowerCase();
    const filtered = allTimezones.filter(tz => 
      tz.toLowerCase().includes(query) ||
      tz.replace(/_/g, ' ').toLowerCase().includes(query)
    );
    
    return { common: filtered, others: [] };
  }, [searchQuery, allTimezones]);
  
  const handleSave = () => {
    saveUserTimezone(selectedTimezone);
    onClose();
    // Trigger a page refresh to update all displayed times
    window.location.reload();
  };
  
  const handleReset = () => {
    setSelectedTimezone(systemTimezone);
  };
  
  const getCurrentTimezoneDisplay = () => {
    return getTimezoneDisplayName(selectedTimezone);
  };
  
  const getTimezonePreview = (tz) => {
    try {
      const now = new Date();
      const formatter = new Intl.DateTimeFormat('en-US', {
        timeZone: tz,
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short'
      });
      return formatter.format(now);
    } catch {
      return '';
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="settings-modal">
        <DialogHeader>
          <DialogTitle className="settings-title">
            <Globe className="settings-icon" />
            Settings
          </DialogTitle>
        </DialogHeader>
        
        <div className="settings-content">
          {/* Timezone Section */}
          <div className="setting-section">
            <Label className="setting-label">
              <Clock className="label-icon" />
              Time Zone
            </Label>
            
            <div className="timezone-info">
              <p className="timezone-description">
                Choose your preferred time zone. All dates and times will be displayed in this zone.
              </p>
              
              <div className="current-timezone">
                <span className="timezone-label">Current:</span>
                <Badge variant="outline" className="timezone-badge">
                  {getCurrentTimezoneDisplay().display}
                </Badge>
              </div>
              
              <div className="system-timezone">
                <span className="timezone-label">System:</span>
                <Badge variant="secondary" className="timezone-badge">
                  {getTimezoneDisplayName(systemTimezone).display}
                </Badge>
              </div>
            </div>
            
            {/* Timezone Selector */}
            <Popover open={timezoneOpen} onOpenChange={setTimezoneOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  role="combobox"
                  aria-expanded={timezoneOpen}
                  className="timezone-selector"
                >
                  <Clock className="selector-icon" />
                  {getCurrentTimezoneDisplay().display}
                  <ChevronsUpDown className="chevron-icon" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="timezone-popover">
                <Command>
                  <CommandInput 
                    placeholder="Search timezones..." 
                    className="timezone-search"
                    value={searchQuery}
                    onValueChange={setSearchQuery}
                  />
                  <CommandList className="timezone-list">
                    <CommandEmpty>No timezone found.</CommandEmpty>
                    
                    {filteredTimezones.common.length > 0 && (
                      <CommandGroup heading={searchQuery ? "Results" : "Common Timezones"}>
                        {filteredTimezones.common.map((tz) => (
                          <CommandItem
                            key={tz}
                            value={tz}
                            onSelect={() => {
                              setSelectedTimezone(tz);
                              setTimezoneOpen(false);
                              setSearchQuery('');
                            }}
                            className="timezone-item"
                          >
                            <Check
                              className={cn(
                                "check-icon",
                                selectedTimezone === tz ? "opacity-100" : "opacity-0"
                              )}
                            />
                            <div className="timezone-item-content">
                              <span className="timezone-name">
                                {tz.replace(/_/g, ' ')}
                              </span>
                              <span className="timezone-time">
                                {getTimezonePreview(tz)}
                              </span>
                            </div>
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    )}
                    
                    {!searchQuery && filteredTimezones.others.length > 0 && (
                      <CommandGroup heading="All Timezones">
                        {filteredTimezones.others.map((tz) => (
                          <CommandItem
                            key={tz}
                            value={tz}
                            onSelect={() => {
                              setSelectedTimezone(tz);
                              setTimezoneOpen(false);
                            }}
                            className="timezone-item"
                          >
                            <Check
                              className={cn(
                                "check-icon",
                                selectedTimezone === tz ? "opacity-100" : "opacity-0"
                              )}
                            />
                            <div className="timezone-item-content">
                              <span className="timezone-name">
                                {tz.replace(/_/g, ' ')}
                              </span>
                              <span className="timezone-time">
                                {getTimezonePreview(tz)}
                              </span>
                            </div>
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    )}
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
          </div>
          
          {/* Action Buttons */}
          <div className="settings-actions">
            <Button 
              variant="outline" 
              onClick={handleReset}
              className="reset-button"
            >
              Reset to System
            </Button>
            <Button 
              onClick={handleSave}
              className="save-button"
            >
              Save Changes
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SettingsModal;
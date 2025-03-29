import os
import yaml
from typing import Dict, Any, List, Union, Tuple, Set
from src.logger import Logger
from datetime import datetime, timedelta, date

class PreferenceKeys:
    """
    Structured access to preference keys from configuration
    """
    def __init__(self, config: Dict[str, Any]):
        keys = config.get('user_preferences', {}).get('keys', {})
        self.language = keys.get('language', 'language')
        self.food_requirements = keys.get('food_requirements', 'food_requirements')
        self.max_distance = keys.get('max_distance', 'max_distance')
        self.time_slots = keys.get('time_slots', 'time_slots')
        self.address = keys.get('address', 'address')
        self.pickup_datetime = keys.get('pickup_datetime', 'pickup_datetime')

class TimeSlot:
    """
    Represents a time slot for food pickup
    """
    def __init__(self, date: datetime, period: str):
        self.date = date
        self.period = period
        
    @classmethod
    def from_string(cls, time_str: str) -> 'TimeSlot':
        """Create TimeSlot from string format (e.g., 'Mar 25 afternoon')"""
        try:
            date_str, period = time_str.rsplit(' ', 1)
            # Parse date assuming current year
            current_year = datetime.now().year
            date_obj = datetime.strptime(f"{date_str} {current_year}", "%b %d %Y")
            return cls(date_obj, period)
        except Exception as e:
            raise ValueError(f"Invalid time slot format: {time_str}") from e
        
    def __str__(self) -> str:
        return f"{self.date.strftime('%b %d')} {self.period}"
        
    def __repr__(self) -> str:
        return self.__str__()
        
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TimeSlot):
            return NotImplemented
        return self.date.date() == other.date.date() and self.period == other.period
        
    def __hash__(self) -> int:
        return hash((self.date.date(), self.period))

class Config:
    def __init__(self):
        self.logger = Logger()
        self.config = self._load_config()
        self.preference_keys = PreferenceKeys(self.config)
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file
        """
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'app_config.yaml')
            if not os.path.exists(config_path):
                self.logger.warning(f"Configuration file not found at {config_path}, using defaults")
                return self._get_default_config()
                
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
            
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            return self._get_default_config()
                
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration - this should match the structure of app_config.yaml
        """
        return {
            'environment': 'development',
            'db': {'path': 'data/database.db'},
            'languages': {
                'supported': ['en', 'es'],
                'default': 'en'
            },
            'distance': {
                'max_threshold': 10.0,
                'min_value': 0.0,
                'unit': 'mile'
            },
            'time': {
                'periods': ['morning', 'afternoon', 'evening', 'night'],
                'period_ranges': {
                    'morning': {'start': '06:00', 'end': '11:59'},
                    'afternoon': {'start': '12:00', 'end': '16:59'},
                    'evening': {'start': '17:00', 'end': '20:59'},
                    'night': {'start': '21:00', 'end': '23:59'}
                },
                'days_ahead': 7,
                'format': {
                    'date': '%b %d',
                    'time': '%H:%M'
                }
            },
            'log_level': 'INFO',
            'user_preferences': {
                'keys': {
                    'language': 'language',
                    'food_requirements': 'food_requirements',
                    'max_distance': 'max_distance',
                    'time_slots': 'time_slots',
                    'address': 'address',
                    'pickup_datetime': 'pickup_datetime'
                },
                'questions': {
                    'language': "Which language would you prefer to use? (en/es): ",
                    'food_requirements': "What are your food requirements? (e.g., halal, kosher, vegetarian): ",
                    'distance': "What is the maximum distance you can travel to get food? (in miles): ",
                    'time_slots': "What time slots are you available? (e.g., morning, afternoon, evening): ",
                    'location': "Please enter your full address (country, city, street, zip code): ",
                    'pickup_datetime': "When would you like to pick up food?"
                },
                'validation': {
                    'time_slots': {'valid_options': ['morning', 'afternoon', 'evening', 'night']},
                    'language': {'valid_options': ['en', 'es']},
                    'pickup_datetime': {
                        'min_days': 0,
                        'max_days': 7
                    }
                },
                'defaults': {
                    'language': 'en',
                    'food_requirements': 'vegetarian',
                    'max_distance': 6,
                    'time_slots': 'morning',
                    'address': '5702 Vassar Drive, College Park, Maryland, 20740',
                    'pickup_datetime': ''
                }
            }
        }
        
    def get_time_periods(self) -> List[str]:
        """Get available time periods"""
        return self.get_nested('time', 'periods', default=[])
        
    def get_period_range(self, period: str) -> Tuple[str, str]:
        """Get start and end time for a period"""
        period_range = self.get_nested('time', 'period_ranges', period, default={})
        return (period_range.get('start', '00:00'), period_range.get('end', '23:59'))
        
    def _is_date_available(self, check_date: date) -> bool:
        """Check if a date is available (not in unavailable_days)"""
        unavailable_days = self.get_nested('time', 'unavailable_days', default=[])
        return check_date.strftime('%Y-%m-%d') not in unavailable_days
        
    def _is_slot_available(self, slot: TimeSlot) -> bool:
        """Check if a specific time slot is available"""
        unavailable_slots = self.get_nested('time', 'unavailable_slots', default=[])
        slot_date = slot.date.strftime('%Y-%m-%d')
        
        for unavailable in unavailable_slots:
            if (unavailable.get('date') == slot_date and 
                unavailable.get('period') == slot.period):
                return False
        return True
        
    def get_development_time_slots(self) -> List[TimeSlot]:
        """
        Get predefined time slots for development mode
        """
        try:
            time_slots = self.get_nested('user_preferences', 'defaults', 'time_slots', default=[])
            return [TimeSlot.from_string(slot) for slot in time_slots]
        except Exception as e:
            self.logger.error(f"Error parsing development time slots: {str(e)}")
            return []
            
    def get_available_time_slots(self, current_time: datetime = None) -> List[TimeSlot]:
        """
        Get available time slots based on current time or use predefined slots in development
        """
        if self.is_development():
            return self.get_development_time_slots()
            
        try:
            if current_time is None:
                current_time = datetime.now()
                
            days_ahead = self.get_nested('time', 'days_ahead', default=7)
            periods = self.get_nested('time', 'periods', default=[])
            available_slots = []
            
            # Generate slots for the next 'days_ahead' days
            for day_offset in range(days_ahead):
                date = current_time.date() + timedelta(days=day_offset)
                
                # Skip unavailable days
                if not self._is_date_available(date):
                    continue
                    
                # For current day, only show future periods
                if day_offset == 0:
                    for period in periods:
                        period_start, _ = self.get_period_range(period)
                        period_time = datetime.strptime(period_start, '%H:%M').time()
                        slot_datetime = datetime.combine(date, period_time)
                        
                        if slot_datetime > current_time:
                            slot = TimeSlot(slot_datetime, period)
                            if self._is_slot_available(slot):
                                available_slots.append(slot)
                else:
                    # For future days, show all periods
                    for period in periods:
                        period_start, _ = self.get_period_range(period)
                        period_time = datetime.strptime(period_start, '%H:%M').time()
                        slot = TimeSlot(datetime.combine(date, period_time), period)
                        if self._is_slot_available(slot):
                            available_slots.append(slot)
            
            return available_slots
            
        except Exception as e:
            self.logger.error(f"Error getting available time slots: {str(e)}")
            return []
        
    def get_nested(self, *keys: str, default: Any = None) -> Any:
        """
        Safely get nested configuration values
        """
        current = self.config
        for key in keys:
            if not isinstance(current, dict):
                return default
            current = current.get(key, default)
            if current is None:
                return default
        return current
        
    def get_environment(self) -> str:
        """Get current environment"""
        return self.get_nested('environment', default='development')
        
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.get_environment() == 'development'
        
    def get_db_path(self) -> str:
        """Get database path"""
        return self.get_nested('db', 'path', default='data/database.db')
        
    def get_supported_languages(self) -> List[str]:
        """Get supported languages"""
        return self.get_nested('languages', 'supported', default=['en', 'es'])
        
    def get_default_language(self) -> str:
        """Get default language"""
        return self.get_nested('languages', 'default', default='en')
        
    def get_distance_config(self) -> Dict[str, Union[float, str]]:
        """Get distance configuration"""
        return self.get_nested('distance', default={
            'max_threshold': 10.0,
            'min_value': 0.0,
            'unit': 'mile'
        })
        
    def get_user_preferences_config(self) -> Dict[str, Any]:
        """Get user preferences configuration"""
        return self.get_nested('user_preferences', default={})
        
    def get_validation_options(self, field: str) -> List[str]:
        """Get validation options for a specific field"""
        return self.get_nested('user_preferences', 'validation', field, 'valid_options', default=[]) 
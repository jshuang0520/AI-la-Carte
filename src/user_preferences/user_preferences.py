import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from src.logger import Logger
from src.translate_helper import TranslateHelper
from src.config.user_preferences_config import UserPreferencesConfig

class UserPreferences:
    def __init__(self, env: str = 'dev'):
        self.logger = Logger()
        self.translate_helper = TranslateHelper()
        self.config = UserPreferencesConfig(env=env)
        self.preferences = {}
        
    def _generate_time_slots(self) -> List[str]:
        """Generate available time slots for the next week"""
        try:
            current_time = datetime.now()
            days_ahead = self.config.config.get('time', {}).get('days_ahead', 7)
            periods = self.config.config.get('time', {}).get('periods', ['morning', 'afternoon', 'evening', 'night'])
            
            available_slots = []
            
            # Generate slots for the next 'days_ahead' days
            for day_offset in range(days_ahead):
                date = current_time.date() + timedelta(days=day_offset)
                
                # For current day, only show future periods
                if day_offset == 0:
                    for period in periods:
                        period_start = self.config.config.get('time', {}).get('period_ranges', {}).get(period, {}).get('start', '00:00')
                        period_time = datetime.strptime(period_start, '%H:%M').time()
                        slot_datetime = datetime.combine(date, period_time)
                        
                        if slot_datetime > current_time:
                            available_slots.append(f"{date.strftime('%Y-%m-%d')} {period}")
                else:
                    # For future days, show all periods
                    for period in periods:
                        available_slots.append(f"{date.strftime('%Y-%m-%d')} {period}")
            
            return available_slots
            
        except Exception as e:
            self.logger.error(f"Error generating time slots: {str(e)}")
            return []
            
    def _handle_multiple_selection(self, options: List[str], category: str) -> str:
        """Handle multiple selection from a list of options"""
        print(f"\nAvailable {category}:")
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        
        print(f"\nEnter the numbers of {category} you need (comma-separated):")
        while True:
            try:
                # Get input and clean it
                raw_input = input().strip()
                if not raw_input:
                    self.logger.warning("Please enter at least one selection")
                    continue
                    
                # Parse selected indices and remove duplicates using set
                selected_indices = set(int(idx.strip()) for idx in raw_input.split(','))
                
                # Validate all indices are within valid range
                if not all(1 <= idx <= len(options) for idx in selected_indices):
                    self.logger.warning(f"Please enter numbers between 1 and {len(options)}")
                    continue
                
                # Convert indices to actual options (using set to ensure uniqueness)
                selected_options = set(options[i-1] for i in selected_indices)
                
                # Verify all selected options are in the valid options list
                if not all(opt in options for opt in selected_options):
                    self.logger.warning("Invalid selection detected. Please try again.")
                    continue
                
                # Convert back to sorted list for consistent output
                return ','.join(sorted(selected_options))
                
            except ValueError as e:
                self.logger.warning("Please enter valid numbers separated by commas")
                continue
            except Exception as e:
                self.logger.warning(f"Invalid selection. Please try again. Error: {str(e)}")
                continue
        
    def _handle_pickup_day(self) -> str:
        """Handle pickup day selection with follow-up questions"""
        print("\nWould you like to get food today or another day this week?")
        print("1. Today")
        print("2. Tomorrow")
        print("3. Another day this week")
        
        while True:
            try:
                selection = int(input("Enter your choice (1-3): ").strip())
                if selection == 1:
                    return "today"
                elif selection == 2:
                    return "tomorrow"
                elif selection == 3:
                    # Get the day of the week
                    print("\nWhich day would you prefer?")
                    print("1. Monday")
                    print("2. Tuesday")
                    print("3. Wednesday")
                    print("4. Thursday")
                    print("5. Friday")
                    print("6. Saturday")
                    print("7. Sunday")
                    
                    day_selection = int(input("Enter your choice (1-7): ").strip())
                    if 1 <= day_selection <= 7:
                        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                        return f"this_week_{days[day_selection-1]}"
                    else:
                        self.logger.warning("Invalid day selection. Please try again.")
                else:
                    self.logger.warning("Invalid selection. Please enter 1, 2, or 3.")
            except ValueError:
                self.logger.warning("Please enter a valid number")
                continue
        
    def collect_preferences(self) -> Dict[str, Any]:
        """Collect user preferences using configuration"""
        try:
            # Define the order of questions
            categories = ['language', 'address', 'pickup_day', 'pickup_time', 
                         'transportation', 'health_dietary', 'religious_dietary',
                         'kitchen_access', 'services', 'proxy_pickup']
            
            # Define which categories support multiple selections
            multiple_selection_categories = [
                'health_dietary', 'religious_dietary', 'services'
            ]
            
            for category in categories:
                question = self.config.get_question(category)
                valid_options = self.config.get_valid_options(category)
                default_value = self.config.get_default_value(category)
                key = self.config.get_key(category)
                
                while True:
                    if category == 'pickup_day':
                        user_input = self._handle_pickup_day()
                    elif category in multiple_selection_categories:
                        # Handle multiple selection fields
                        user_input = self._handle_multiple_selection(valid_options, category)
                        if not user_input:
                            continue
                    else:
                        user_input = input(question).strip()
                    
                    # If no input and default exists, use default
                    if not user_input and default_value is not None:
                        user_input = str(default_value)
                        self.logger.info(f"Using default value for {category}: {default_value}")
                    
                    # Validate input if valid options exist
                    if valid_options:
                        if category in multiple_selection_categories:
                            # For multiple selection fields, validate each selected option
                            selected_options = [opt.strip() for opt in user_input.split(',')]
                            if not all(opt in valid_options for opt in selected_options):
                                self.logger.warning(f"Invalid selection. Valid options: {valid_options}")
                                continue
                        elif user_input not in valid_options:
                            self.logger.warning(f"Invalid input for {category}. Valid options: {valid_options}")
                            continue
                    
                    self.preferences[key] = user_input
                    
                    # Handle conditional questions
                    if category == 'transportation' and user_input.lower() == 'no':
                        # Skip to proxy pickup question
                        self.preferences['proxy_pickup'] = input(self.config.get_question('proxy_pickup')).strip()
                        break
                    
                    break
                    
            return self.preferences
            
        except Exception as e:
            self.logger.error(f"Error collecting preferences: {str(e)}")
            raise
            
    def verify_input(self, category: str, value: str) -> bool:
        """Verify user input against configuration"""
        try:
            valid_options = self.config.get_valid_options(category)
            
            # If no valid options defined, accept any input
            if valid_options is None:
                return True
                
            # For multiple selection fields, validate each selected option
            multiple_selection_categories = [
                'health_dietary', 'religious_dietary', 'services'
            ]
            
            if category in multiple_selection_categories:
                selected_options = [opt.strip() for opt in value.split(',')]
                return all(opt in valid_options for opt in selected_options)
                
            # Check if value is in valid options
            return value in valid_options
            
        except Exception as e:
            self.logger.error(f"Error verifying input: {str(e)}")
            return False 
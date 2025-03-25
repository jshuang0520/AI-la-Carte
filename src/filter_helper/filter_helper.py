import pandas as pd
import datetime

from typing import Dict, Any, List
from src.logger import Logger
from src.geo_helper import GeoHelper
from src.rag_helper import RAGHelper
from src.translate_helper import TranslateHelper

class FilterHelper:
    def __init__(self):
        self.logger = Logger()
        self.geo_helper = GeoHelper()
        self.rag_helper = RAGHelper()
        self.translate_helper = TranslateHelper()
        
    def get_recommendations(
        self,
        user_preferences: Dict[str, Any],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Main recommendation function that coordinates RAG, geo filtering, and translations
        """
        try:
            # Step 1: Filter by distance
            geo_stores = self.geo_helper.find_nearby_food_assistance(
                user_preferences['location'],
                float(user_preferences['distance'])
            )

            # Filter according to user preferences
            filtered_stores = self._filter_stores(
                geo_stores,
                user_preferences
            )
            print(filtered_stores)
            return filtered_stores
            
            """
            # Step 2: Get RAG-based recommendations
            rag_stores = self.rag_helper.get_relevant_stores(
                user_preferences,
                filtered_stores,
                top_n=top_n
            )
            
            # Step 3: Translate results to user's preferred language
            translated_stores = self.translate_helper.translate_stores(
                rag_stores,
                user_preferences['language']
            )
            
            # Step 4: Sort by relevance and distance
            return self._sort_results(translated_stores)
            """

        except Exception as e:
            self.logger.error(f"Error getting recommendations: {str(e)}")
            raise
        

    def _filter_stores(
        self,
        stores: pd.DataFrame,             
        user_preferences: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Filter stores based on user preferences and return as a DataFrame
        """
        try:
            requested_date = user_preferences.get('requested_date', pd.Timestamp.now().date())
            requested_date = pd.to_datetime(requested_date).date()
            asked_time = user_preferences.get('asked_time', 'morning')

            # Filter by required columns and convert timestamp to date
            distance_dataframe = stores[['agency_ref', 'phone', 'email', 'Date_of_Last_SO', 'Distance']]
            distance_dataframe['Date_of_Last_SO'] = pd.to_datetime(distance_dataframe['Date_of_Last_SO'], unit='ms').dt.date

            # Get market data and Shopping Partner data
            markets_HOO = pd.read_excel("data/CAFB_Markets_HOO.xlsx")
            SP_HOO = pd.read_excel("data/CAFB_Shopping_Partners_HOO.xlsx")
            HOO_dataframe = self._mix_markets_SP_HOO(
                markets_HOO,
                SP_HOO
            )

            # Find which weeks do the market/shopping partner opens for present and future months (consective 8 weeks)
            result_week_dataframe = self._add_weeks_present(
                HOO_dataframe,
                distance_dataframe,
                requested_date
            )

            # Add current and next opening dates
            result_date_dataframe = self._add_current_next_dates(
                result_week_dataframe,
                requested_date
            )

            # Add time based information
            markets_information = self._filter_time_information(
                result_date_dataframe,
                asked_time
            )

            # Convert the filtered list back to a DataFrame
            filtered_stores = markets_information[markets_information["Open on Requested Date"]].copy()
            return filtered_stores
        
        except Exception as e:
            self.logger.error(f"Error filtering stores: {str(e)}")
            raise

    def _mix_markets_SP_HOO(
        self,
        markets_HOO: pd.DataFrame,
        SP_HOO: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Given markets and shopping partner data, merge them into a single dataframe
        """
        freq_markets_HOO = markets_HOO[~markets_HOO["Frequency"].isna()]
        freq_markets_HOO.loc[freq_markets_HOO["Frequency"].str.strip() == "Every week", 'Frequency'] = "Every week 12345"
        for i in range(5): 
            freq_markets_HOO[f"Week {i + 1}"] = False
            freq_markets_HOO.loc[freq_markets_HOO["Frequency"].str.contains(str(i + 1)), f"Week {i + 1}"] = True

        #TODO: Add Shopping Partner data
        return HOO_dataframe

    def _add_weeks_present(
        self,
        HOO_dataframe: pd.DataFrame,
        distance_dataframe: pd.DataFrame,
        requested_date: pd.Timestamp
    ) -> pd.DataFrame:
        """
        Given date information, find 8 weeks from the start of the date's month when the shop/market is open
        """
        time_dataframe = pd.merge(
            distance_dataframe, 
            HOO_dataframe, 
            left_on='agency_ref', 
            right_on='Agency ID', 
            how='inner'
        )

        weekday_database = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6
        }

        time_dataframe["Weekday"] = time_dataframe["Day or Week"].map(weekday_database)
        time_dataframe["This Month's 1st day"] = datetime.datetime(requested_date.year, requested_date.month, 1)
        time_dataframe["This Month's 1st day"] = pd.to_datetime(time_dataframe["This Month's 1st day"])
        time_dataframe["Next Month's 1st day"] = (time_dataframe["This Month's 1st day"] 
                                                + pd.DateOffset(months=1))

        for which_month in ["This", "Next"]:    # Running on month
            for i in range(5):  # Running on week
                # Find ith date of the month
                time_delta = pd.to_timedelta(((time_dataframe["Weekday"]
                                                - time_dataframe[f"{which_month} Month's 1st day"].dt.weekday \
                                                + 7) % 7) + 7 * i, unit='D')
                time_dataframe[f"{which_month} Week {i + 1}'s date"] = time_dataframe[f"{which_month} Month's 1st day"] \
                                                                    + time_delta
                
                # Check whether the date is in the same month
                not_same_month = time_dataframe[f"{which_month} Week {i + 1}'s date"].dt.month \
                                != time_dataframe[f"{which_month} Month's 1st day"].dt.month
                time_dataframe.loc[not_same_month, f"{which_month} Week {i + 1}'s date"] = None
                
                # Check whether it is working on that date or not
                time_dataframe.loc[~time_dataframe[f"Week {i + 1}"], f"{which_month} Week {i + 1}'s date"] = None
        

    def _add_current_next_dates(
        self,
        week_info_dataframe: pd.DataFrame,
        requested_date: pd.Timestamp
    ) -> pd.DataFrame:
        """
        Given week information on when they open, add the current and next opening dates
        """
        week_info_dataframe["Open on Requested Date"] = False
        for i in range(5):
            week_info_dataframe.loc[
                    week_info_dataframe[f"This Week {i + 1}'s date"].dt.date == requested_date, 
                    "Open on Requested Date"
            ] = True

        week_info_dataframe["Open on Next Date"] = False
        for which_month in ["Next", "This"]:    # Running on month
            for i in range(4, -1, -1):  # Running on week
                week_info_dataframe.loc[
                        week_info_dataframe[f"{which_month} Week {i + 1}'s date"] > pd.to_datetime(requested_date), 
                        "Open on Next Date"
                ] = week_info_dataframe[f"{which_month} Week {i + 1}'s date"].dt.date 

        # Solving Every Other Week: Find Opened on current date and next opening date
        week_info_dataframe["Time diff Req Date"] = (pd.to_datetime(requested_date).date() - week_info_dataframe["Date_of_Last_SO"]).apply(lambda x: x.days) % 14
        week_info_dataframe.loc[week_info_dataframe["Time diff Req Date"] == 0, "Time diff Req Date"] = 14
        week_info_dataframe.loc[(week_info_dataframe["Time diff Req Date"] == 0) &
                        (week_info_dataframe["Frequency"] == "Every Other Week")
                        , "Open on Current Date"] = True

        week_info_dataframe.loc[week_info_dataframe["Frequency"] == "Every Other Week" 
                        , "Open on Next Date"] = (pd.Timestamp(requested_date) + pd.to_timedelta(week_info_dataframe["Time diff Req Date"], unit='D')).dt.date
        week_info_dataframe[week_info_dataframe["Frequency"] == "Every Other Week"]

        # For a certain agency ref, if there are multiple dates, take the minimum date
        week_info_dataframe["Open on Next Date"] = week_info_dataframe.groupby("agency_ref")["Open on Next Date"].transform('min')

        # Remove unnecessary columns
        result_date_dataframe = week_info_dataframe.copy()
        result_date_dataframe.drop(columns=[
            "Day or Week", 
            "Weekday", 
            "This Month's 1st day", 
            "Next Month's 1st day",
            "Week 1",
            "Week 2",
            "Week 3",
            "Week 4",
            "Week 5",
            "This Week 1's date",
            "This Week 2's date",
            "This Week 3's date",
            "This Week 4's date",
            "This Week 5's date",
            "Next Week 1's date",
            "Next Week 2's date",
            "Next Week 3's date",
            "Next Week 4's date",
            "Next Week 5's date"
        ], inplace=True)

        return 

    def _filter_time_information(
        self,
        date_info_dataframe: pd.DataFrame,
        requested_time: str
    ) -> pd.DataFrame:
        """
        Given the dataframe containing the date information, filter the dataframe based on the time information
        """
        start_time_information = {
            "morning": '6:00:00',
            "afternoon": '12:00:00',
            "evening": '17:00:00',
            "night": '19:00:00'
        }

        end_time_information = {
            "morning": '11:59:59',
            "afternoon": '16:59:59',
            "evening": '18:59:59',
            "night": '23:59:59'
        }

        date_info_dataframe["Max Starting Time"] = start_time_information[requested_time]
        date_info_dataframe["Max Ending Time"] = end_time_information[requested_time]

        for col in ["Starting Time", "Ending Time", "Max Starting Time", "Max Ending Time"]:
            date_info_dataframe[col] = pd.to_datetime(date_info_dataframe[col], format="%H:%M:%S").dt.time

        # if max(Starting Time, asked_time_start) > min(Ending Time, asked_time_end): Time does not exist
        date_info_dataframe.loc[date_info_dataframe["Max Starting Time"] < date_info_dataframe["Starting Time"],
                                    "Max Starting Time"] = date_info_dataframe["Starting Time"]
        date_info_dataframe.loc[date_info_dataframe["Max Ending Time"] > date_info_dataframe["Ending Time"],
                                    "Max Ending Time"] = date_info_dataframe["Ending Time"]

        # date_info_dataframe["Max Starting Time"] = pd.to_datetime(date_info_dataframe["Max Starting Time"], format="%H:%M:%S").dt.time
        # date_info_dataframe["Max Ending Time"] = pd.to_datetime(date_info_dataframe["Max Ending Time"], format="%H:%M:%S").dt.time
        date_info_dataframe.loc[date_info_dataframe["Max Starting Time"] > date_info_dataframe["Max Ending Time"],
                                    "Open on Requested Date"] = False

        date_info_dataframe.drop(columns=[
            "Max Starting Time",
            "Max Ending Time"
        ], inplace=True)
        
        return date_info_dataframe 

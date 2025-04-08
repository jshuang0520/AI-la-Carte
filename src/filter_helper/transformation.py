import pandas as pd
import json
import re
import numpy as np

def load_table_data(excel_path):
    """Load the Excel file (cafb_markets_shopping_partners.xlsx) into a DataFrame."""
    return pd.read_excel(excel_path)

def load_dict_data(json_path):
    """Load the list of dictionaries from JSON into a DataFrame."""
    with open(json_path, "r") as f:
        data = json.load(f)  # data is a list of dicts
    df = pd.json_normalize(data)
    return df

# A helper function to pick the first non-null value from multiple columns
def first_non_null(*vals):
    for val in vals:
        if pd.notna(val):
            return val
    return None

# A helper function to parse a "XX of the Month" pattern or 'Every week' from the Hours_<Day> text.
def parse_frequency(hours_str):
    if not isinstance(hours_str, str):
        return None
    
    # Look for patterns like "3rd of the Month", "1st of the Month", "Every week" etc.
    # You can extend this with more advanced parsing if needed.
    match = re.search(r'(\d+(?:st|nd|rd|th) of the Month)', hours_str)
    if match:
        return match.group(1)
    
    if "Every week" in hours_str:
        return "Every week"
    
    # Fallback
    return None

# Map each Day to the relevant columns in df_dict
day_map = {
    "Monday": {
        "start_cols": ["start1_Monday", "start2_Monday", "start3_Monday"],
        "end_cols":   ["end1_Monday",   "end2_Monday",   "end3_Monday"],
        "hours_col":  "Hours_Monday"
    },
    "Tuesday": {
        "start_cols": ["start1_Tuesday", "start2_Tuesday", "start3_Tuesday"],
        "end_cols":   ["end1_Tuesday",   "end2_Tuesday",   "end3_Tuesday"],
        "hours_col":  "Hours_Tuesday"
    },
    "Wednesday": {
        "start_cols": ["start1_Wednesday", "start2_Wednesday", "start3_Wednesday"],
        "end_cols":   ["end1_Wednesday",   "end2_Wednesday",   "end3_Wednesday"],
        "hours_col":  "Hours_Wednesday"
    },
    "Thursday": {
        "start_cols": ["start1_Thursday", "start2_Thursday", "start3_Thursday"],
        "end_cols":   ["end1_Thursday",   "end2_Thursday",   "end3_Thursday"],
        "hours_col":  "Hours_Thursday"
    },
    "Friday": {
        "start_cols": ["start1_Friday", "start2_Friday", "start3_Friday"],
        "end_cols":   ["end1_Friday",   "end2_Friday",   "end3_Friday"],
        "hours_col":  "Hours_Friday"
    },
    "Saturday": {
        "start_cols": ["start1_Saturday", "start2_Saturday", "start3_Saturday"],
        "end_cols":   ["end1_Saturday",   "end2_Saturday",   "end3_Saturday"],
        "hours_col":  "Hours_Saturday"
    },
    "Sunday": {
        "start_cols": ["start1_Sunday", "start2_Sunday", "start3_Sunday"],
        "end_cols":   ["end1_Sunday",   "end2_Sunday",   "end3_Sunday"],
        "hours_col":  "Hours_Sunday"
    }
}

def fill_missing_values(row):
    """
    A function to fill the missing values in Starting Time, Ending Time, and Frequency
    by looking up the merged dictionary columns according to Day or Week.
    """
    day = row["Day or Week"]
    # Only fill if the day is recognized
    if day in day_map:
        day_info = day_map[day]
        
        # Fill Starting Time if NaN
        if pd.isna(row["Starting Time"]):
            st = first_non_null(*(row[col] for col in day_info["start_cols"] if col in row))
            if pd.notna(st):
                row["Starting Time"] = st
        
        # Fill Ending Time if NaN
        if pd.isna(row["Ending Time"]):
            et = first_non_null(*(row[col] for col in day_info["end_cols"] if col in row))
            if pd.notna(et):
                row["Ending Time"] = et
        
        # Fill Frequency if NaN
        if pd.isna(row["Frequency"]):
            hours_str = row.get(day_info["hours_col"], None)
            freq_val = parse_frequency(hours_str)
            if freq_val:
                row["Frequency"] = freq_val
    
    return row

def main():
    # Example usage:
    excel_path = "cafb_markets_shopping_partners.xlsx"
    dict_json_path = "arcgis_data.json"  # your second dataset in JSON format

    # 1. Load the table from Excel
    df_table = load_table_data(excel_path)

    # 2. Load the dictionary data from JSON
    df_dict = load_dict_data(dict_json_path)

    # 3. Merge on Agency ID = agency_ref
    df_merged = pd.merge(
        df_table,
        df_dict,
        left_on="Agency ID",
        right_on="agency_ref",
        how="left"
    )

    # 4. Apply the fill_missing_values function row-wise
    df_filled = df_merged.apply(fill_missing_values, axis=1)

    # 5. (Optional) If you only want the final columns from the original table, you can select them:
    # df_final = df_filled[["Agency ID", "Agency Name", "Shipping Address", 
    #                       "Day or Week", "Starting Time", "Ending Time", "Frequency"]]
    # For demonstration, let's keep everything:
    df_final = df_filled

    # 6. Save or do further processing
    df_final.to_excel("cafb_mkt_sp_filled.xlsx", index=False)
    print(df_final.head())
    print("Data transformation complete. Output saved to 'cafb_markets_shopping_partners_filled.xlsx'.")

if __name__ == "__main__":
    main()

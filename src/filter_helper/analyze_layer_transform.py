import pandas as pd
import numpy as np
from arcgis.features import FeatureLayer
import copy

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def extract_data(layer_url):
    """Extract data from the feature layer."""
    layer = FeatureLayer(layer_url)
    results = layer.query(where="1=1", return_geometry=True)
    all_attributes = [feature.attributes for feature in results]
    return pd.DataFrame(all_attributes)


def remove_duplicates(row, columns):
    """Remove duplicates while preserving order."""
    starts = [row[col] for col in columns]
    unique_starts = list(dict.fromkeys(filter(pd.notna, starts)))
    return pd.Series(unique_starts + [None] * (len(columns) - len(unique_starts)))


def split_rows(df, columns):
    """Split rows based on '\\r\\n' in specified columns."""
    expanded_rows = []
    for _, row in df.iterrows():
        max_splits = max(
            [len(str(row[col]).split("\r\n")) for col in columns if col in df.columns]
        )
        for i in range(max_splits):
            new_row = row.copy()
            for col in columns:
                if col in df.columns:
                    split_values = str(row[col]).split("\r\n")
                    new_row[col] = split_values[i] if i < len(split_values) else None
            expanded_rows.append(new_row)
    return pd.DataFrame(expanded_rows)


def main():
    # Extract data
    layer_url = (
        "https://services.arcgis.com/oCjyzxNy34f0pJCV/arcgis/rest/services/"
        "Active_Agencies_Last_45_Days/FeatureServer/0"
    )
    data = extract_data(layer_url)

    # Remove duplicates
    removable_columns = [
        col for col in data.columns for day in WEEKDAYS if day in col
    ]
    data.drop_duplicates(inplace=True)

    # Convert data
    weekday_set_data = pd.DataFrame(columns=data.columns)
    for day in WEEKDAYS:
        temp_data = data[data[f"Hours_{day}"].notna()].copy()
        if not temp_data.empty:
            temp_data["Day of week"] = day
            temp_data["Hours"] = temp_data[f"Hours_{day}"]
            temp_data["ByAppointmentOnly"] = temp_data[f"ByAppointmentOnly_{day}"]
            temp_data["ResidentsOnly"] = temp_data[f"ResidentsOnly_{day}"]
            temp_data["Notes"] = temp_data[f"Notes_{day}"]
            temp_data["Reqs"] = temp_data[f"Reqs_{day}"]
            temp_data["start1"] = temp_data[f"start1_{day}"]
            temp_data["start2"] = temp_data[f"start2_{day}"]
            temp_data["start3"] = temp_data[f"start3_{day}"]
            temp_data["end1"] = temp_data[f"end1_{day}"]
            temp_data["end2"] = temp_data[f"end2_{day}"]
            temp_data["end3"] = temp_data[f"end3_{day}"]
            weekday_set_data = pd.concat([weekday_set_data, temp_data], ignore_index=True)

    weekday_set_data.drop(columns=removable_columns, inplace=True)

    # Add rows with no hours mentioned
    hours_columns = [col for col in removable_columns if "Hours" in col]
    no_hours_mentioned = data[data[hours_columns].isna().all(axis=1)]
    weekday_set_data = pd.concat([weekday_set_data, no_hours_mentioned], ignore_index=True)
    weekday_set_data.reset_index(drop=True, inplace=True)

    # Remove duplicates in start1, start2, start3 columns
    time_set_data = copy.deepcopy(weekday_set_data)
    time_set_data[["start1", "start2", "start3"]] = time_set_data.apply(
        remove_duplicates, axis=1, args=(["start1", "start2", "start3"],)
    )
    time_set_data[["end1", "end2", "end3"]] = time_set_data.apply(
        remove_duplicates, axis=1, args=(["end1", "end2", "end3"],)
    )

    # Split rows based on '\r\n'
    columns_to_split = ["Notes", "ByAppointmentOnly", "Reqs", "ResidentsOnly", "Hours"]
    expanded_data = split_rows(time_set_data, columns_to_split)
    expanded_data.reset_index(drop=True, inplace=True)

    # Setting Frequency, Additional Notes, Start and Ending time
    frequency_data = expanded_data.copy()
    frequency_data[["Opening_Hours", "Frequency_Additional_Notes"]] = frequency_data[
        "Hours"
    ].str.split(";", expand=True)
    frequency_data["Frequency"] = (
        frequency_data["Frequency_Additional_Notes"]
        .str.replace(r"\(.*\)", "", regex=True)
        .str.strip()
    )
    frequency_data["Additional_Notes"] = frequency_data[
        "Frequency_Additional_Notes"
    ].str.extract(r"\((.*)\)")[0].str.strip()
    frequency_data[["Start_Time", "End_Time"]] = frequency_data[
        "Opening_Hours"
    ].str.split("to", expand=True)
    frequency_data["Start_Time"] = frequency_data["Start_Time"].str.strip()
    frequency_data["End_Time"] = frequency_data["End_Time"].str.strip()
    frequency_data.reset_index(drop=True, inplace=True)


if __name__ == "__main__":
    main()

import requests
import pandas as pd
from typing import List

BASE_URL = "http://backend:8000"


def get_all_faculties():
    response = requests.get(f"{BASE_URL}/faculties/")
    if response.status_code == 200:
        return response.json()
    return []


def get_latest_ia_usages():
    response = requests.get(f"{BASE_URL}/ia-usages/")
    if response.status_code == 200:
        return response.json()
    return []


def get_historical_data_by_faculty(faculty_name):
    response = requests.get(f"{BASE_URL}/ia-usage-history/{faculty_name}")
    if response.status_code == 200:
        return response.json()
    return []


def get_all_historical_data():
    response = requests.get(f"{BASE_URL}/ia-usages-history/all")
    if response.status_code == 200:
        response_data = response.json()
        return process_data_for_line_chart_race(response_data)
    return []


def process_data_for_line_chart_race(response_data):
    try:
        flattened_data = [
            {"date": entry['date'], "usage_percentage": entry['usage_percentage'], "faculty": entry['usage']['faculty']}
            for entry in response_data
        ]
        df = pd.DataFrame(flattened_data)
        df['date'] = pd.to_datetime(df['date'])

        # Eliminar filas con valores nulos en las columnas clave
        df.dropna(subset=['faculty', 'usage_percentage', 'date'], inplace=True)
        df = df.sort_values(by=['faculty', 'date']).reset_index(drop=True)
        return df
    except KeyError as e:
        print(f"KeyError encountered: {e}")
        return []
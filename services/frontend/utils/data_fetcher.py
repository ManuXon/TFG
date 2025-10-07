import requests
import pandas as pd

# This is the internal Docker hostname of your backend service (from docker-compose)
BASE_URL = "http://backend:8000/api"


def get_spike_map_data(category="All", gender=None, teaching_experience=None, ub_profile=None):
    """Fetch spike map data from the backend FastAPI service."""
    try:
        params = {
            "category": category,
            "gender": gender,
            "teaching_experience": teaching_experience,
            "ub_profile": ub_profile
        }
        response = requests.get(f"{BASE_URL}/spike-map", params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except Exception as e:
        print(f"❌ Error fetching spike map data: {e}")
        return pd.DataFrame()


def get_treemap_data(gender=None, teaching_experience=None, ub_profile=None):
    """Fetch treemap data from the backend FastAPI service."""
    try:
        params = {
            "gender": gender,
            "teaching_experience": teaching_experience,
            "ub_profile": ub_profile
        }
        response = requests.get(f"{BASE_URL}/treemap-data", params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except Exception as e:
        print(f"❌ Error fetching treemap data: {e}")
        return pd.DataFrame()


def get_knowledge_distribution(faculty_name):
    """Fetch the knowledge-level distribution for a given faculty."""
    try:
        response = requests.get(f"{BASE_URL}/faculty/{faculty_name}/knowledge-distribution")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching knowledge distribution: {e}")
        return {"categories": [], "values": []}


def get_sankey_chart_data():
    """Fetch Sankey chart data from the backend API."""
    try:
        response = requests.get(f"{BASE_URL}/sankey-data")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching Sankey data: {e}")
        return {"sources": [], "targets": [], "values": [], "labels": [], "faculty_colors": {}}

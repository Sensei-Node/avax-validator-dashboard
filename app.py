import json
from datetime import datetime

import pycountry
import requests
from flask import Flask, render_template, jsonify


with open('config.json', 'r') as config_file:
    config = json.load(config_file)

VALIDATORS = config['validators']
REFRESH_INTERVAL_MINUTES = config['refresh_interval_minutes']
REFRESH_INTERVAL_MS = REFRESH_INTERVAL_MINUTES * 60 * 1000
API_ENDPOINT = (
    "https://api.avascan.info/v2/network/mainnet/staking/validations?nodeIds="
    + ",".join(VALIDATORS)
    + "&status=active"
)
# Offset to convert ASCII letters to Regional Indicator Symbols (flag emojis)
REGIONAL_INDICATOR_OFFSET = 127397
IP_GEOLOCATION_TIMEOUT_SECONDS = 5


app = Flask(__name__)

# Cache for last known uptime values
uptime_cache = {validator: 0.0 for validator in VALIDATORS}


def country_code_to_flag(country_code):
    """Convert ISO country code to flag emoji."""
    if not country_code or len(country_code) != 2:
        return ""
    return "".join(chr(ord(c) + REGIONAL_INDICATOR_OFFSET) for c in country_code.upper())


def get_country_code_from_name(country_name):
    """Get ISO country code from country name."""
    try:
        country_obj = pycountry.countries.search_fuzzy(country_name)[0]
        return country_obj.alpha_2
    except (LookupError, AttributeError, IndexError):
        return ""


def get_location_from_ip(node_ip):
    """Fetch location data using IP geolocation service."""
    try:
        ip_info_response = requests.get(
            f"https://ipinfo.io/{node_ip}/json",
            timeout=IP_GEOLOCATION_TIMEOUT_SECONDS
        )
        ip_info_data = ip_info_response.json()
        city = ip_info_data.get("city", "Unknown")
        country_code = ip_info_data.get("country", "Unknown")
        
        if country_code != "Unknown":
            try:
                country = pycountry.countries.get(alpha_2=country_code).name
            except (AttributeError, KeyError):
                country = country_code
        else:
            country = "Unknown"
            country_code = ""
        
        return f"{city}, {country}", country_code
    except Exception:
        return "Unknown, Unknown", ""


def format_location(location_city, location_country, node_ip):
    """Determine and format location string with flag emoji."""
    country_code = ""
    
    if location_city and location_country:
        country_code = get_country_code_from_name(location_country)
        location = f"{location_city}, {location_country}"
    elif node_ip:
        location, country_code = get_location_from_ip(node_ip)
    else:
        location = "Unknown, Unknown"
    
    flag_emoji = country_code_to_flag(country_code)
    if flag_emoji:
        location = f"{location} {flag_emoji}"
    
    return location


def format_uptime(avg_uptime, node_id):
    """Format uptime percentage, using cache if unavailable."""
    if isinstance(avg_uptime, (int, float)):
        formatted_uptime = round(avg_uptime * 100, 2)
        if node_id:
            uptime_cache[node_id] = formatted_uptime
        return formatted_uptime
    else:
        return uptime_cache.get(node_id, 0.0)


def format_stake(stake_value):
    """Convert stake from nAVAX to AVAX."""
    if stake_value and stake_value != "Unknown":
        return round(int(stake_value) / 1_000_000_000, 2)
    return "Unknown"


def format_expiration_date(end_time):
    """Format ISO datetime to readable string."""
    if end_time == "Unknown":
        return "Unknown"
    
    try:
        dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        return dt.strftime("%b %d, %Y %H:%M UTC")
    except Exception:
        return "Unknown"


def parse_validator_item(item):
    """Parse a single validator item and return formatted data."""
    node_id = item.get("nodeId")
    if not node_id:
        return None, None
    
    node_info = item.get("node", {})
    location_data = node_info.get("location", {})
    
    location_city = location_data.get("city", "")
    location_country = location_data.get("country", "")
    node_ip = node_info.get("ip", "")
    avg_uptime = node_info.get("uptime", {}).get("avg", "Unknown")
    end_time = item.get("endTime", "Unknown")
    stake_from_self = item.get("stake", {}).get("fromSelf", "Unknown")
    stake_from_delegations = item.get("stake", {}).get("fromDelegations", "Unknown")
    
    formatted_data = {
        "location": format_location(location_city, location_country, node_ip),
        "uptime": format_uptime(avg_uptime, node_id),
        "expiration_date": format_expiration_date(end_time),
        "stake_from_self": format_stake(stake_from_self),
        "stake_from_delegations": format_stake(stake_from_delegations),
    }
    
    return node_id, formatted_data


def fetch_validator_data():
    """Fetch raw validator data from Avascan API."""
    headers = {"accept": "application/json"}
    response = requests.get(API_ENDPOINT, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_uptime():
    """Fetch and format validator uptime data."""
    try:
        data = fetch_validator_data()
        uptime_data = {}
        
        for item in data.get("items", []):
            node_id, formatted_data = parse_validator_item(item)
            if node_id and formatted_data:
                uptime_data[node_id] = formatted_data
        
        return uptime_data
    
    except Exception as e:
        return {validator: f"Error {e}" for validator in VALIDATORS}


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/data")
def data():
    uptime_data = fetch_uptime()
    return jsonify(uptime_data)


@app.route("/config")
def get_config():
    return jsonify({"refresh_interval_ms": REFRESH_INTERVAL_MS})


if __name__ == "__main__":
    app.run(debug=False)

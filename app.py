import json
import pycountry
import requests

from datetime import datetime
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

def fetch_uptime():
    try:
        headers = {"accept": "application/json"}
        response = requests.get(API_ENDPOINT, headers=headers)
        data = response.json()

        uptime_data = {}
        for item in data.get("items", []):
            node_id = item.get("nodeId")
            node_info = item.get("node", {})
            location_data = node_info.get("location", {})
            location_city = location_data.get("city", "")
            location_country = location_data.get("country", "")
            node_ip = node_info.get("ip", "")
            avg_uptime = node_info.get("uptime", {}).get("avg", "Unknown")
            end_time = item.get("endTime", "Unknown")
            stake_from_self = item.get("stake", {}).get("fromSelf", "Unknown")
            stake_from_delegations = item.get("stake", {}).get("fromDelegations", "Unknown")

            # Processing values to avoid errors in conversions
            # Use cached value if `avg_uptime` is unknown, otherwise update cache
            if isinstance(avg_uptime, (int, float)):
                formatted_uptime = round(avg_uptime * 100, 2)
                if node_id:
                    uptime_cache[node_id] = formatted_uptime
            else:
                formatted_uptime = uptime_cache.get(node_id, 0.0)
            
            formatted_stake_from_self = (
                round(int(stake_from_self) / 1_000_000_000, 2)
                if stake_from_self
                else "Unknown"
            )
            formatted_stake_from_delegations = (
                round(int(stake_from_delegations) / 1_000_000_000, 2)
                if stake_from_delegations
                else "Unknown"
            )

            # Determine location: use API data or fallback to IP geolocation
            country_code = ""
            if location_city and location_country:
                # Try to get country code from country name
                try:
                    country_obj = pycountry.countries.search_fuzzy(location_country)[0]
                    country_code = country_obj.alpha_2
                except (LookupError, AttributeError, IndexError):
                    country_code = ""
                location = f"{location_city}, {location_country}"
            elif node_ip:
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
                    location = f"{city}, {country}"
                except Exception:
                    location = "Unknown, Unknown"
                    country_code = ""
            else:
                location = "Unknown, Unknown"
                country_code = ""
            
            flag_emoji = country_code_to_flag(country_code)
            if flag_emoji:
                location = f"{location} {flag_emoji}"

            # Format expiration date
            if end_time != "Unknown":
                try:
                    dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    formatted_end_time = dt.strftime("%b %d, %Y %H:%M UTC")
                except Exception:
                    formatted_end_time = "Unknown"
            else:
                formatted_end_time = "Unknown"

            if node_id:
                uptime_data[node_id] = {
                    "location": location,
                    "uptime": formatted_uptime,
                    "expiration_date": formatted_end_time,
                    "stake_from_self": formatted_stake_from_self,
                    "stake_from_delegations": formatted_stake_from_delegations,
                }

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

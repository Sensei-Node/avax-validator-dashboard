import pycountry
import requests

from datetime import datetime
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# List of Validators (Add more Node IDs here)
VALIDATORS = [
    "NodeID-F3SZA2ZNdRjTBe3GYyRQFDaCXB3DyaZQQ",  # Sensei 1
    "NodeID-2Coj79FAu7rPdSdYdJ27CqTr1K2p45gze",  # Sensei 2
    "NodeID-9Efcx2E5uEHZqZSTWT1jPd8DfEkJaZeGj",  # Sensei 3
    "NodeID-8mirL2rorHYSEbkBxu8TwodvpN29RrNY3",  # Sensei 4
]

# Construct API Endpoint dynamically
API_ENDPOINT = (
    "https://api.avascan.info/v2/network/mainnet/staking/validations?nodeIds="
    + ",".join(VALIDATORS)
    + "&status=active"
)

# Cache for last known uptime values
uptime_cache = {validator: 0.0 for validator in VALIDATORS}


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
            if location_city and location_country:
                location = f"{location_city}, {location_country}"
            elif node_ip:
                try:
                    ip_info_response = requests.get(
                        f"https://ipinfo.io/{node_ip}/json",
                        timeout=5
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
                    location = f"{city}, {country}"
                except Exception:
                    location = "Unknown, Unknown"
            else:
                location = "Unknown, Unknown"

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


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, jsonify
import requests
import pycountry

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
            name = item.get("name", "⚠️ Unknown")
            
            avg_uptime = node_info.get("uptime", {}).get("avg", "N/A")
            location_data = node_info.get("location", {})
            location_city = location_data.get("city", "")
            location_country = location_data.get("country", "")
            node_ip = node_info.get("ip", "")
            
            stake_from_self = item.get("stake", {}).get("fromSelf", "N/A")
            stake_from_delegations = item.get("stake", {}).get("fromDelegations", "N/A")

            # Processing values to avoid errors in conversions
            # Use cached value if `avg_uptime` is N/A, otherwise update cache
            if isinstance(avg_uptime, (int, float)):
                formatted_uptime = round(avg_uptime * 100, 2)
                if node_id:
                    uptime_cache[node_id] = formatted_uptime
            else:
                formatted_uptime = uptime_cache.get(node_id, 0.0)
            
            formatted_stake_from_self = (
                round(int(stake_from_self) / 1_000_000_000, 2)
                if stake_from_self
                else "N/A"
            )
            formatted_stake_from_delegations = (
                round(int(stake_from_delegations) / 1_000_000_000, 2)
                if stake_from_delegations
                else "N/A"
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

            if node_id:
                uptime_data[node_id] = {
                    "uptime": formatted_uptime,
                    "name": name,
                    "location": location,
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

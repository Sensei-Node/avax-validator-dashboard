from flask import Flask, render_template, jsonify
import requests

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
            avg_uptime = item.get("node", {}).get("uptime", {}).get("avg", "N/A")
            name = item.get("name", "⚠️ Unknown")
            location_city = (
                item.get("node", {}).get("location", {}).get("city", "Unknown")
            )
            location_country = (
                item.get("node", {}).get("location", {}).get("country", "Unknown")
            )
            location = f"{location_city}, {location_country}"
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

            if node_id:
                uptime_data[node_id] = {
                    "uptime": formatted_uptime,
                    "name": name,
                    "location": location,
                    "stake_from_self": formatted_stake_from_self,
                    "stake_from_delegations": formatted_stake_from_delegations,
                }

            # Handling for validators that not return locations
            if node_id == "NodeID-2Coj79FAu7rPdSdYdJ27CqTr1K2p45gze":
                if uptime_data[node_id]["location"] == "Unknown, Unknown":
                    ip_info_response = requests.get(
                        "https://ipinfo.io/158.255.76.58/json"
                    )
                    ip_info_data = ip_info_response.json()
                    city = ip_info_data.get("city", "Unknown")
                    country = "Nigeria"  # Hardcode Nigeria (API doesn't support)
                    uptime_data[node_id]["location"] = f"{city}, {country}"

            elif node_id == "NodeID-9Efcx2E5uEHZqZSTWT1jPd8DfEkJaZeGj":
                if uptime_data[node_id]["location"] == "Unknown, Unknown":
                    ip_info_response = requests.get(
                        "https://ipinfo.io/160.202.130.67/json"
                    )
                    ip_info_data = ip_info_response.json()
                    city = ip_info_data.get("city", "Unknown")
                    country = "Brasil"  # Hardcode Brasil (API doesn't support)
                    uptime_data[node_id]["location"] = f"{city}, {country}"

            elif node_id == "NodeID-8mirL2rorHYSEbkBxu8TwodvpN29RrNY3":
                if uptime_data[node_id]["location"] == "Unknown, Unknown":
                    ip_info_response = requests.get(
                        "https://ipinfo.io/103.88.234.47/json"
                    )
                    ip_info_data = ip_info_response.json()
                    city = ip_info_data.get("city", "Unknown")
                    country = "Mexico"  # Hardcode Mexico (API doesn't support)
                    uptime_data[node_id]["location"] = f"{city}, {country}"

            elif node_id == "NodeID-F3SZA2ZNdRjTBe3GYyRQFDaCXB3DyaZQQ":
                if uptime_data[node_id]["location"]:
                    ip_info_response = requests.get(
                        "https://ipinfo.io/160.202.130.45/json"
                    )
                    ip_info_data = ip_info_response.json()
                    city = ip_info_data.get("city", "Unknown")
                    country = "Brasil"  # Hardcode Brasil again (API doesn't support)
                    # Hardcode specified values
                    if city != "Unknown":
                        city = "São Paulo"
                    if country != "Unknown":
                        country = "Brasil"
                    uptime_data[node_id]["location"] = f"{city}, {country}"

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

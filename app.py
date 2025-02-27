from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

# List of Validators (Add more Node IDs here)
VALIDATORS = [
    # "NodeID-F3SZA2ZNdRjTBe3GYyRQFDaCXB3DyaZQQ", # Sensei (does not appear on the dashboard because it is inactive)
    "NodeID-4G6U36ehMMYjJ3C9gzLmYRzQFho8c4U4w",
    "NodeID-2jz2UxTN4JBu5qxWi4gwtqyQPLizj6Xka",
    "NodeID-BhvvT3sTYTF8Gi6ebafnHyAGLLB1pj6PW",
    "NodeID-DqggQ5z3g89eJszSnyTWYBejggS4piCsH",
    "NodeID-4cwQT5hvhnhgYM7kJia4MK5kT8XLVZSNz",
]

# Construct API Endpoint dynamically
API_ENDPOINT = (
    "https://api.avascan.info/v2/network/mainnet/staking/validations?nodeIds="
    + ",".join(VALIDATORS)
    + "&status=active"
)


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
            formatted_uptime = (
                round(avg_uptime * 100, 2)
                if isinstance(avg_uptime, (int, float))
                else "N/A"
            )
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

from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

# List of Validators (Add more Node IDs here)
VALIDATORS = [
    "NodeID-F3SZA2ZNdRjTBe3GYyRQFDaCXB3DyaZQQ",
    "NodeID-4G6U36ehMMYjJ3C9gzLmYRzQFho8c4U4w"  # Example additional validator
]

# Construct API Endpoint dynamically
API_ENDPOINT = "https://api.avascan.info/v2/network/mainnet/staking/validations?nodeIds=" + ",".join(VALIDATORS) + "&status=active"

def fetch_uptime():
    try:
        headers = {"accept": "application/json"}
        response = requests.get(API_ENDPOINT, headers=headers)
        data = response.json()
        
        uptime_data = {}
        for item in data.get("items", []):
            node_id = item.get("nodeId")
            avg_uptime = item.get("node", {}).get("uptime", {}).get("avg", "N/A")
            name = item.get("name", "Unknown")
            location = item.get("node", {}).get("location", {}).get("city", "Unknown") + ", " + item.get("node", {}).get("location", {}).get("country", "Unknown")
            stake_from_self = item.get("stake", {}).get("fromSelf", "N/A")
            stake_from_delegations = item.get("stake", {}).get("fromDelegations", "N/A")
            
            if node_id and isinstance(avg_uptime, (int, float)):
                uptime_data[node_id] = {
                    "uptime": round(avg_uptime * 100, 2),  # Convert to percentage
                    "name": name,
                    "location": location,
                    "stake_from_self": round(int(stake_from_self) / 1000000000, 2),
                    "stake_from_delegations": round(int(stake_from_delegations) / 1000000000, 2)
                }
            else:
                uptime_data[node_id] = "N/A"
        
        return uptime_data
    except Exception as e:
        return {validator: "Error" for validator in VALIDATORS}

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/data')
def data():
    uptime_data = fetch_uptime()
    return jsonify(uptime_data)

if __name__ == '__main__':
    app.run(debug=True)

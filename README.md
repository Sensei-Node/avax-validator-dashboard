# Avalanche Validator Dashboard

This is a simple Flask web application that monitors the uptime of multiple Avalanche validators using data from Avascan.

![dashboard](static/dashboard.png)

## Features
- Fetches validator uptime dynamically
- Displays validator details including:
  - Name
  - Location
  - Uptime percentage
  - Stake from self
  - Stake from delegations
- Auto-refresh every 10 minutes

## Installation

### Prerequisites
- Python 3.7+
- pip

### Clone the repository
```shell
git clone https://github.com/PixelNoob/avax-validator-dashboard.git
```

Go to the project:

```shell
cd avalanche-validator-dashboard
```

### Install dependencies

Create your `.venv` folder and use:
```sh
pip install -r requirements.txt
```

## Usage

### Run the Flask App
```sh
python app.py
```

or 

```sh
python3 app.py
```

### Open in browser

Once the server is running, open it locally:
```
http://127.0.0.1:5000/
```

## Project structure

```
/avax-validator-dashboard/
├── app.py                # Main Flask application
├── requirements.txt      # Required dependencies
├── static/               # Static files (e.g., favicon)
│   ├── avax.ico          # Avax favicon
│   ├── sensei.png        # SenseiNode logo
│   ├── dashboard.png     # Dashboard image example
├── templates/            # HTML templates
│   ├── dashboard.html    # Main dashboard UI
└── README.md             # Project documentation
```

## API endpoint used
This app fetches data from:
```
https://api.avascan.info/v2/network/mainnet/staking/validations?nodeIds=<NODE_IDS>&status=active
```

## Contributing
Feel free to add new features through an issue. PRs are welcome! 🚀

---
# Made with ❤️ by Avalanche Node Operators

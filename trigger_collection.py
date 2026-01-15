import requests
import json

# Trigger a run cycle for surface bot to collect data
try:
    response = requests.post('http://127.0.0.1:5000/api/bots/run-cycle', json={
        'bot_type': 'surface',
        'source_type': 'surface'
    })
    if response.status_code == 200:
        print("✅ Surface bot run cycle started")
    else:
        print(f"❌ Failed to start run cycle: {response.status_code}")
except Exception as e:
    print(f"❌ Error triggering collection: {e}")

# Also trigger for osint
try:
    response = requests.post('http://127.0.0.1:5000/api/bots/run-cycle', json={
        'bot_type': 'osint',
        'source_type': 'osint'
    })
    if response.status_code == 200:
        print("✅ OSINT bot run cycle started")
    else:
        print(f"❌ Failed to start OSINT run cycle: {response.status_code}")
except Exception as e:
    print(f"❌ Error triggering OSINT collection: {e}")

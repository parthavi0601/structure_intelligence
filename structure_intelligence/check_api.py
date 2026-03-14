import urllib.request
import json

try:
    with urllib.request.urlopen('http://localhost:8000/api/behavioral-metrics/B003') as response:
        data = json.loads(response.read().decode())
        if 'data' in data and len(data['data']) > 0:
            first_record = data['data'][0]
            with open('api_first_record.json', 'w') as f:
                json.dump(first_record, f, indent=4)
            print("Successfully saved api_first_record.json")
        else:
            print("No data or empty data returned.")
except Exception as e:
    print("Error:", e)

import requests
import json
import pandas as pd
import time
import sys

def get_pagerduty_api_key():
    """
    Prompt the user to enter their PagerDuty API key.
    """
    api_key = input("Enter your PagerDuty API key: ")
    return api_key

def get_service_id():
    """
    Prompt the user to enter a Service ID for filtering (optional).
    """
    service_id = input("Enter the Service ID to filter (leave empty to not use this filtering): ")
    return service_id

def fetch_pagerduty_data(api_key, offset=0, service_id=None):
    """
    Fetch PagerDuty data using the provided API key, optional offset, and optional Service ID filter.
    """
    url = 'https://api.pagerduty.com/incidents?include%5B%5D=first_trigger_log_entries'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Token token={api_key}',
        'Content-Type': 'application/json'
    }
    params = {
        'limit': 100,  # Set the limit to 100
        'offset': offset  # Optional offset for pagination
    }

    if service_id:
        params['service_ids[]'] = service_id

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching data: {response.status_code} - {response.text}")
            return None
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None

def save_to_json(data, filename):
    """
    Append the fetched data to an existing JSON file or create a new one.
    """
    try:
        with open(filename, 'r') as infile:
            existing_data = json.load(infile)
            existing_data['incidents'].extend(data['incidents'])
    except FileNotFoundError:
        existing_data = data

    with open(filename, 'w') as outfile:
        json.dump(existing_data, outfile, indent=4)
    print(f"Data appended to {filename}")

def convert_to_csv(data):
    """
    Convert the aggregated JSON data to a single CSV file.
    """
    flattened_data = []
    for incident in data['incidents']:
        # Extract relevant fields (customize as needed)
        flattened_row = [
            incident['incident_number'],
            incident['description'],
            incident['first_trigger_log_entry']['channel']['details'].get('customerName', ''),
            incident['status'],
            incident['first_trigger_log_entry']['channel']['cef_details'].get('severity', ''),
            incident['first_trigger_log_entry']['channel']['details'].get('awsAccountId', ''),
            incident['first_trigger_log_entry']['channel']['details'].get('awsRegion', ''),
            incident['first_trigger_log_entry']['channel']['details'].get('customerId', ''),
            incident['first_trigger_log_entry']['channel']['details'].get('environment', '')
        ]
        flattened_data.append(flattened_row)

    df = pd.DataFrame(flattened_data, columns=[
        'incident_number', 'Description', 'customerName', 'Status',
        'Severity', 'awsAccountId', 'awsRegion', 'customerId', 'environment'
    ])

    df.to_csv('pagerduty_final_data.csv', index=False)  # Use a consistent filename
    print("Data converted to pagerduty_final_data.csv")

def show_spinner():
    """
    Display a spinner to indicate program execution.
    """
    spinner = "|/-\\"
    for _ in range(10):
        sys.stdout.write("\r" + "Processing... " + spinner[_ % len(spinner)])
        sys.stdout.flush()
        time.sleep(0.1)
    print("\n")  # Add a newline after the spinner

def main():
    api_key = get_pagerduty_api_key()
    service_id = get_service_id()
    offset = 0
    all_data = {'incidents': []}  # Initialize an empty list to aggregate all incidents

    while True:
        data = fetch_pagerduty_data(api_key, offset, service_id)
        if not data:
            break
        all_data['incidents'].extend(data['incidents'])  # Append incidents to the aggregated list
        if 'more' in data and data['more']:
            offset += 100  # Increment offset for next page
        else:
            break  # No more pages, exit loop

    # Save the aggregated data to a consistent JSON filename
    save_to_json(all_data, 'pagerduty_aggregated_data.json')

    # Convert the aggregated JSON data to a single CSV file
    show_spinner()  # Display spinner
    convert_to_csv(all_data)

if __name__ == "__main__":
    main()

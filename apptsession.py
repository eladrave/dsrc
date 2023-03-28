import os
import requests
import csv
import pytz
from datetime import datetime, timedelta
import time


def get_appointments(session, url):
    r = session.get(url)
    data = r.json()
    return data


def get_appointment_details(session, url):
    r = session.get(url)
    data = r.json()
    return data


def main():
    api_key = os.environ['TUTORCRUNCHER_API_KEY']
    url = 'https://secure.tutorcruncher.com/api/appointments/'
    appointments = []

    now = datetime.now(pytz.utc)
    thirty_days_ago = now - timedelta(days=30)

    # Create a session and set the API key in the headers
    session = requests.Session()
    session.headers.update({'Authorization': f'token {api_key}'})

    # Get appointments from all pages
    while url:
        data = get_appointments(session, url)
        for appointment in data['results']:
            start = appointment['start']
            appointment_start = datetime.fromisoformat(start.replace('Z', '+00:00')).astimezone(pytz.utc)

            if thirty_days_ago <= appointment_start <= now:
                time.sleep(1)  # Add a delay between requests
                appointment_details = get_appointment_details(session, appointment['url'])

                coach_name = appointment_details['cjas'][0]['name'] if appointment_details['cjas'] else None
                client_name = appointment_details['rcras'][0]['paying_client_name'] if appointment_details['rcras'] else None
                client_status = appointment_details['rcras'][0]['status'] if appointment_details['rcras'] else None

                finish = appointment['finish']
                appointment_end = datetime.fromisoformat(finish.replace('Z', '+00:00')).astimezone(pytz.utc)

                appointments.append({
                    'appointment_id': appointment['id'],
                    'appointment_start': appointment_start,
                    'appointment_end': appointment_end,
                    'appointment_status': appointment['status'],
                    'coach_name': coach_name,
                    'client_name': client_name,
                    'client_status': client_status
                })
                print(f"Number of appointments: {len(appointments)}")

        url = data['next']

    # Write appointments to a CSV file
    with open('appointments.csv', mode='w', newline='') as csvfile:
        fieldnames = ['appointment_id', 'appointment_start', 'appointment_end', 'appointment_status', 'coach_name', 'client_name', 'client_status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for appointment in appointments:
            writer.writerow(appointment)

    print("Appointments written to appointments.csv")


if __name__ == '__main__':
    main()

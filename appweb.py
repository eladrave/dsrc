import os
import requests
import csv
import pytz
import time
from datetime import datetime, timedelta
from flask import Flask, request, send_file, render_template_string
import logging
from dotenv import load_dotenv
import os
import urllib.parse

load_dotenv()

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

HTML_TEMPLATE = '''
<!doctype html>
<html>
<head>
  <title>Appointment Report</title>
</head>
<body>
  <h1>Appointment Report</h1>
  <form action="/getreport" method="get">
    <div>
      <label for="days">Days:</label>
      <input type="number" id="days" name="days" value="7">
    </div>
    <div>
      <label for="coach">Coach:</label>
      <input type="text" id="coach" name="coach">
    </div>
    <div>
      <label for="client">Client:</label>
      <input type="text" id="client" name="client">
    </div>
    <button type="submit">Get Report</button>
  </form>
</body>
</html>
'''

def get_appointments(session, url, params=None):
    r = session.get(url, params=params)
    data = r.json()
    return data


def get_appointment_details(session, url):
    r = session.get(url)
    data = r.json()
    return data

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/getreport')
def get_report():
    days = int(request.args.get('days', 7))
    coach_filter = request.args.get('coach', None)
    client_filter = request.args.get('client', None)

    api_key = os.environ['TUTORCRUNCHER_API_KEY']
    url = 'https://secure.tutorcruncher.com/api/appointments/'
    appointments = []

    now = datetime.now(pytz.utc)
    days_ago = now - timedelta(days=days)

    # Create a session and set the API key in the headers
    session = requests.Session()
    session.headers.update({'Authorization': f'token {api_key}'})

    params = {
        'start_gte': days_ago.strftime('%m/%d/%Y'),
        'start_lte': now.strftime('%m/%d/%Y')
    }

    # Get appointments from all pages
    while url:
        data = get_appointments(session, url, params)
        data = get_appointments(session, url)
        for appointment in data['results']:
            start = appointment['start']
            appointment_start = datetime.fromisoformat(start.replace('Z', '+00:00')).astimezone(pytz.utc)

            if days_ago <= appointment_start:
                #time.sleep(1)  # Add a delay between requests
                appointment_details = get_appointment_details(session, appointment['url'])

                coach_name = appointment_details['cjas'][0]['name'] if appointment_details['cjas'] else None
                client_name = appointment_details['rcras'][0]['paying_client_name'] if appointment_details['rcras'] else None
                client_status = appointment_details['rcras'][0]['status'] if appointment_details['rcras'] else None

                if (coach_filter in [None, ''] or coach_name == coach_filter) and (client_filter in [None, ''] or client_name == client_filter):
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
                    logging.info(f"Appointment details: {appointment}")
        url = data['next']
        time.sleep(1)  # Add a delay between pagination requests

    # Write appointments to a CSV file
    file_name = f"appointments.{coach_filter}.{client_filter}.csv"
    with open(file_name, mode='w', newline='') as csvfile:
        fieldnames = ['appointment_id', 'appointment_start', 'appointment_end', 'appointment_status', 'coach_name', 'client_name', 'client_status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for appointment in appointments:
            writer.writerow(appointment)

    return send_file(file_name, as_attachment=True, max_age=0)


if __name__ == '__main__':
    app.run("0.0.0.0",port=5555,debug=True)

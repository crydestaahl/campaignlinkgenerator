from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
import requests
import pandas as pd
import os
import logging
import shutil
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['TEMPLATE_FILE'] = 'template_file'
socketio = SocketIO(app)

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s:%(message)s')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        api_key = request.form['api_key']
        username = request.form['username']
        password = request.form['password']
        eogrequestcode = request.form['eogrequestcode']
        campaign_id = request.form['campaign_id']
        communicationType = int(request.form['communicationType'])
        eventId = request.form['eventId']
        inventoryType = int(request.form['inventoryType'])
        inventory = int(request.form['inventory'])
        inventoryTags = request.form['inventoryTags']
        internalreference = request.form['internalreference']

        # Kontrollera om en fil laddades upp
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            # Läs Excel-filen
            df = pd.read_excel(file_path)
            names = df['Name'].tolist()
            results = []

            # Skicka API-anrop för varje namn i Excel-filen
            for i, name in enumerate(names):
                url = f"https://api.tickster.com/sv/api/0.4/crm/{eogrequestcode}/campaigns/{campaign_id}/communications?key={api_key}"
                payload = {
                    "name": name,
                    "communicationType": communicationType,
                    "eventId": eventId,
                    "inventoryType": inventoryType,
                    "inventory": inventory,
                    "inventoryTags": inventoryTags,
                    "internalreference": internalreference
                }
                headers = {
                    'Content-Type': 'application/json'
                }
                # Lägg till användarnamn och lösenord för Basic Authentication
                auth = (username, password)

                response = requests.post(url, json=payload, headers=headers, auth=auth)

                # Logga hela begäran inklusive headern
                logging.info(f"Sending request for {name}: URL: {url}, Payload: {payload}, Headers: {headers}, Auth: ({username}, {'*'*len(password)})")
                
                # Logga statuskod och fullständig respons
                logging.info(f"Response status code for {name}: {response.status_code}")
                logging.info(f"Response text for {name}: {response.text}")

                try:
                    response_data = response.json()
                    # Logga responsen
                    logging.info(f"Received JSON response for {name}: {response_data}")
                    
                    if response.status_code == 200:
                        url = response_data.get('url', '')
                        df.at[i, 'URL'] = url
                    else:
                        df.at[i, 'URL'] = 'Error'
                except requests.exceptions.JSONDecodeError:
                    df.at[i, 'URL'] = 'Invalid JSON response'
                    logging.error(f"Failed to decode JSON for {name}: {response.text}")
                
                results.append(response.text)

                # Skicka progressuppdatering till klienten
                progress = int((i + 1) / len(names) * 100)
                socketio.emit('progress_update', {'progress': progress})

                # Kontrollera om alla API-anrop är klara
                if progress == 100:
                    socketio.emit('process_complete')

            # Skriv uppdaterad DataFrame till en ny Excel-fil
            output_file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], 'namn_inkl_urls.xlsx')
            df.to_excel(output_file_path, index=False)

            # Ta bort den uppladdade filen
            os.remove(file_path)

            # Returnera den uppdaterade Excel-filen till användaren
            return send_file(output_file_path, as_attachment=True)

    return render_template('index.html')

@app.route('/download_template')
def download_template():
    template_path = os.path.join(app.config['TEMPLATE_FILE'], 'names.xlsx')
    return send_file(template_path, as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['DOWNLOAD_FOLDER']):
        os.makedirs(app.config['DOWNLOAD_FOLDER'])
    app.run(debug=False)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['DOWNLOAD_FOLDER']):
        os.makedirs(app.config['DOWNLOAD_FOLDER'])
    socketio.run(app, debug=False)

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from flask import Flask, render_template, request, jsonify, url_for

# Läs Excel-filen och hämta namnen från kolumnen "Namn" (anpassa kolumnnamnet efter ditt Excel-dokument)
df = pd.read_excel('names.xlsx')
print(df.columns)  # Skriv ut kolumnnamnen för att verifiera rätt namn
names = df['Name']

# API-URL och parametrar
base_url = "https://api.tickster.com/sv/api/0.4/crm/5U1G551GMYY6JTL/campaigns/W547EAK9/communications"
api_key = "4f07078a24ee683d"
headers = {'Content-Type': 'application/json'}

# Användarnamn och lösenord för Basic Authentication
username = 'tickster.timra'
password = 'Tickster4466'

# Lägg till en ny kolumn för URL:en i DataFrame
df['URL'] = ""

# Loopa genom varje namn och gör API-anrop
for i, name in enumerate(names):
    payload = {
        "name": name,
        "communicationType": 1,
        "eventId": "PFMN1803MXL7T8D",
        "inventoryType": 3,
        "inventory": 2,
        "inventoryTags": "",
        "internalreference": f"{name}_reference"  # Anpassa efter ditt behov
    }

    api_url = f"{base_url}?key={api_key}"

    response = requests.post(
        api_url,
        json=payload,
        headers=headers,
        auth=HTTPBasicAuth(username, password)
    )

  # Hantera API-svaret om det behövs
    print(f"Anrop för {name} - Statuskod: {response.status_code}")

    # Om API-anropet var framgångsrikt (statuskod 200), lägg till URL:en i DataFrame
    if response.status_code == 200:
        url = response.json().get('url', '')
        df.at[i, 'URL'] = url

# Skriv uppdaterad DataFrame till Excel-filen
df.to_excel('namn_inkl_urls.xlsx', index=False)

print("Alla API-anrop och uppdatering av URL:er är slutförda.")


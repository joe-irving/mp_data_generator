import pandas as pd
import requests
from datetime import datetime

PARL_BASE_URL = "https://members-api.parliament.uk/api"

input_file = "/home/joe/Documents/Work/TippingPointUK/Data/mp_data_generator/output/2020-08-22-1400-search_from_airtable.csv"


def parse_contact(contacts):
    contacts_parsed = {}
    for contact_dict in contacts:
        if contact_dict['isWebAddress']:
            contact = contact_dict['line1']
        else:
            contact = contact_dict
        contacts_parsed[contact_dict['type']] = contact
    return contacts_parsed


mp_data = pd.read_csv(input_file)

mp_id_data = mp_data[['airtable_id', 'airtable_name', 'lookup.id']]

mp_contact_full_data = []

print(mp_id_data)

for mp_rec in mp_id_data.to_dict(orient="records"):
    print(mp_rec['airtable_name'])
    mp_url = f'{PARL_BASE_URL}/Members/{mp_rec["lookup.id"]}'
    mp_contact_url = f'{PARL_BASE_URL}/Members/{mp_rec["lookup.id"]}/Contact'
    mp = {
        'airtable_id': mp_rec['airtable_id'],
        'airtable_name': mp_rec['airtable_name'],
        'contact': {},
        'mp': {}
    }
    mp_lookup = requests.get(mp_url)
    contact_lookup = requests.get(mp_contact_url)
    if contact_lookup.status_code == 200:
        mp['contact'] = parse_contact(contact_lookup.json()['value'])
    if mp_lookup.status_code == 200:
        mp['mp'] = mp_lookup.json()['value']
    mp_contact_full_data.append(mp)

mp_contact_full_data_df = pd.json_normalize(mp_contact_full_data)

mp_contact_full_data_df.to_csv(f'output/{datetime.now()}-search_from_airtable.csv')

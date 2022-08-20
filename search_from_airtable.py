from pyairtable import Table
import os
import requests
from datetime import datetime
import pandas as pd

PARL_BASE_URL = "https://members-api.parliament.uk/api"


api_key = os.environ.get("AIRTABLE_API_KEY")

mps = Table(api_key, os.environ.get('BASE_ID'), os.environ.get('SC_MP_TABLE'))
lookup_mps = []

for mp_rec in mps.all(view='viwRvk0B1gfLBKBN6'):
    mp = {
        'airtable_id': mp_rec['id'],
        'airtable_name': mp_rec['fields']['Name']
    }
    print(f"Search: {mp['airtable_name']}")
    lookup_url = f'{PARL_BASE_URL}/Members/Search'
    lookup_params = {
        'Name': mp['airtable_name']
    }
    lookup = requests.get(lookup_url, params=lookup_params)
    if lookup.status_code != 200:
        lookup_mps.append(mp)
        continue
    lookup_result = lookup.json()['items']
    if len(lookup_result) > 0:
        lookup_mp = lookup_result[0]['value']
    else:
        lookup_mp = {}
    print(f"Result: {lookup_mp.get('nameDisplayAs')}")
    mp['lookup'] = lookup_mp
    lookup_mps.append(mp)

lookup_mps_df = pd.json_normalize(lookup_mps)
lookup_mps_df.to_csv(f'output/{datetime.now()}-search_from_airtable.csv')

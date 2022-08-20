import pandas as pd
import requests
from datetime import datetime

BASE_URL = "https://members-api.parliament.uk/api"
OUT_DIR = "/home/joe/Documents/Work/TippingPointUK/Data/mp_data_generator/output"


def get_parties():
    url = f"{BASE_URL}/Parties/StateOfTheParties/1/{datetime.now()}"
    party_data_req = requests.get(url)
    if party_data_req.status_code != 200:
        print(party_data_req.json())
        return
    parties = party_data_req.json()['items']
    return [p['value'] for p in parties]


if __name__ == '__main__':
    parties = pd.json_normalize(get_parties())
    parties.to_csv(f'{OUT_DIR}/{datetime.now()}-parties.csv')

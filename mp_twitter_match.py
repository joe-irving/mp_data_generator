import pandas as pd
import requests
from datetime import datetime

BASE_URL = "https://members-api.parliament.uk/api/"

BASE_DIR = "/home/joe/Documents/Work/TippingPointUK/Data/mp_data_generator"


def get_constit(search_text):
    params = {
        'searchText': search_text
    }
    url = f'{BASE_URL}Location/Constituency/Search'
    search = requests.get(url, params=params)
    if search.status_code != 200:
        return
    constits = search.json()['items']
    if len(constits) == 0:
        return
    return constits[0]['value']


def get_member_id(constit):
    constit_res = get_constit(constit)
    if constit_res:
        print(f"Got '{constit_res['name']}' when searching for '{constit}'")
        return constit_res['currentRepresentation']['member']['value']['id']
    else:
        print(f"Failed lookup for '{constit}'")


if __name__ == "__main__":
    url = 'https://www.politics-social.com/api/list/csv/followers'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    twitter_df = pd.read_csv(url, storage_options=headers)

    twitter_df['Members API ID'] = twitter_df['Constituency'].apply(get_member_id)

    twitter_df.to_csv(f"{BASE_DIR}/output/{datetime.now()}-twitter-handles")

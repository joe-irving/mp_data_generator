import requests
import math
# import csv
from datetime import datetime
import pandas as pd

PER_REQ = 20
NO_MPS = 650
NO_REQ = math.ceil(650/20)
BASE_URL = "https://members-api.parliament.uk/api"

constituencies = []
all_data = []

for i in range(NO_REQ):
    url = f"{BASE_URL}/Location/Constituency/Search"
    params = {"skip": i*PER_REQ, "take": PER_REQ}
    response = requests.get(url, params=params)
    for item in response.json()["items"]:
        c = item["value"]  # c as in constituency
        all_data.append(c)
        mp = c["currentRepresentation"]["member"]["value"]
        data = {
            "id": item["value"]["id"],
            "name": c["name"],
            # "mp_id": mp["id"],
            "mp_name": mp["nameListAs"],
            # "mp_gender": mp["gender"]
        }
        constituencies.append(data)

all_data_df = pd.json_normalize(all_data)
constituencies_df = pd.json_normalize(constituencies)

all_data_df.to_csv(f"output/{datetime.now()}.csv")
constituencies_df.to_csv(f"output/{datetime.now()}-basic.csv")

# keys = constituencies[0].keys()
# with open(f"{datetime.now()}output.csv", "w+") as output_file:
#     dict_writer = csv.DictWriter(output_file, keys)
#     dict_writer.writeheader()
#     dict_writer.writerows(constituencies)

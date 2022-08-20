###############################################################################
# Generate a custom target list of UK MPs, intended for uploading to Action
# Network. Input data is in the format:
#
# geoid            |   members-api_constituency_id
# ----------------------------------------
# 022719_pa ...    |  3506
# ...
#
# and outputs a csv of all the MPs contact info.

import requests
import csv
import yaml
import re
# from dotenv import load_dotenv
import os
import json

# load_dotenv()

AIRTABLE_API_KEY=os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_URL = f"https://api.airtable.com/v0/{os.environ.get('MP_BASE_ID')}/{os.environ.get('MP_TABLE_ID')}"

INPUT_FILE = "input_data.csv"
OUTPUT_FILE = "MP_contact.csv"

PHONE_REGEX = "^(((\+44\s?\d{4}|\(?0\d{4}\)?)\s?\d{3}\s?\d{3})|((\+44\s?\d{3}|\(?0\d{3}\)?)\s?\d{3}\s?\d{4})|((\+44\s?\d{2}|\(?0\d{2}\)?)\s?\d{4}\s?\d{4}))(\s?\#(\d{4}|\d{3}))?$"
TWITTER_USERNAME_REGEX = "^https?://(www\.)?twitter\.com/(#!/)?([^/]+)(/\w+)*$"

TITLES = [
    "Mr",
    "Ms",
    "Mx",
    "Sir",
    "Dame",
    "Mrs",
    "Dr",
    "Miss"
]

out_data = []

keys = []

extract_contact_fields = ["email", "phone", "postcode", "address"]

subs = {
    "postcode": "zip_code"
}

priority_contact_type = ["Party", "Constituency", "Parliamentary"]
priority_contact_type.reverse()


def get_airtable_records(page_size=100, offset=None):
    url = AIRTABLE_URL
    params = {
        "view": "viwPJ4HQMlGs2fk9h",
        "pageSize": page_size,
        "fields": ["geoid","constituency_id"]
    }
    if offset:
        params["offset"] = offset
    headers = {"Authorization": "Bearer {}".format(AIRTABLE_API_KEY)}
    response = requests.get(url, headers=headers, params=params)
    return response.json()


def get_address(contact):
    address = ""
    for i in range(1,5):
        address_line = contact["line{}".format(i)]
        if address_line:
            address += contact["line{}".format(i)] + ", "
    if contact["postcode"]:
        address += contact["postcode"]
    if len(address) > 0:
        return address
    else:
        return None


in_data = get_airtable_records()
first = True

while "offset" in in_data.keys() or first:
    first = False
    if "offset" in in_data.keys():
        offset=in_data["offset"]
    else:
        offset=None
    # Loop through ids and add MP contact data
    for record in in_data["records"]:
        airtable_record_id = record["id"]

        constituency = record["fields"]
        # Get constituency data
        c = requests.get("https://members-api.parliament.uk/api/Location/Constituency/{}".format(constituency["constituency_id"])).json()
        try:
            mp_id = c["value"]["currentRepresentation"]["member"]["value"]["id"]
        except TypeError as err:
            print(err)
            print(c)
        mp = requests.get("https://members-api.parliament.uk/api/Members/{}/".format(mp_id)).json()["value"]
        mp_contact = requests.get("https://members-api.parliament.uk/api/Members/{}/contact".format(mp_id)).json()["value"]
        if mp["nameAddressAs"]:
            first_name = mp["nameAddressAs"]
        else:
            first_name = mp["nameDisplayAs"]
            # Generate title
            first_word_name = first_name.split(" ")[0]
            if first_word_name not in TITLES:
                if mp["gender"] == "F":
                    title = "Ms"
                elif mp["gender"] == "M":
                    title = "Mr"
                else:
                    title = "Mx"

        out_data_line = {
            "first_name": first_name,
            "mp_id": mp_id,
            "list_name": mp["nameListAs"],
            "display_name": mp["nameDisplayAs"],
            "full_title_name":  mp["nameFullTitle"],
            "gender": mp["gender"],
            "party": mp["latestParty"]["name"],
            "geoid": constituency["geoid"],
            "constituency_id": constituency["constituency_id"],
            "constituency": c["value"]["name"],
            "country": "UK",
            "photo": [{"url":mp["thumbnailUrl"]}]
        }
        if title:
            out_data_line["title"]=title
        for key in out_data_line.keys():
            if key not in keys:
                keys.append(key)
        # Extract contact info
        contact_dict = {}
        for contact in mp_contact:
            if contact["isWebAddress"]:
                out_data_line[contact["type"]] = contact["line1"]
            else:
                # Compress the address to one feild
                contact["address"] = get_address(contact)
                for contact_field in extract_contact_fields:
                    if contact_field not in contact_dict.keys():
                        contact_dict[contact_field] = {}
                    out_data_line["{}_{}".format(contact_field,contact["type"])] = contact[contact_field]
                    contact_dict[contact_field][contact["type"]] = contact[contact_field]

        # Set a default value for "email", "phone" etc
        for type in priority_contact_type:
            for field in extract_contact_fields:
                if field in contact_dict.keys():
                    if type in contact_dict[field].keys():
                        out_data_line[field] = contact_dict[field][type]
        # Sub any values
        for key in subs:
            if key in out_data_line.keys():
                out_data_line[subs[key]] = out_data_line[key]

        # Create GEOID
        geoid_created = "022719_parliamentary_constituences_{}".format(out_data_line["constituency"].strip().lower().replace(" ","_")).replace("_st_","_st._")

        out_data_line["geoid_created"] = geoid_created
        out_data_line["geoid_is_same"] = geoid_created == constituency["geoid"] # for double checking mainly


        # Parse phone number
        if out_data_line["phone"]:
            # Some of the phone numbers are badly entered
            phone_numbers = re.findall(PHONE_REGEX,out_data_line["phone"])
            if len(phone_numbers) > 0:
                phone = phone_numbers[0][0]
                if phone.startswith("0"):
                    phone = phone.replace("0","+44",1).replace(" ","")
                out_data_line["phone"] = phone
        # Parse twitter username
        if "Twitter" in out_data_line.keys():
            usernames =  re.findall(TWITTER_USERNAME_REGEX, out_data_line["Twitter"])[0]
            for item in usernames:
                if len(item) > 1:
                    out_data_line["twitter_username"] = item

        # Any extra header values for CSV?
        for key in out_data_line.keys():
            # If so add them to the list of keys
            if key not in keys:
                keys.append(key)
        out_data.append(out_data_line)

        # Add updates to Airtable
        url=f"{AIRTABLE_URL}/{airtable_record_id}"
        headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json"
        }
        airtable_update_data = {"fields": out_data_line}
        print(json.dumps(airtable_update_data))
        response = requests.patch(url,json=airtable_update_data,headers=headers)
        print(yaml.dump(response.json()))
    in_data = get_airtable_records(offset=offset)

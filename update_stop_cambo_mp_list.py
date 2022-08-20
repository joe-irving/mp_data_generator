from pyairtable import Table
import pandas as pd
import os
import re

ROOT_DIR = "/home/joe/Documents/Work/TippingPointUK/Data/mp_data_generator/"

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

MP_GENDER = {
    "M": "Mr",
    "F": "Ms"
}

# in the format attr: airtable_field
FIELD_MATCHING = {
    'email': 'Email',
    'twitter': 'Twitter',
    'title': 'Title',
    'airtable_photo': 'Profile',
    'gender': 'Gender',
    'party': 'Party',
    'constituency': 'Constituency',
    'parl_id': 'Parliamentary ID'
}


class MPData():
    def __init__(self, row):
        self.raw = row
        self.email = self.get_email()
        self.twitter = self.get_twitter_handle()
        self.title = self.get_title()
        self.airtable_id = self.raw['airtable_id']
        self.photo = self.raw['mp.thumbnailUrl']
        self.airtable_photo = [{'url': self.photo}]
        self.gender = self.raw['mp.gender']
        self.constituency = self.raw['mp.latestHouseMembership.membershipFrom']
        self.party = self.raw['mp.latestParty.name']
        self.parl_id = self.raw['mp.id']

    def get_email(self):
        e_con = '^contact.\w{0,50}.email$'
        e_keys = [k for k in self.raw.keys() if re.search(e_con, k)]
        emails = [self.raw[c] for c in e_keys if isinstance(self.raw[c], str)]
        if len(emails) > 0:
            return emails[0]

    def get_twitter_handle(self):
        twitter_url = self.raw['contact.Twitter']
        if isinstance(self.raw['contact.Twitter'], str):
            return twitter_url.replace('https://twitter.com/', '@')

    def get_title(self):
        name_title = self.raw['mp.nameDisplayAs'].split(' ')[0]
        if name_title in TITLES:
            return name_title
        if self.raw['mp.gender'] in MP_GENDER.keys():
            return MP_GENDER[self.raw['mp.gender']]
        else:
            return "Mx"


def update_airtable(key, base, table, fields, mps):
    airtable = Table(key, base, table)
    mps_airtable = []
    for mp in mps:
        mp_airtable = {fields[f]: getattr(mp, f) for f in fields.keys() if getattr(mp, f)}
        mps_airtable.append({'id': mp.airtable_id, 'fields': mp_airtable})
    airtable.batch_update(mps_airtable, typecast=True)


if __name__ == "__main__":

    mp_data = pd.read_csv(f'{ROOT_DIR}output/2022-08-15 14:07:46.071523-search_from_airtable.csv')

    api_key = os.environ.get('AIRTABLE_API_KEY')
    airtable = Table(api_key, os.environ.get('BASE_ID'), os.environ.get('SC_MP_TABLE'))

    mps = []

    for mp_row in mp_data.to_dict(orient='records'):
        mps.append(MPData(mp_row))

    update_airtable(api_key, os.environ.get('BASE_ID'), os.environ.get('SC_MP_TABLE'),
                    FIELD_MATCHING,
                    mps)

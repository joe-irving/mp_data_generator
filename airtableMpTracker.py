import requests
import os
# from dotenv import load_dotenv
import yaml
import math

# load_dotenv()

class airtableMpTracker:
    """ A tool to update pariamentry question relating to a search term """

    def __init__(self, airtable_app_id=""):
        self.airtable_app_id = airtable_app_id
        self.airtable_base_url = f'https://api.airtable.com/v0/{self.airtable_app_id}'
        AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
        self.headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json"
        }

    def get_mp(self,id):
        return requests.get(f'https://members-api.parliament.uk/api/Members/{id}/').json()["value"]

    def get_all_airtable_records(self,table,id_field=None):
        print("Getting records in airtable")
        airtable_url = f'{self.airtable_base_url}/{table}'
        offset = True
        airtable_records = {}
        while offset:
            records = requests.get(airtable_url,headers=self.headers).json()
            if "offset" not in records.keys():
                offset = False
            for q in records["records"]:
                id = q["fields"][id_field] if id_field else q["id"]
                airtable_records[id] = q
        print(f"received {len(airtable_records)} records from airtable")
        return airtable_records

    def get_all_parliament_questions(self, search_term):
        print(f"Searching all parliamentary questions relating to '{search_term}'")
        TAKE = 20
        parliament_url = f'https://writtenquestions-api.parliament.uk/api/writtenquestions/questions'
        params = {
            "searchTerm": search_term,
            "take": 1,
            "skip": 0
        }
        no_questions = requests.get(parliament_url,params=params).json()["totalResults"]
        print("Questions:",no_questions)
        no_requests = math.ceil(no_questions/TAKE)
        params["take"]=TAKE
        results=[]
        for i in range(no_requests):
            response = requests.get(parliament_url,params=params).json()
            results.extend(response["results"])
            no_questions = response["totalResults"]
            params["skip"] = (i+1)*params["take"]
        return results

    def update_questions(self, search_term="",question_table="Questions"):
        airtable_url = f'{self.airtable_base_url}/{question_table}'
        # Get parliament questions
        current_questions = self.get_all_parliament_questions(search_term)
        current_question_ids = []
        # Get airtable questions
        airtable_questions = self.get_all_airtable_records(question_table,id_field="id")
        # Loop through current questions updating or adding new
        for question in current_questions:
            q = question["value"]
            current_question_ids.append(q["id"])
            # If exists, update
            if q["id"] in airtable_questions.keys():
                print(f"Updating question {q['id']}")
                mp_name = self.get_mp(q["askingMemberId"])["nameDisplayAs"]
                q["MP Name"] = mp_name
                airtable_q_data = {
                    "records":  [
                        {
                            "id":airtable_questions[q["id"]]["id"],
                            "fields": q
                        }
                    ],
                    "typecast": True
                }
                message = requests.patch(airtable_url,json=airtable_q_data,headers=self.headers).json()
                if "error" in message.keys():
                    raise Exception(message)
            # Else create record
            else:
                print(f"Creating question {q['id']}")
                member_name = self.get_mp(q["askingMemberId"])["nameDisplayAs"]
                q["MP Name"] = member_name
                airtable_q_data = {
                    "records":  [{"fields": q}],
                    "typecast": True
                }
                print(q["questionText"])
                message = requests.post(airtable_url,json=airtable_q_data,headers=self.headers).json()
                if "error" in message.keys():
                    raise Exception(message)
                else:
                    airtable_questions[q["id"]] = message["records"][0]
        # Delete questions on airtable not in parliament api lookup
        delete_records = airtable_questions.keys() - current_question_ids
        for q_id in delete_records:
            print(f"Creating question {q_id}")
            airtable_record_id = airtable_questions[q_id]["id"]
            airtable_record_url = f'{airtable_url}/{airtable_record_id}'
            message = requests.delete(airtable_record_url,headers=self.headers).json()
            if "error" in message.keys():
                raise Exception(message)


if __name__ == "__main__":
    updater = airtableMpTracker(airtable_app_id=os.environ.get('BASE_ID'))
    updater.update_questions(search_term="cambo", question_table=os.environ.get('QUESTION_TABLE_ID'))

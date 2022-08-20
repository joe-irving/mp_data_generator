import requests
import math
import json
import geojson
import yaml
import folium

m = folium.Map(location=[51.581703,-3.809383])


PER_REQ = 20
NO_MPS = 650
NO_REQ = math.ceil(NO_MPS/PER_REQ)
# NO_REQ = 1

for i in range(NO_REQ):

    c_search = requests.get("https://members-api.parliament.uk/api/Location/Constituency/Search?skip={}&take={}".format(i*PER_REQ,PER_REQ))
    count=0
    for item in c_search.json()["items"]:
        count+=1
        print(i+count, end="\r")
        c = item["value"] # c as in constituency
        mp = c["currentRepresentation"]["member"]["value"]
        # Get geojson
        c_geometry = requests.get("https://members-api.parliament.uk/api/Location/Constituency/{}/Geometry".format(c["id"]))
        if mp["latestParty"]["backgroundColour"]:
            bg_colour = "#"+mp["latestParty"]["backgroundColour"]
        else:
            bg_colour = "#ffffff"
        c_geojson_item = {
            "type": "Feature",
            "properties": {
                "name": c["name"],
                "fill": bg_colour,
                "stroke": bg_colour,
                "stroke-width": 0
            },
            "geometry": json.loads(c_geometry.json()["value"])
        }

        tile = folium.GeoJson(
            data=json.dumps(c_geojson_item),
            style_function=lambda x: {
                'fillColor': x["properties"]["fill"],
                "color": x["properties"]["stroke"],
                "fillOpacity": "0.4",
                "opacity":"0.8",
            }).add_to(m)
        folium.Popup(c["name"]).add_to(tile)

m.save("index.html")

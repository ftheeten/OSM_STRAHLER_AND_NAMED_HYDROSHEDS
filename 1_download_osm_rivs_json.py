import requests
import time
import sys
import urllib.parse
from requests.exceptions import HTTPError
import osm2geojson
import json
import os

out="D:\\DEV\\GIS_OSM\\out_africafull"
url_overpass="https://overpass-api.de/api/interpreter"
MIN_X=-26
MAX_X=55
MIN_Y=-35
MAX_Y=38
 
def add_name_to_prop(p_src_json, p_field="tags", to_explode=["name", "waterway"]):
    returned={}
    returned["type"]="FeatureCollection"
    returned["features"]=[]
    for elem in p_src_json["features"]:
        elem2=elem.copy()
        added={}
        for f in to_explode:
            added[f]=None
        if p_field in elem2["properties"]:
            for f in to_explode:
                if f in elem2["properties"][p_field]:
                    added[f]=elem2["properties"][p_field][f]
        elem2["properties"] = {**elem2["properties"], **added}
        returned["features"].append(elem2)
    return returned

def count_data(p_min_x, p_max_x, p_min_y, p_max_y, p_step_x, p_step_y, p_out, attr_1="waterway", p_field="name"):
    i=0
    cpt_boxes={}
    for x in range(p_min_x, p_max_x, p_step_x):
        for y in range(p_min_y, p_max_y, p_step_y):
            max_y=min(p_max_y, y+p_step_y)
            max_x=min(p_max_x, x+p_step_x)
            bbox=(y, x, max_y, max_x)
            print(bbox)
            cpt_boxes[bbox]=True
    print(len(cpt_boxes))
    
def get_data(p_min_x, p_max_x, p_min_y, p_max_y, p_step_x, p_step_y, p_out, attr_1="waterway", p_field="name"):
    headers = {
                "Referer": "https://africamuseum.be",
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:149.0) Gecko/20100101 Firefox/149.0"
    
    }
    i_download=0
    ix=0            
    for x in range(p_min_x, p_max_x, p_step_x):
        iy=0
        for y in range(p_min_y, p_max_y, p_step_y):
            try:
                if i_download>=0:
                    max_y=min(p_max_y, y+p_step_y)
                    max_x=min(p_max_x, x+p_step_x)
                    bbox=(y, x, max_y, max_x)
                    print(bbox)
                    query='[out:json];way["waterway"](if:is_closed()==0)({y},{x},{max_y},{max_x});out geom;'.format(y=y, x=x, max_y=max_y, max_x=max_x)
                    print(query)
                    res = requests.post(url_overpass, headers=headers, data= query)
                    if res is not None:
                        print(res)
                        print(res.text)
                        if res.text is not None:
                            if len(str(res.text).strip())>0:
                                iy=iy+1
                                out_file='out_{ix}_{iy}.geojson'.format(ix=ix, iy=iy)
                                save_to=os.path.join(p_out, out_file)
                                try:
                                    tmp=json.loads(res.text)
                                    geojson = osm2geojson.json2geojson(tmp)
                                    geojson=add_name_to_prop(geojson)
                                    print(geojson)                          
                                    print(save_to)
                                    print(geojson)
                                    with open(save_to, 'w', encoding='utf-8') as f:
                                        print("save")
                                        json.dump(geojson, f, ensure_ascii=False, indent=4)
                                except ValueError as e:
                                    print("ERROR_JSON_FORMAT")
                            time.sleep(20)
            except HTTPError as e:
                print(e.response.text)
            finally:
                i_download=i_download+1
        ix=ix+1 
        
#count_data(MIN_X, MAX_X, MIN_Y, MAX_Y, 3, 3, out)        
get_data(MIN_X, MAX_X, MIN_Y, MAX_Y, 2, 2, out)

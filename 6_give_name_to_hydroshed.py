import pandas as pnd
import geopandas
import shapely
from shapely import unary_union
import sys
import copy
import os
from collections import OrderedDict
from operator import itemgetter
import tkinter as tk
from tkinter import filedialog
from unidecode import unidecode


root = tk.Tk()
root.withdraw()

files = [ ('Geopackages Files', '*.gpkg'), ('shapefiles Files', '*.shp')]
FILE_BASINS=filedialog.askopenfilename(title="input file basins", filetypes = files, defaultextension = files)
FILE_NAMED_RIVERS=filedialog.askopenfilename(title="input file rivers with Strahler", filetypes = files, defaultextension = files)
OUT_FILE_TMP=filedialog.asksaveasfile(title="output file named basins", filetypes = files, defaultextension = files)
OUT_FILE=os.path.realpath(OUT_FILE_TMP.name)
DICT_IDX_RIVS={}
THRESHOLD_AUX_RIVER=0.7

if os.path.isfile(OUT_FILE):
    OUT_FILE_TMP.close()
    os.remove(OUT_FILE)
    

def find_touching(p_line_geom, g_sheds):
    touching = g_sheds[g_sheds.geometry.intersects(p_line_geom)]
    return touching


def associate_basin_to_name(f_sheds, f_rivs, p_out):
    global DICT_IDX_RIVS, THRESHOLD_AUX_RIVER
    result_tmp={}
    g_rivs = geopandas.read_file(f_rivs)
    g_rivs = g_rivs[g_rivs["name"].str.len() > 0]
    g_sheds = geopandas.read_file(f_sheds)
    
    g_sheds["main_river"]=""
    g_sheds["main_river_len"]=0.0
    g_sheds["other_rivers"]=""
    #g_sheds["other_rivers_list"]=None
    g_sheds=g_sheds.set_crs('epsg:4326')
    g_sheds=g_sheds.to_crs('epsg:3857')
    g_rivs.set_crs('epsg:3857') 
    g_rivs.to_crs('epsg:3857') 
    g_rivs["geometry"] = g_rivs["geometry"].normalize()
    g_rivs["wkb"] = g_rivs.geometry.apply(lambda g: g.wkb)
    g_rivs = g_rivs.drop_duplicates(subset="wkb").drop(columns="wkb")
    #clipped_lines_gdf = geopandas.clip(g_sheds, g_rivs)
    #clipped_lines_gdf = clipped_lines_gdf[~clipped_lines_gdf.is_empty]
    
    for i, row in g_rivs.iterrows():
        
        #print(row)
        touching=find_touching(row["geometry"],g_sheds)
        name_riv=row["name"].upper().strip()
        name_riv=unidecode(name_riv)
        riv_geometry=row["geometry"]
        if len(touching)>0:
            #print(len(touching))
            #print("----")
            for i2, row2 in touching.iterrows():
                #print(i)
                if not i2 in result_tmp:
                    result_tmp[i2]={}                    
                tmp_geom=g_sheds.loc[i2]["geometry"]
                intersection_line = riv_geometry.intersection(tmp_geom)
                #print(intersection_line)
                len_line=intersection_line.length
                #print(len_line)
                if not name_riv in result_tmp[i2]:
                    result_tmp[i2][name_riv]=len_line
                else:
                    result_tmp[i2][name_riv]=result_tmp[i2][name_riv]+len_line
    for idx_shed, names_rivs in result_tmp.items():
        by_len= OrderedDict(sorted(names_rivs.items(), key=itemgetter(1), reverse=True))
        if len(by_len)>0:
            vals= [key for key in by_len.keys()] #list(by_len.keys())
            main_name=vals[0]
            main_len=by_len[vals[0]]
            g_sheds.at[idx_shed, "main_river_len"] = main_len
            if len(by_len)>1:
                alt_name=vals[1]
                alt_len=by_len[vals[1]]
                if alt_len/main_len >THRESHOLD_AUX_RIVER:
                    main_name=main_name+" ("+alt_name+")"
                merged_tmp=vals[1:]
                merged=';'.join(merged_tmp)
                g_sheds.at[idx_shed, "other_rivers"] = merged
                #g_sheds.at[idx_shed, "other_rivers_list"]=vals
            g_sheds.at[idx_shed, "main_river"] = main_name
        DICT_IDX_RIVS[idx_shed]=by_len
    g_sheds2= g_sheds.copy()
    """
    for i, row in g_sheds.iterrows():
        riv_copy= g_rivs.copy()
        tmp={}
        neighbors = g_sheds2[((g_sheds2.index != i) & (g_sheds2.geometry.touches(row.geometry)))].index.tolist()
        neighbors.append(i)
        tmp={}
        for i2 in neighbors:
            if i2 in DICT_IDX_RIVS:
                tmp2=DICT_IDX_RIVS[i2]
                for riv, len_riv in tmp2.items():
                    riv2=unidecode(riv)
                    if not riv2 in tmp:
                        tmp[riv2]=tmp2[riv]
                    else:
                        tmp[riv2]=tmp[riv2]+len_riv
        by_len2= OrderedDict(sorted(tmp.items(), key=itemgetter(1), reverse=True))
        ref_len=0
        if len(by_len2)>0:
            vals= [key for key in by_len2.keys()] #list(by_len.keys())
            alt_name = vals[0]
            ref_len=by_len2[alt_name]
            if i in DICT_IDX_RIVS:
                ref_rivs=DICT_IDX_RIVS[i].keys()
            else:
                ref_rivs=[]
            if alt_name!=row["main_river"]  and alt_name in ref_rivs and ref_len> row["main_river_len"]:
                g_sheds.at[i, "main_river"]=alt_name+ "/"+row["main_river"]
    """   
       
    g_sheds.to_file(p_out, layer='rivers', driver="GPKG", mode="w")
    
associate_basin_to_name(FILE_BASINS, FILE_NAMED_RIVERS, OUT_FILE)
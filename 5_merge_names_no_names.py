import pandas as pnd
import geopandas
import shapely
from shapely.geometry import Point, LineString
from shapely.ops import linemerge, unary_union
from collections.abc import Iterable
import sys
import copy
import os


FILE_NO_NAMES="no_names_3.gpkg"
FILE_NAMES="names3.gpkg"
OUT_FILE="added_names.gpkg"
TRIB_LIST={}

def find_touching(p_line_no_name, g_name):
    tmp_geometry=p_line_no_name["geometry"]
    touching = g_name[g_name.geometry.intersects(tmp_geometry)]
    if touching.empty:
        return None, None
    else:
        longest = touching.loc[touching.geometry.length.idxmax()]
        return longest["ref_name"], longest["strahler_tmp"]
    
def find_complement_name(start, opposite, g_name, idx_name,  complements, complements_len,strahler_list, idx_trib_list ): 
    if start in idx_name:
        for ends, idx_lines in idx_name[start].items():
            for idx_line in idx_lines:
                for idx_line in idx_lines:
                    line=g_name.loc[idx_line]
                    tmp_idx=line["id_str"]
                    tmp_len=line["geometry"].length
                    tmp_name=line["ref_name"]
                    strahler=line["strahler_tmp"]
                    idx_tributary=line["idx_tributary"]
                    complements[tmp_idx]=tmp_name
                    complements_len[tmp_idx]=tmp_len
                    strahler_list[tmp_idx]=strahler
                    idx_trib_list[tmp_idx]=idx_tributary
                    
def get_tributary_list(p_name): 
    global TRIB_LIST
    if not p_name in TRIB_LIST:
        TRIB_LIST[p_name]=1
        return 1
    else:
        returned=TRIB_LIST[p_name]
        TRIB_LIST[p_name]=returned+1
        return returned
  
def associate_to_name( g_name, g_no_name):
    global TRIB_LIST
    to_remove=[]
    to_add=[]
    idx_name=build_index(g_name)
    idx_no_name=build_index(g_no_name)
    #associate_to_name(idx_name, g_name, idx_no_name, g_no_name)
    for start, item in idx_no_name.items():
        for opposite, ori_lines in item.items():
            for index_line in ori_lines:
                ori_line=g_no_name.loc[index_line]                
                #print("RF")
                new_line=ori_line.copy()
                complements={}
                complements_len={}
                strahler_list={}
                idx_trib_list={}
                find_complement_name(start, opposite, g_name, idx_name, complements, complements_len, strahler_list,idx_trib_list )
                find_complement_name(opposite, start, g_name, idx_name, complements, complements_len, strahler_list,idx_trib_list )
                if len(complements)>0:
                    type_aff="continued"
                    #print(complements)
                    #print(complements_len)
                    key_max_len=max(complements_len, key=complements_len.get)                
                    max_len=complements_len[key_max_len]
                    ref_name_to_give=complements[key_max_len].strip()
                    name_to_give=ref_name_to_give
                    strahler_to_give=(strahler_list[key_max_len])
                    idx_tributary=idx_trib_list[key_max_len]
                    cpt_name=0                 
                    if len(complements)>1:
                        for tmp_name in complements:
                            if tmp_name.strip()==name_to_give:
                                cpt_name=cpt_name+1
                                if cpt_name>1:
                                    type_aff="tributary"
                                    idx_get_tributary_list=get_tributary_list(ref_name_to_give)
                                    strahler_to_give=strahler_to_give+1
                                    idx_tributary=idx_get_tributary_list
                                    name_to_give =  name_to_give #+ " (tributary "+str(idx_get_tributary_list)+" local Strahler :"+str(strahler_to_give)+")"  
                                    
                                    break
                    if type_aff=="continued":
                        ref_name_to_give=name_to_give
                    #print(name_to_give)
                    new_line["ref_name"]=ref_name_to_give
                    new_line["name"]=name_to_give
                    new_line["name_completed"]=True
                    new_line["name_infered_type"]=type_aff
                    new_line["strahler_tmp"]=strahler_to_give
                    new_line["idx_tributary"]=idx_tributary
                    to_add.append(new_line)
                    to_remove.append(ori_line["id_str"])
                else:
                    ref_name_to_give, strahler_to_give=find_touching(ori_line, g_name)
                    #strahler_to_give=(strahler_list[key_max_len])
                    name_to_give=ref_name_to_give
                    if not name_to_give is None:
                        new_line=ori_line.copy()
                        new_line["ref_name"]=ref_name_to_give                        
                        new_line["name_completed"]=True
                        new_line["name_infered_type"]="tributary"
                        idx_get_tributary_list=get_tributary_list(ref_name_to_give)
                        idx_tributary=idx_get_tributary_list
                        name_to_give =  name_to_give #+ " (tributary "+str(idx_get_tributary_list)+" local Strahler :"+str(strahler_to_give)+")" 
                        
                        strahler_to_give=strahler_to_give+1
                        new_line["strahler_tmp"]=strahler_to_give
                        new_line["name"]=name_to_give
                        new_line["idx_tributary"]=idx_tributary
                        to_add.append(new_line)
                        to_remove.append(ori_line["id_str"])
                    
    to_remove=list(set(to_remove))
    len_to_add=len(to_add) 
    len_to_remove=len(to_remove)
    print(f"{len_to_add=}")
    print(f"{len_to_remove=}") 
    lenframe=len(g_no_name)
    print(f"{lenframe=}")
    g_no_name = g_no_name[~g_no_name["id_str"].isin(to_remove)]
    lenframe=len(g_no_name)
    print(f"{lenframe=}")
    if len_to_add>0:    
        new_ds=geopandas.GeoDataFrame(to_add, crs="EPSG:3857")         
        gpnd2 = pnd.concat([g_name, new_ds] , ignore_index=True) 
        return associate_to_name( gpnd2, g_no_name)
    else:
        g_name = pnd.concat([g_name, g_no_name] , ignore_index=True) 
        return g_name
        
def build_index(g_name):
    returned={}
    for i, row in g_name.iterrows():
        start=row["start"]
        end=row["end"]
        if not start in returned:
            returned[start]={}
            if not end in returned[start]:
                returned[start][end]=[]
            returned[start][end].append(i)
        if not end in returned:
            returned[end]={}
            if not start in returned[end]:
                returned[end][start]=[]
            returned[end][start].append(i)
    return returned 
    
def name_trib_strahler(g_name):
    mask=g_name['idx_tributary'] >1 
    g_name.loc[mask, "name"] = (
        g_name.loc[mask, "name"]
        + " (tributary:"
        + g_name.loc[mask, "idx_tributary"].astype(str)
         + " local Strahler -:"
        + g_name.loc[mask, "strahler_tmp"].astype(str)
        +")"
       )
    return g_name
    
    
def load_files(p_name, p_no_name, p_out_file):
    g_name = geopandas.read_file(p_name)
    g_no_name = geopandas.read_file(p_no_name) 
    g_name=g_name.to_crs(3857)
    g_no_name=g_no_name.to_crs(3857)
    g_name["start"]=g_name.geometry.apply(lambda geom: geom.coords[0])
    g_name["end"]=g_name.geometry.apply(lambda geom: geom.coords[-1])
    g_name["length"]=g_name.geometry.length
    g_name["id_str"]=g_name["id"].astype(str)
    g_name["name_completed"]=False
    g_name["name_infered_type"]=None
    g_name["strahler_tmp"]=0
    g_name["idx_tributary"]=0
    g_name["ref_name"]=g_name["name"]
    g_no_name["start"]=g_no_name.geometry.apply(lambda geom: geom.coords[0])
    g_no_name["end"]=g_no_name.geometry.apply(lambda geom: geom.coords[-1])
    g_no_name["length"]=g_name.geometry.length
    g_no_name["strahler_tmp"]=0
    frame_name=associate_to_name( g_name, g_no_name)
    frame_name=frame_name.drop(["start", "end"], axis=1)
    frame_name=name_trib_strahler(frame_name)
    #print(list(gdf.select_dtypes('geometry').columns))
    if os.path.exists(p_out_file):
        try:
            os.remove(p_out_file)
        except OSError:
            print("can't delete file")
    frame_name.to_file(p_out_file, layer='rivers', driver="GPKG", mode="w")
      
    
load_files(FILE_NAMES, FILE_NO_NAMES, OUT_FILE)
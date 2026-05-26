import pandas as pnd
import geopandas
import shapely
from shapely.geometry import Point, LineString
from shapely.ops import linemerge, unary_union
from collections.abc import Iterable
import sys
import copy
import tkinter as tk
from tkinter import filedialog
import tkFileDialog

root = tk.Tk()
root.withdraw()


files = [ ('Geopackages Files', '*.gpkg')]
FILE= filedialog.askopenfilename(title="input file rivers", filetypes = files, defaultextension = files)

FILE_NO_NAME=filedialog.asksaveasfile(title="output file unnamed rivers", filetypes = files, defaultextension = files)
FILE_NAME=filedialog.asksaveasfile(title="output file named rivers", filetypes = files, defaultextension = files)
GPD_NAME=None
GPD_NO_NAME=None
DICT_NAME_1={}
DICT_NO_NAME_1={}
TO_REMOVE=[]

   



   


   
           
def geopandas_without_duplicate(p_list):
    gpnd=geopandas.GeoDataFrame(p_list)    
    #gpnd["geometry"] = gpnd["list_points"].apply(LineString)
    gpnd = gpnd.set_geometry(gpnd["geometry"],crs="EPSG:4326")
    #gpnd = gpnd.set_geometry(gpnd.geometry.normalize())
    #gpnd["geometry"] = gpnd.geometry    
    print(gpnd)
    print(len(gpnd))
    gpnd = gpnd.drop_duplicates(subset="geometry", keep="first")
    print(len(gpnd))
    return gpnd
   
 

 

def test_ring(p_geom):    
    tmp=p_geom.coords
    if len(tmp)>2:
        if tmp[0]==tmp[-1]:
            #print("ring")
            tmp=tmp[:-1]
            return LineString(tmp)
            #sys.exit()
    return p_geom  
 
def merge_touching_line_string(l1, l2):
    l1=test_ring(l1)
    l2=test_ring(l2)
    result=linemerge([l1, l2])
    result=result.normalize()
    gtype=result.geom_type.lower()
    if gtype=="multilinestring":
        print("multi")
        print(l1)
        print(l2)
        print(result)
        sys.exit()
    return result


   
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
 
def find_complement(p_index, gpnd, start, opposite, complements, complements_len, old_geom, current_id_str, to_remove ): 
    ref_len=old_geom.length
    delete_this=False
    if start in p_index:
        #print(p_index[start])
        #print(p_index[start].keys())
        #print(p_index[start].values())
        #sys.exit()
        for ends, idx_lines in p_index[start].items():
            #print("----")
            #print(f"{start=}")
            #print(f"{ends=}")
            #print(idx_lines)
            #sys.exit()
            for idx_line in idx_lines:
                #print(idx_line)                
                line=gpnd.loc[idx_line]
                #print(line)
                #print(f"{current_id_str=}")
                #print(f'{line["id_str"]=}')
                #print(f'{opposite=}')
                if current_id_str!=line["id_str"] and not line["id_str"] in to_remove:
                    #print("go") 
                    line2=line.copy()                    
                    if not(old_geom.covered_by(line2["geometry"])) and  not(line2["geometry"].covered_by(old_geom)): #line["iteration"]<current_iteration:
                        #print("complement_found")
                        #print(ends)
                        #print(line)
                        #line["to_remove"]=True
                        line2['length']=line2["geometry"].length
                        #returned[line["geometry"].wkb]=line
                        complements[line2["id_str"]]=line
                        complements_len[line2["id_str"]]=line2['length']
                   
 
def complete_touching_paths(gpnd, processed=0, iteration=0):   
    to_remove=[]
    to_build=[]
    init=processed
    cpt_add=0
    cpt_delete=0
    to_add=[]
    p_dict_1=build_index(gpnd)
    for start, item in p_dict_1.items():
        for opposite, ori_lines in item.items():
            for index_line in ori_lines:
                #print(f"{index_line=}")
                ori_line=gpnd.loc[index_line]
                
                #print("RF")
                line=ori_line.copy()
                complements={}
                complements_len={}
                old_geom=line["geometry"]
                len_old=old_geom.length
                find_complement(p_dict_1, gpnd, start, opposite, complements, complements_len, old_geom, ori_line["id_str"] , to_remove)  
                find_complement(p_dict_1, gpnd, opposite, start, complements, complements_len, old_geom, ori_line["id_str"], to_remove )                
                if len(complements)>0:
                    #print(complements)
                    key_max_len=max(complements_len, key=complements_len.get)                
                    max_len=complements_len[key_max_len]
                    line_to_merge=complements[key_max_len]
                    #print(line_to_merge)
                    geom1=old_geom
                    geom2= line_to_merge["geometry"]
                    geom3=merge_touching_line_string(geom1, geom2)
                    new_id=str(line["id_str"])+"_"+str(line_to_merge["id_str"])
                    #print(new_id)
                    #print(geom3)
                    to_remove.append(line["id_str"])
                    to_remove.append(line_to_merge["id_str"])
                    new_line=line.copy()
                    new_line["id_str"]=new_id
                    new_line["geometry"]=geom3
                    new_line["start"]=geom3.coords[0]
                    new_line["end"]=geom3.coords[-1]
                    new_line["merged"]=True
                    to_add.append(new_line)
                    #print("merge")
                    #sys.exit()
    len_to_add=len(to_add) 
    len_to_remove=len(to_remove)
    print(f"{len_to_add=}")
    print(f"{len_to_remove=}")
    #for line in len_to_add:
    lenframe=len(gpnd)
    print(f"{lenframe=}")
    gpnd = gpnd[~gpnd["id_str"].isin(to_remove)]
    lenframe=len(gpnd)
    print(f"{lenframe=}")
    if len_to_add>0:
        new_ds=geopandas.GeoDataFrame(to_add, crs="EPSG:4326")         
        gpnd2 = pnd.concat([gpnd, new_ds] , ignore_index=True)
        #print("afterconcat")
        #print(gpnd2)
        return complete_touching_paths(gpnd2, processed+1, iteration+1)
    else:
        print("exit")
        #print(gpnd)
        return gpnd
    




def dissolve_on_name(p_gdf):
    results=[]
    for name, group in p_gdf.groupby("name"):
        #print(name)
        #sys.exit()
        tmp_id=group["id"]
        #print(tmp_id)
        #sys.exit()
        geom=shapely.unary_union(group.geometry)
        geom=shapely.line_merge(geom)
        gtype=geom.geom_type.lower()
        geom=geom.normalize()
        if gtype=="linestring": 
            id= group.iloc[0]['id']
            id_str= str(group.iloc[0]['id'])
            results.append({ "type":"way", "tags":group.tags.iloc[0],"id":id, "id_str":id_str, "name":name, "waterway":"river",  "geometry":geom, "merged":True })
        elif gtype=="multilinestring":
            #print(geom)
            suff=0
            for g in geom.geoms:
                id= group.iloc[0]['id']
                id_str= str(group.iloc[0]['id'])+"_split_"+str(suff)
                results.append({ "type":"way", "tags":group.tags.iloc[0],"id": id, "id_str": id_str, "name":name, "waterway":"river", "geometry":g, "merged":True})
                suff=suff+1
            #sys.exit()
        else:
            print(geom)
            sys.exit()
    tmp=geopandas.GeoDataFrame(results, crs=p_gdf.crs)
    tmp=calc_length(tmp)
    tmp["start"]=tmp["geometry"].apply(lambda geom: Point(geom.coords[0]))
    tmp["end"]=tmp["geometry"].apply(lambda geom: Point(geom.coords[-1]))
    return tmp
       
def split_name_no_name(p_gdf):
    p_gdf.name = p_gdf.name.fillna('')
    gpd_with_name=p_gdf[~(p_gdf['name']=="")]
    gpd_without_name=p_gdf[(p_gdf['name']=="")]
    gpd_without_name = gpd_without_name.drop_duplicates(subset="geometry", keep="first")
    return gpd_with_name, gpd_without_name
   
def calc_length(p_gdf):
    gdf2=p_gdf.to_crs("EPSG:3857")
    gdf2["length_m"]=gdf2["geometry"].length
    gdf2=gdf2["length_m"]
    returned=pnd.merge(p_gdf, gdf2, left_index=True, right_index=True)
    return returned
   
   

   
def load_file(p_file):
    global GPD_NAME, GPD_NO_NAME, TO_REMOVE
    gdf = geopandas.read_file(p_file)
    gdf["merged"]=False
    print(gdf)
    gdf=calc_length(gdf)
    print(gdf)
    gdf["start"]=gdf["geometry"].apply(lambda geom: Point(geom.coords[0]))
    gdf["end"]=gdf["geometry"].apply(lambda geom: Point(geom.coords[-1]))
    GPD_NAME, GPD_NO_NAME=split_name_no_name(gdf)
    print(GPD_NAME)
    print(GPD_NO_NAME)
    GPD_NAME=dissolve_on_name(GPD_NAME)
    print(GPD_NAME)
    GPD_NO_NAME["id_str"]=GPD_NO_NAME["id"]
    #GPD_NO_NAME["id_str"]=pnd.to_numeric(GPD_NO_NAME['id_str'], downcast='integer', errors='coerce')
    GPD_NO_NAME["id_str"]=GPD_NO_NAME["id_str"].astype(str)
    
    #for i, row in GPD_NAME.iterrows():
    #   print(row)
    #pandas_to_dict(GPD_NAME, DICT_NAME_1)
    #pandas_to_dict(GPD_NO_NAME, DICT_NO_NAME_1)
    #complete_path( DICT_NO_NAME_1, DICT_NAME_1)
    GPD_NO_NAME_DEF=complete_touching_paths(GPD_NO_NAME)
    len_fr=len(GPD_NO_NAME_DEF)
    print(f"{len_fr=}")
    print(GPD_NO_NAME_DEF)
    GPD_NO_NAME_DEF=GPD_NO_NAME_DEF.drop(["start", "end"], axis=1)
    GPD_NAME=GPD_NAME.drop(["start", "end"], axis=1)
    #print(list(gdf.select_dtypes('geometry').columns))
    GPD_NO_NAME_DEF.to_file(FILE_NO_NAME, layer='rivers', driver="GPKG", mode="w")
    GPD_NAME.to_file(FILE_NAME, layer='rivers', driver="GPKG", mode="w")
    
load_file(FILE)

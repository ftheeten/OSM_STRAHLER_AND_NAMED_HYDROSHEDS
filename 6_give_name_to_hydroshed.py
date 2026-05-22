import pandas as pnd
import geopandas
import shapely
from shapely import unary_union
import sys
import copy
import os
from collections import OrderedDict
from operator import itemgetter

FILE_BASINS="C:\\DivaGisData\\hydrosheds_lake_2026\\hybas_lake_af_lev01-12_v1c\\hybas_lake_af_lev06_v1c.shp"
FILE_NAMED_RIVERS="added_names.gpkg"
OUT_FILE="hybas_lake_af_lev06_v1c_named_osm.gpkg"

def find_touching(p_line_geom, g_sheds):
    touching = g_sheds[g_sheds.geometry.intersects(p_line_geom)]
    return touching


def associate_basin_to_name(f_sheds, f_rivs, p_out):
    result_tmp={}
    g_rivs = geopandas.read_file(f_rivs)
    g_rivs = g_rivs[g_rivs["name"].str.len() > 0]
    g_sheds = geopandas.read_file(f_sheds)
    
    g_sheds["main_river"]=""
    g_sheds["other_rivers"]=""
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
            """
            if "INZIA" in list(by_len.keys()):
                print(names_rivs)
                vals= [key for key in by_len.keys()]
                print(vals)
                print(list(by_len.values()))
                sys.exit()
            """
            vals= [key for key in by_len.keys()] #list(by_len.keys())
            g_sheds.at[idx_shed, "main_river"] = vals[0]
            if len(by_len)>1:                
                merged_tmp=vals[1:]
                merged=';'.join(merged_tmp)
                g_sheds.at[idx_shed, "other_rivers"] = merged
    g_sheds.to_file(p_out, layer='rivers', driver="GPKG", mode="w")
    
associate_basin_to_name(FILE_BASINS, FILE_NAMED_RIVERS, OUT_FILE)
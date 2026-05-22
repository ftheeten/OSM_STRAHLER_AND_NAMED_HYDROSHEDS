import geopandas as gpd
import pandas as pnd
from glob import glob
import traceback
import sys
files = glob("*.geojson")

"""
gdfs = [gpd.read_file(f) for f in files]
"""
i=0
tmp=None
previous=None
for f in files:
    try:
        print("----")
        print(i)
        if tmp is not None:
            previous=tmp.copy()
        tmp=gpd.read_file(f)
        tmp.set_crs(4326)
        tmp.geometry=tmp.geometry.normalize()
        tmp["wkb"] = tmp.geometry.apply(lambda g: g.wkb)
        if i>1:
            tmp= pnd.concat([tmp, previous], ignore_index=True) 
            #print(tmp)
            #sys.exit()
            print(len(tmp))
            tmp = tmp.drop_duplicates(subset="wkb") #.drop(columns="wkb")
            print(len(tmp))

        i=i+1
    except Exception:
        print(traceback.format_exc())
        #sys.exit()
        
tmp.to_file("merged.gpkg", layer='rivers', driver="GPKG", mode="w")
"""
gdf = gpd.GeoDataFrame(
    pd.concat(gdfs, ignore_index=True)
)

gdf["wkb"] = gdf.geometry.apply(lambda g: g.wkb)

gdf = (
    gdf
    .drop_duplicates(subset="wkb")
    .drop(columns="wkb")
)

gdf.to_file(
    "merged.geojson",
    driver="GeoJSON"
)
"""
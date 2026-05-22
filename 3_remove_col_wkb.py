import geopandas as gpd
import pandas as pnd

tmp=gpd.read_file("merged.gpkg")

tmp=tmp.drop(columns="wkb")

tmp.to_file("merged_final.gpkg", layer='rivers', driver="GPKG", mode="w")
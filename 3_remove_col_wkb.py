import geopandas as gpd
import pandas as pnd

files = [ ('Geopackages Files', '*.gpkg')]
FILE= filedialog.askopenfilename(title="input file rivers", filetypes = files, defaultextension = files)
tmp=gpd.read_file(FILE)

tmp=tmp.drop(columns="wkb")

tmp.to_file("merged_final.gpkg", layer='rivers', driver="GPKG", mode="w")
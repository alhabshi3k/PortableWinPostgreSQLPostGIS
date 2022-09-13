#!/usr/bin/env python
# coding: utf-8

# # Web scrapping PostgreSQL and PostGIS downloads site for Binaries
# The main objective is to create a portable PostGreSQL with other Extensions (specifically PostGIS ) from already available binaries without doing installation using installers for Windows. This allow doing experiments of using SQL for querying and analysis. Although PostgreSQL is meant to handle billions of records and manage storages, this is not the objective of having portable PostgreSQL with PostGIS.
# 
# ## Downloading sites: 
# 
#  - https://www.enterprisedb.com/download-postgresql-binaries/
#  - http://download.osgeo.org/postgis/windows/
#  
# ## The Objectives 
# A. Extracting the latest download link from pages
# 
# ### in Linux, experiment done using busybox
# 1. download the main bag and extract the JSON content and save it to a temp.json
# 
# ```bash
# curl -k https://www.enterprisedb.com/download-postgresql-binaries/ | grep -Eo '\{\".*\}' > temp.json
# ```
# 
# 2. Get the latest version , that is the max number
# 
# ```bash
# cat temp.JSON | grep -Eo ' [0-9]{,2}\.[0-9]{,2}' | awk 'max<$0 || NR==1{ max=$0} END{print max}'
# ```

# In[ ]:


import json, time, re , os, shutil
from urllib.request import urlopen, urlretrieve
from zipfile import ZipFile, Path
from shutil import move, rmtree, copytree, make_archive

o_s, arch = 'windows', "x86-64"
dl , pg= "download", 'postg'
download_links = {'pgsql': f"https://www.enterprisedb.com/{dl}-{pg}resql-binaries/" , 'postgis': f"http://{dl}.osgeo.org/{pg}is/{o_s}/"}


# In[ ]:


# --- The Following code was for situation when the links encapsuled in JSON - Something have changed to page
## curl -k https://www.enterprisedb.com/download-postgresql-binaries/ | grep -Eo '\{\".*\}' > temp.json
# JSON_conext = re.search('\{\".*\}', urlopen(download_links['pgsql']).read().decode() ).group(0)
## cat temp.JSON | grep -Eo ' [0-9]{,2}\.[0-9]{,2}' | awk 'max<$0 || NR==1{ max=$0} END{print max}'

# txt_start = f'{o_s}" href="'

# pg_ver = str(max( float(r) for r in re.findall(' ([0-9]{,2}\.[0-9]{,2})', JSON_conext) ))   # get the least version of stable postgreSQL
# temp_json = json.loads( JSON_conext )["props"]["pageProps"]["content"].split("<b>Version ")
# scrap = { r[:4]: r[r.rfind(txt_start)+ len(txt_start):r.rindex('"><',None,r.find(f"{o_s}_sm_{arch}"))]  for r in temp_json if r[:2].isdigit() }
# download_links['pgsql'] = urlopen(scrap[pg_ver]).geturl()
# ---------------------------------------------------------------------------
# ----- the page is now link static HTML with elements of paragraphs --------
page = urlopen(download_links['pgsql']).read().decode()
import xml.etree.ElementTree as ET
paragraphs = ET.fromstring(page).findall(".//p")
# Get Most recent PostgreSQL version
pg_ver = max([ float(".".join(p.text.split(" ").pop().split(".")[:2])) for p in ET.fromstring(page).findall('.//p/span') if "(Not supported)" not in p.text ])
pg_ver_text = F"Version {pg_ver}"
# Get the paragraph element that followed the mentioning of the version
paragraph_with_links = [ paragraphs[paragraphs.index(p)+1] for p in paragraphs if p.findtext("span") == pg_ver_text].pop()
# Get the link that is related to 
link = [ alink.attrib["href"] for alink in paragraph_with_links.findall('a') if f"{o_s}_sm_{arch}" in alink.find("img").attrib["src"] ].pop()
download_links['pgsql'] = urlopen(link).geturl()
# download_links['pgsql'] # testing


# In[ ]:


# get the latest crosspond PostgreSQL version that PostGIS is compiled for.
res = urlopen(download_links['postgis']).read().decode().splitlines()
# pg_ver_Postgis  = max( href[href.find("pg"):href.find("/")+1] for href in res if any([time.strftime("%Y-%b", time.gmtime()) in href,  href.find("pg9") < 0, href.find("pg") > 0]) )
# assert pg_ver_Postgis[2:4] == pg_ver[:2], f"PostGIS for PostgreSQL v{pg_ver_Postgis[2:4]} do not match PostgreSQL v{pg_ver[:1]}"
pg_ver_Postgis  = [ href[href.find("pg"):href.find("/")+1] for href in res  if F"{round(pg_ver)}/" in href ].pop()
res = urlopen(f"{download_links['postgis']}{pg_ver_Postgis}").read().decode().splitlines()
# Get the file name of PostGIS binaries bundle and not the executable installer. that is the Zip file
dfile = [ r[r.find("postgis"):r.find('.zip')+4] for r in res if '.zip"' in r ].pop()
download_links['postgis'] = f"{download_links['postgis']}{pg_ver_Postgis}{dfile}"
postgis_ver = download_links['postgis'][download_links['postgis'].rfind("-")+1:download_links['postgis'].rfind("x")]


# In[ ]:


# Setting up folders and packed file name
# ----------------------------------------
from pathlib import Path
download_dir = Path("downloads")
download_dir.mkdir(parents=True, exist_ok=True)
extraction_dir = download_dir / Path("pgsql")
extraction_dir.mkdir(parents=True, exist_ok=True)
packed_file = download_dir / f"Portable-PG{pg_ver}-PostGIS-v{postgis_ver}"


# In[ ]:


# Sending information to Systen environment
# -----------------------------------------
print(f"{pg_ver}", download_links['pgsql'], postgis_ver, download_links['postgis'], f"{packed_file}.zip")
# Report Information
# ------------------
print(f"PostgreSQL version : pg{pg_ver}", F"PostGIS version: {postgis_ver}", sep="\n")
[ print(f"- {link} : {v}") for link,v in download_links.items() ].pop()


# In[ ]:


for link in download_links.values():
    print(f"Downloading  {link} ==> " , end=" ")
    filename = link[link.rfind("/")+1:]
    # filename = link.rsplit('/').pop()  or link[link.rfind("/")+1:]
    # zipfile = ZipFile(urlretrieve(link,filename= link.rsplit('/').pop())[0])
    zipfile = ZipFile(filename) or ZipFile(urlretrieve(link,filename= filename )[0])
    print(f" DONE")
    print(f"- Extracting  {zipfile.filename} ==> " , end=" "); print( (zipfile.extractall(), f"DONE")[1] )
    possible_unpacked_path = Path(zipfile.filename[:-len(".zip")])
    # Get Root/Main directories in zip file, 
    # in case the zipping process was one directory and the then the zipped file have the same filename.
    root_dirs = [f.filename for f in zipfile.filelist if f.filename.count("/") == 1 and f.filename.endswith("/")] 
    if possible_unpacked_path.is_dir() or len(root_dirs) == 1: 
        root_dir = Path(root_dirs.pop()[:-len("/")])    
        # if extraction_dir.name is root_dir.name: continue 
        for f in root_dir.glob("*"): 
            if f.name in (root_dir.name, ".ipynb_checkpoints") : continue
            if f.is_file():  move( f, extraction_dir )  
            else: copytree(f, extraction_dir / Path(f.parts[1]), dirs_exist_ok=True); rmtree(f)
        rmtree(root_dir)


# In[ ]:


## TODO 
# - Removing un-need file and directories
# --> symbols,  pgAdmin III, StackBuilder , doc
folder_to_remove = ['symbols',  'pgAdmin III', 'StackBuilder' , 'doc', 'include','bin/postgisgui']
print("Deleting Unwanted folders => ", end=" ")
[ rmtree( extraction_dir / folder, ignore_errors=True) for folder in folder_to_remove ].pop()
print(" DONE")

print("Deleting Unwanted Files =>", end=" ")
patterns = ["bin/wx*.*","bin/stackbuilder.exe"] # of files in folder to delete.
[f.unlink(missing_ok=False)  for pattern in patterns for f in extraction_dir.glob(pattern)].pop()
print(" DONE")
# - Detect and remove duplicated files.

# organize the dll
# copy Batchfile scripts and other helpful light programs


# In[ ]:


# Final Archive The Whole Directory. or let Github action do The Archiveing and produce Zip file
# print("zipping all => ", end=" ")
# packed_file = make_archive( packed_file , "zip", root_dir = extraction_dir.parent, base_dir = extraction_dir )  # zipping the directory
# print(" DONE")

## Try to leave the option of compression the folde to GithubActions.

# rmtree(extraction_dir, ignore_errors=True) # It didn't work

# TODO:
# - DELETE the Downloaded zipped file
# - DELETE the pgsql folder 


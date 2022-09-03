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

# In[1]:


import json, time, re #  os, shutil
from urllib.request import urlopen, urlretrieve
from zipfile import ZipFile, Path
from shutil import move, rmtree, copytree, make_archive

o_s, arch = 'windows', "x86-64"
dl , pg= "download", 'postg'
download_links = {'pgsql': f"https://www.enterprisedb.com/{dl}-{pg}resql-binaries/" , 'postgis': f"http://{dl}.osgeo.org/{pg}is/{o_s}/"}


# In[2]:

# curl -k https://www.enterprisedb.com/download-postgresql-binaries/ | grep -Eo '\{\".*\}' > temp.json
JSON_conext = re.search('\{\".*\}', urlopen(download_links['pgsql']).read().decode() ).group(0)
# cat temp.JSON | grep -Eo ' [0-9]{,2}\.[0-9]{,2}' | awk 'max<$0 || NR==1{ max=$0} END{print max}'

txt_start = f'{o_s}" href="'

pg_ver = str(max( float(r) for r in re.findall(' ([0-9]{,2}\.[0-9]{,2})', JSON_conext) ))   # get the least version of stable postgreSQL
temp_json = json.loads( JSON_conext )["props"]["pageProps"]["content"].split("<b>Version ")
scrap = { r[:4]: r[r.rfind(txt_start)+ len(txt_start):r.rindex('"><',None,r.find(f"{o_s}_sm_{arch}"))]  for r in temp_json if r[:2].isdigit() }
download_links['pgsql'] = urlopen(scrap[pg_ver]).geturl()

# In[3]:


# get the latest crosspond PostgreSQL version that PostGIS is compiled for.
res = urlopen(download_links['postgis']).read().decode().splitlines()
pg_ver_Postgis  = max( href[href.find("pg"):href.find("/")+1] for href in res if all([time.strftime("%Y-%b", time.gmtime()) in href,  href.find("pg9") < 0, href.find("pg") > 0]) )
assert pg_ver_Postgis[2:4] == pg_ver[:2], f"PostGIS for PostgreSQL v{pg_ver_Postgis[2:4]} do not match PostgreSQL v{pg_ver[:1]}"
res = urlopen(f"{download_links['postgis']}{pg_ver_Postgis}").read().decode().splitlines()
# Get the file name of PostGIS binaries bundle and not the executable installer. that is the Zip file
dfile = [ r[r.find("postgis"):r.find('.zip')+4] for r in res if '.zip"' in r ].pop()
download_links['postgis'] = f"{download_links['postgis']}{pg_ver_Postgis}{dfile}"
postgis_ver = download_links['postgis'][download_links['postgis'].rfind("-")+1:download_links['postgis'].rfind("x")]


# In[ ]:


from pathlib import Path
extraction_dir = Path("pgsql")
extraction_dir.mkdir(parents=True, exist_ok=True)

for link in download_links.values():
    # print(f"Downloading  {link} ==> " , end=" ")
    # zipfile = link.rsplit('/').pop()
    zipfile = ZipFile(urlretrieve(link,filename= link.rsplit('/').pop())[0])
    # print(f" DONE")
    # Get Root/Main directories in zip file, 
    # in case the zipping process was one directory and the then the zipped file have the same filename.
    root_dirs = [f.filename for f in zipfile.filelist if f.filename.count("/") == 1 and f.filename.endswith("/")] 
    
    zipfile.extractall() # print(f"- Extracting  {zipfile.filename} ==> " , end=" "); print( (zipfile.extractall(), f"DONE")[1] )
    
    possible_unpacked_path = Path(zipfile.filename.removesuffix(".zip"))
    if possible_unpacked_path.is_dir() or len(root_dirs) == 1: 
        root_dir = Path(root_dirs.pop().removesuffix("/"))    
        if extraction_dir.name is root_dir.name: continue 
        for f in root_dir.glob("*"): 
            if f.name in (root_dir.name, ".ipynb_checkpoints") : continue
            if f.is_file():  move( f, extraction_dir )  
            else: copytree(f, extraction_dir / Path(f.parts[1]), dirs_exist_ok=True); rmtree(f)
        rmtree(possible_unpacked_path)
    zipfile.close() 
    Path(link.rsplit('/').pop()).unlink(missing_ok=False)

# In[ ]:


## TODO 
# - Removing un-need file and directories
# --> symbols,  pgAdmin III, StackBuilder , doc
folder_to_remove = ['symbols',  'pgAdmin III', 'StackBuilder' , 'doc', 'include','bin/postgisgui']
for folder in folder_to_remove:  rmtree( extraction_dir / folder, ignore_errors=True)

patterns = ["bin/wx*.*","bin/stackbuilder.exe"] # of files in folder to delete.
for pattern in patterns: 
    for f in extraction_dir.glob(pattern): f.unlink(missing_ok=False)
# - Detect and remove duplicated files.

# Organize the dll
# copy Batchfile scripts and other helpful light programs


# In[ ]:


# Final Archive The Whole Directory.
packed_file = f"Portable-PG{pg_ver}-PostGIS-v{postgis_ver}"
make_archive( packed_file , "zip", extraction_dir.parent, extraction_dir )  # zipping the directory
## Try to leave the option of compression the folde to GithubActions.
rmtree(extraction_dir, ignore_errors=True)
# In[6]:


# Report Information
# ------------------
# print(f"PostgreSQL version : pg{pg_ver}", F"PostGIS version: {postgis_ver}", sep="\n")
# [ print(f"- {link} : {v}") for link,v in download_links.items() ][0]


print(f"{pg_ver}", download_links['pgsql'], postgis_ver, download_links['postgis'], f"{packed_file}.zip")
#postgresql_zipfile = urllib.request.urlretrieve(pgsql_download_link,filename= pgsql_download_link.rsplit('/').pop())
# postgis_zipfile = urllib.request.urlretrieve(postgis_download_link,filename= postgis_download_link.rsplit('/').pop() )

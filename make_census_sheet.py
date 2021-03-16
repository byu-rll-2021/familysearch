# -*- coding: utf-8 -*-
"""
Created on Thu Feb 18 13:09:18 2021

@author: jaredmw2
"""

import re
import sys
import json
import os
import requests
import pandas as pd
import numpy as np
import time
import math
import subprocess

#sys.path.append(r'R:\JoePriceResearch\Python\all_code')
os.chdir(r'V:\FHSS-JoePriceResearch\tools')
from FamilySearch1 import FamilySearch

FSusername = 'jared_wright'
FSpassword = 'n1k0las2'
directory = r"V:\FHSS-JoePriceResearch\RA_work_folders\Jared_Wright\Salt_Lake_census_sheet"
city = "Salt Lake"
county = ""
state = "Utah"
years = [1900, 1910, 1920, 1930, 1940]
inputfile = 'index_ark1910.csv'
outputfile = 'pids_scraped.csv'


# SPECIFY HOW MANY PROCESSES TO RUN AT ONCE:
num_processes = 20
############################################################################################################################################



"""
Get arks in a place (without using the refined census folders… scrape family search)
not sure how to do this without the refined census. may need to scrape every time we
start a new sheet
the file 
R:\JoePriceResearch\Python\all_code\FamilySearch1\ArkSearch.py may be of interest
"""
#for now get the arks for a specific place using the refined census data. Put the csv file in the directory 
#with first column an index and second column the list of arks. Change "inputfile" below to match file name.


"""
Scrape for pids using arks
V:\FHSS-JoePriceResearch\RA_work_folders\Ace_Haws\1910_tree\scrape_pids.py
"""

#inputfile must have only two columns, first column is a unique "index", 
#second column contains your arks (column header doesn't matter)
os.chdir(directory)
fs = FamilySearch(FSusername, FSpassword, directory, inputfile, 'temp_pids.csv', auth=True)
fs.GetPidFromArk()


"""
Scrape birth and death dates and census records 
V:\FHSS-JoePriceResearch\RA_work_folders\Neil_Duzett\master_scrape\split_scrape.py
V:\FHSS-JoePriceResearch\RA_work_folders\Neil_Duzett\master_scrape\scrape.py

V:\FHSS-JoePriceResearch\RA_work_folders\Ace_Haws\code_examples\scrape_person.py
documentation at
R:\JoePriceResearch\Python\all_code\FamilySearch1\Documentation\ScrapePerson.txt
"""


############################################### MODIFY THIS SECTION ONLY ###################################################################
# SPECIFY SAVE DIRECTORY:
csv_url = directory # arg 1
# SPECIFY CSV TO RUN:
csv_to_run = os.path.join(directory, 'temp_pids.csv') # arg 2
print(csv_to_run)

# SPECIFY TYPE:
# allowed types are: hop, scrape
run_type = "scrape" # arg 8

# SPECIFY TYPE-SPECIFIC VARIABLES:
    # For hops...
num_hops = 3 # arg 9
    # For scrapes... allowed features: name, byear_dyear, census_arks, baptism_date, creation_info, num_sources, num_hints, census_hints, residences, parents, contributors, kids, duplicates, blue_hints
scrape_features = ["byear_dyear", "census_arks"] # arg 10

############################################################################################################################################

# Don't misuse these 
un_pw = [['neil_duzett', 'Something199442'], ['danielsabey', 'Seoulsouth2015'], ["soccertomb", "Tombryan1"]]

bat_path = 'run_scrape.bat'

num_rows = 0
for row in open(csv_to_run):
    num_rows += 1

how_many = int(num_rows / num_processes) + (num_rows % num_processes > 0) # arg 4
user_switch_cutoff = int(num_processes / len(un_pw)) + (num_processes % len(un_pw) > 0)
user_num = 0

if run_type == "scrape":
    for x in range(1, num_processes + 1):
        
        if (user_num + 1) * user_switch_cutoff < x:
            user_num += 1
        username = un_pw[user_num][0] # arg 6
        password = un_pw[user_num][1] # arg 7
        
        csv_to_save = f'temp_scraped_{x}.csv' # arg 3
        where_to_start = (x - 1) * how_many # arg 5
        
        print("Starting process " + str(x) + " on section " + str(where_to_start) + " / " + str(num_rows) + " with a chunk size of " + str(how_many) + ". User: " + username)
        arg_list = [csv_url, csv_to_run, csv_to_save, str(how_many), str(where_to_start), username, password, run_type, str(num_hops), "?".join(scrape_features)]
        executable = os.path.join(r'V:\FHSS-JoePriceResearch\RA_work_folders\Neil_Duzett\master_scrape', bat_path)
        # Arguments: working directory, csv to run on, csv save name, how many lines to give to a process, which line to start on, fs username, fs password, process type (hop or scrape), num_hops, scrape_features
        p = subprocess.Popen([executable, "+".join(arg_list)], creationflags=subprocess.CREATE_NEW_CONSOLE)

        time.sleep(10)
    print("Running " + str(num_processes) + " processes on ".format(run_type) + csv_to_run + ", saving as " + csv_to_save)
    
elif run_type == "hop":
    username = un_pw[user_num][0] # arg 6
    password = un_pw[user_num][1] # arg 7
    arg_list = [csv_url, csv_to_run, "", str(0), str(0), username, password, run_type, str(num_hops), "?".join(scrape_features)]
    executable = os.path.join(r'V:\FHSS-JoePriceResearch\RA_work_folders\Neil_Duzett\master_scrape', bat_path)
    # Arguments: working directory, csv to run on, csv save name, how many lines to give to a process, which line to start on, fs username, fs password, process type (hop or scrape), num_hops, scrape_features
    p = subprocess.Popen([executable, "+".join(arg_list)], creationflags=subprocess.CREATE_NEW_CONSOLE)




"""
Scrape for blue hints
Do we want to count blue hints as attached? What did we do for Skagit?



fs = FamilySearch(FSusername, FSpassword, directory, 'temp_pids.csv', 'temp_hints.csv', auth=True)
outputfile = fs.GetBlueHintsAA(sheet='temp_pids.csv', idcolint = 0) #idcolint is the column index that the pids are in
    
print('Blue Hints complete: ', outputfile)
"""

"""
Create census sheet
create link to pid for avalable pids
Add ‘---’ for years not alive
Add “complete?” and “volunteer” columns
I could do this myself. But whoever did it for Skagit could do it faster
Dataframe to csv
"""


os.chdir(directory)
df = pd.read_csv('temp_scraped_1.csv', header=0, engine='python')
df.columns = ['pid', 'birthdate', 'deathdate', 'censuslinks', 'censusdesc']
for i in range(num_processes - 1):
    filename = 'temp_scraped_' + str(i+2) + '.csv'
    tmpdf = pd.read_csv(filename, names=['pid', 'birthdate', 'deathdate', 'censuslinks', 'censusdesc'], engine='python')
    df = df.append(tmpdf, ignore_index=True)
    print(df.shape)

#we don't need to export to csv unless we add the section to get blue hints
#df.to_csv('temp_scraped.csv')


df['birthyear']=df['birthdate'].str.extract(r'(\d{4})')
df['deathyear']=df['deathdate'].str.extract(r'(\d{4})')
df.drop(columns=['birthdate', 'deathdate'], inplace=True)
df['censuslinks'] = df['censuslinks'].str.split(';')
df['censusdesc'] = df['censusdesc'].str.split(';')
print(df['censuslinks'][0])
print(df['censusdesc'][0])


df['samelen'] = df['censuslinks'].str.len()==df['censusdesc'].str.len()
df = df.loc[df.samelen, :]
df.drop(columns=['samelen'], inplace=True)

#source: https://stackoverflow.com/questions/12680754/split-explode-pandas-dataframe-string-entry-to-separate-rows/40449726#40449726
def explode(df, lst_cols, fill_value='', preserve_index=False):
    # make sure `lst_cols` is list-alike
    if (lst_cols is not None
        and len(lst_cols) > 0
        and not isinstance(lst_cols, (list, tuple, np.ndarray, pd.Series))):
        lst_cols = [lst_cols]
    # all columns except `lst_cols`
    idx_cols = df.columns.difference(lst_cols)
    # calculate lengths of lists
    lens = df[lst_cols[0]].str.len()
    # preserve original index values    
    idx = np.repeat(df.index.values, lens)
    # create "exploded" DF
    res = (pd.DataFrame({
                col:np.repeat(df[col].values, lens)
                for col in idx_cols},
                index=idx)
             .assign(**{col:np.concatenate(df.loc[lens>0, col].values)
                            for col in lst_cols}))
    # append those rows that have empty lists
    if (lens == 0).any():
        # at least one list in cells is empty
        res = (res.append(df.loc[lens==0, idx_cols], sort=False)
                  .fillna(fill_value))
    # revert the original index order
    res = res.sort_index()
    # reset index if requested
    if not preserve_index:        
        res = res.reset_index(drop=True)
    return res

df = explode(df,['censuslinks', 'censusdesc'], preserve_index=False)

df['censusyears']=df['censusdesc'].str.extract(r'United States Census\,\s(\d{4})')
df['censusarks']=df['censuslinks'].str.extract(r'(\w{4}-\w{3})$')

for year in years:
    df.loc[df.birthyear==str(year), 'ark'+ str(year)] = df['censusarks']
    df['ark'+ str(year)] = ""
    df.loc[df.censusyears==str(year), 'ark'+ str(year)] = df['censusarks']

df.drop(columns=['censusdesc', 'censuslinks', 'censusarks', 'censusyears'], inplace=True)
df = df.fillna('')
#df = df.groupby(['pid', 'birthyear', 'deathyear']).agg(''.join)
#df = df.groupby(['pid', 'birthyear', 'deathyear']).agg(lambda x: ''.join(x.unique()))
df = df.groupby(['pid', 'birthyear', 'deathyear']).max()
df.reset_index(level=df.index.names, inplace=True)

df["byr"] = pd.to_numeric(df["birthyear"])
df["dyr"] = pd.to_numeric(df["deathyear"])
for year in years:
    df.loc[df.byr > year, 'ark'+ str(year)] = "---"
    df.loc[df.dyr < year, 'ark'+ str(year)] = "---"
df.drop(columns=['byr', 'dyr'], inplace=True)

df['person_url'] = 'https://www.familysearch.org/tree/person/details/' + df['pid']
df.drop(columns=['pid'], inplace=True)
df = df[['person_url', 'birthyear', 'deathyear', 'ark1900', 'ark1910', 'ark1920',
       'ark1930', 'ark1940']]
#is_NaN = df.isnull()
#row_has_NaN = is_NaN.any(axis=1)
df['complete?'] = ""
#df = df.replace({'complete?': {True: '',  False: 'complete'}})
df['volunteer'] = ""

os.chdir(directory)
df.to_csv('census_sheet.csv', index=False)

print(df.shape)
print(df.columns)
print(df.head)






# -*- coding: utf-8 -*-
"""
Created on Wed May 30 14:28:05 2018

@author: bbranchf
"""

import sys

sys.path.append(r'R:\JoePriceResearch\Python\Miniconda\envs\record_linking\Lib\site-packages')

import time
import pandas as pd
import re
import requests
import asyncio
import aiohttp
#import os
import json

async def get(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return response
async def do_other_things():
    print('doing other things')
        
def GetBlueHintsAA(self, sheet,  idcolint=0, header=True):
    '''
    This function uses the family search api to get record hints for a list
    of pids from a google sheet and adds them to the sheet in the column 
    specified in out_col.
        
    Parameters
    ----------
    google_sheet (bool)     = whether or not the data comes from a google sheet
    sheet (str)             = the id code of the google sheet(s) to work on or the filename to use
        given https://docs.google.com/spreadsheets/d/1jhn5D1HFWnDr3JHgu3E6ktbuL7FIUvmSLGfIxZj9ZVk/edit#gid=0
        sheet = "1jhn5D1HFWnDr3JHgu3E6ktbuL7FIUvmSLGfIxZj9ZVk"
    
    idcolstr                 = the letter corresponding to the column with FSIDs
    
    idcolint                = the index of the column with FSIDs (if not using google sheets)
    
    out_col (str)           = the letter of the column for record links

    header (bool)           = declares whether or not there are headers in 
                            the file/sheet to be read. Thsi will nost likely 
                            be True for all google docs we work with
                            
    record_type (str)       = What kind of records should be searched for
                                'any': default
                                    gets any record type
                                'census': if no year is declared it will find 
                                    the first census hint
                                'death': gets record hints for obituaries,
                                    graves and death records
                                'birth': I think you probably get it by now
                                'marriage': 
    cen_year (str)          = the year of the census you would like
    
    links (bool)            = if True then the first record hint will be given
                                as a url linking directly to the record 
                                attachment
    '''
    #if google_sheet==True:
    
    # Get an API token.
    token = self.Authenticate()
    
    # Read the ids.
    full_df = pd.read_csv(sheet)
    ids = full_df.iloc[:,idcolint]
    
    # assigning what to look for 
    #regex = '.*'
    # considering the presence of headers
    
    pids = []
    match = []
    hints = []
    titles = []
    # Get a list of pids.
    idlist = ids.str.extract('([0-9A-Z]{4}-[0-9A-Z]{3}[0-9A-Z]*)', expand=False).fillna('')
    # Initialize total time.
    tot = 0.0
    num = 1
    '''
    loop = asyncio.get_event_loop()
    coroutines = [get(f'https://www.familysearch.org/service/tree/tree-data/record-matches/{fsid}/all?hintsOnLiving=true&livingHintsEx=true') for fsid in idlist]
    results = loop.run_until_complete(asyncio.gather(*coroutines))
    #loop.run_until_complete(do_other_things())

    
    print("Results: %s" % results)
    loop.close()
#    in_line = True
    # establishing a connection
    '''
    with requests.Session() as s:
        # let them know who we are and what format to retrieve data
        s.headers.update({'Authorization': 'Bearer %s' %(token),
                          'Accept':'application/json'})
        for fsid in idlist:
            start = time.time()
            try:
                #print(time.time()-start)
                pull = s.get(f'https://www.familysearch.org/service/tree/tree-data/record-matches/{fsid}/all?hintsOnLiving=true&livingHintsEx=true')
                #print(time.time()-start)
                #print(pull.status_code)
                if pull.status_code != 200:
                    for i in range(3):
                        #print ("tried case")
                        pull = s.get(f'https://www.familysearch.org/service/tree/tree-data/record-matches/{fsid}/all?hintsOnLiving=true&livingHintsEx=true')
                        if pull.status_code == 200:
                            break
                        elif i == 2:
                            print(f'no record hints retrieved for {fsid}')
            except:
                print(f'no record hints retrieved for {fsid}')
    
            try:
                #entry_list = pull.json()['entries']
                data = pull.json()['data']['matches'][0]
                #print(data)
                ark = re.search(r"(?<=1:1:)([A-Z0-9]{4}-[A-Z0-9]{3,4})",str(data)).group(1)
                score = data['score']
                titles.append(data['collectionTitle'])
                match.append(score)
                hints.append(f'https://www.familysearch.org/search/linker?pal=/ark:/61903/1:1:{ark}&id={fsid}')
                pids.append(fsid)
                #print('found one!')
                
            except:
                #print("exception")
                pass
               
            #Get the end time.
            end = time.time()
            #print(end-start)
            # Print the time total.
            tot = tot + (end-start)
            num += 1
            av = tot/num
            if num % 200 == 0:
                print(str(num) + " of " + str(ids.shape[0]))
                print('Average time per person: ', round(av,4))
                print('Minutes Left:', round(((len(idlist)-num)*av)/60, 3), '\n')
                
    #        if in_line and len(records) != num:
    #            print("Warning: The references may not be in line with the corresponding FSIDs")
    #            print("The first instance of them being off occured at line " + str(num))
    #            in_line = False
    
    full_df['pid'] = pd.Series(pids)
    full_df['match_score'] = pd.Series(match)
    full_df['collection'] = pd.Series(titles)
    full_df['hint'] = pd.Series(hints)
    
    full_df.to_csv(self.outfile, index=False, header=header)
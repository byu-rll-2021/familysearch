# -*- coding: utf-8 -*-
"""
Created on Fri Apr 27 14:09:55 2018

@author: bbranchf

This is a file declaring the DeletedCleaner function for the FamilySearch
class. It is to be referenced in the __init__.py

this new version uses the api and while it has to do one at a time it will
be way faster than any selenium scrape we do


#########################################################
NOTE: As of 24 Jan 2019, The function does not appear to be working for 
certaing files. The file that it does not work on ismade up entirely of 
deleted ids and it is returning a 500 error probably because it expects
to get something from the call but it does not.
#########################################################



"""

import sys

sys.path.append(r'R:\JoePriceResearch\Python\Anaconda3\Lib\site-packages')

import pandas as pd
import re
import requests
import os
from time import sleep, time
import json
# from selenium.common.exceptions import NoSuchElementException
import http.client


def ReplaceDeleted(self, sheet_list='', idcol='A', google_sheet=True,
                   header=True, delim=",", overwrite=True, write_changed=False,
                   sheet_name='Sheet1', verbosity=0):
    '''
    This function uses the family search api to find all of the FSIDs on
    a google sheet that correspond to a deleted person. The function then
    finds the new FSIDs and changes them to the most current one.
        
    Parameters
    ----------
    google_sheet (bool)     = declares if the file to be edited is
                            a google sheet or not
    if google_sheet = True (Default)
        sheet_list (list)   = the id code of the google sheet(s) to work on
            given https://docs.google.com/spreadsheets/d/1jhn5D1HFWnDr3JHgu3E6ktbuL7FIUvmSLGfIxZj9ZVk/edit#gid=0
            sheet_list[i]   = "1jhn5D1HFWnDr3JHgu3E6ktbuL7FIUvmSLGfIxZj9ZVk"
    
    if google_sheet = False
        sheet_list (list)   = the filenames of the csv. The full filepath
                              will be necessary if the file is in a directory
                              other than the one in the class initialization
    **** if only one sheet is desired it may be entered as a string and it
            will be coerced into a list object
    idcol (str)             = the letter corresponding to the column with FSIDs
                                or the column number in the case of a csv 
                                (start at 1, not 0)
    header (bool)           = declares whther or not there are headers in 
                                the file/sheet to be read.
    delim (str)             = the delimiter for the file to be read. Only 
                                for use with google_sheet = False. 
    '''
    
    
    
    #use the login function.
    # replace_driver = self._login()
    
    if type(sheet_list) == str and sheet_list != '':
        # this coerces a string into a list with one element so you can pass
        # one or multiple sheets
        sheet_list = sheet_list.split()
    elif sheet_list == '':
        sheet_list = [self.infile]
    
    for i in range(len(sheet_list)):
        
        if google_sheet == True:
            # coercing idcol to uppercase
            idcol = idcol.upper()
            # Read the ids.
            df = pd.DataFrame(self._google_read(sheet_list[i],f'{sheet_name}!{idcol}:{idcol}'.format()), columns=['pids']).fillna(value='')
            
        else:
            if type(idcol) == str:
                idcol = int(input("Please input a number for the column (start at 1): "))
            
            try:
                # get the header later don't worry that header=None
                if sheet_list[i][-3:] == 'csv':
                    full_df = pd.read_csv(sheet_list[i], header=None, sep=delim)
                elif sheet_list[i][-3:] in ['xls','lsx','lsm']:
                    full_df = pd.read_excel(sheet_list[i], header=None, sep=delim)
            except UnicodeDecodeError:
                if sheet_list[i][-3:] == 'csv':
                    full_df = pd.read_csv(sheet_list[i], header=None, encoding='latin')
                elif sheet_list[i][-3:] in ['xls','lsx','lsm']:
                    full_df = pd.read_excel(sheet_list[i], header=None, encoding='latin')
            # Read the ids.
            df = pd.DataFrame(full_df[idcol - 1]).rename(columns={idcol-1:'pids'})
            
        # Get a list of pids.
        first = df.pids.iloc[0]
        df['pids_old'] = df['pids']
        df['pids'] = df['pids'].str.replace('([0-9A-Z]{4})([0-9A-Z]{3})',r'\1-\2')
        df['pids'] = df['pids'].str.extract('([0-9A-Z]{4}-[0-9A-Z]{3}[0-9A-Z]*)', expand=False)
        idlist = df['pids'].loc[df.pids.str.contains('[0-9A-Z]{4}-[0-9A-Z]{3}[0-9A-Z]*') == True]
        
        if verbosity > 0:
            print('gathered pids')
        
        with requests.Session() as session:
            # assigning 
            headers={'Authorization': 'Bearer %s' %(self.token), 'Accept':'application/json'}
            session.headers.update(headers)
            
            # Loop to get 200 ids
            allids = set()
            for x in range(0, len(idlist), 200):
                if x % 1000 == 0:
                    print("Checking: ", x, " of ", len(idlist))
                # Join all the ids together.
                ids = ','.join(idlist[x:x+200])
                
                # Initialize an array.
                newids = []
                split_lists = []
                switch_502 = False
                again = True
                fails = 0
                first_502 = True
                while again:
                    if switch_502:
                        ids = split_lists.pop(0)
                    if switch_502 and first_502:
                        print('\nYou got a 502 error, which may mean that you are using arkIDs as pids')
                        first_502 = False
                    # Use the API to check which pids are deleted.
                    try:
                        pull = session.get(f'http://api.familysearch.org/platform/tree/persons?pids={ids}')
                        if verbosity > 1:
                            print('made a call')
                    except http.client.HTTPException:
                        if fails <= 10:
                            http.client._MAXHEADERS += 100
                            continue
                        else:
                            again = False
                            continue
                        
                    if pull.status_code == 502: 
                        # this isn't in the familysearch API docs we think it is caused by asking for arkIDs but
                        switch_502 = True
                        split_lists.append(ids[:int(len(ids.split(',')))])
                        split_lists.append(ids[int(len(ids.split(','))):])
                    elif pull.status_code == 204:
                        print("204 error.")
                        raise e
                    elif pull.status_code == 429:
                        wait = (int(pull.headers['Retry-After'])*1.1)
                        print('Throttled, waiting {0: .1f} seconds!'.format(wait))
                        time.sleep(wait)
                    if i == 4:
                        raise badRequestError
                    elif pull.status_code == 200 and len(split_lists) == 0:
                        again = False
                # Get the text.
                text = pull.json()
                
                # Find all pids that are not deleted.
                newids = newids + [self._remove_non_ascii(y['id']) for y in text['persons']]
                
                # Make a list of deleted ids.
                for y in idlist[x:x+200]:
                    # Get the pid for those deleted.
                    if y not in newids:
                        allids.add(y)
            
            if verbosity >= 0:
                print('completed checking, getting new ids')
            
            # Initialize total time.
            tot = 0.0
            num = 0
            
            bad_ids = dict()
            new_ids = []
            
            idlist = list(allids)
            
            # Check the deleted ids.
            for fsid in idlist:
                # Skip if not an id.
                if not re.search('[0-9A-Z]{4}-[0-9A-Z]{3}[0-9A-Z]*', fsid):
                    continue
                
                # Get the start time.
                start = time()
                
                info = session.get('http://api.familysearch.org/platform/tree/persons/%s' %(fsid))
    
                ##Try a lot to get the request to actually work
                for z in range(25):
                    if info.status_code == 403:
                        print(f'We couldn\'t get info on {fsid} it was "forbidden" by family search')
                        newid = fsid
                        bad_ids[fsid] = 403
                        break   
                    elif info.status_code == 404:
                        print(f'{fsid} is likely not a real person as the API didn\'t have any information on them')
                        newid = fsid
                        bad_ids[fsid] = 404
                        break
                    elif info.status_code == 410:
                        print(f'{fsid} has been deleted and we could not find the correct one')
                        newid = ''
                        bad_ids[fsid] = 410
                        break
                    try:
                        newid = re.search('[0-9A-Z]{4}-[0-9A-Z]{3}[0-9A-Z]?', info.json()['links']['alternate'][0]['href'])[0]
                        break
                    except KeyError:                       
                        try:
                            newid = re.search('[0-9A-Z]{4}-[0-9A-Z]{3}[0-9A-Z]?', info.json()['persons'][0]['id'])[0]
                        except KeyError as e:
                            print('new format of json')
                            with open('out_test.txt', 'w') as out:
                                json.dump(out, info.json(), indent = 4)
                            print(f'Exported json for pid {fsid} to {os.getcwd()}\\out_test.txt')
                            newid = ''
                            # print('\n\n', info.json())
                            # print('\n\n', info.json().keys())
                            # raise e
                    except (IndexError, ValueError) as e:
                        raise e
                    except:
                        info = session.get('http://api.familysearch.org/platform/tree/persons/%s' %(fsid))

                new_ids.append(newid)
                    
                '''
                if z == 5:
                    print(fsid)
                    print('Status Code:', info.status_code)
                    print('Having some problems finding your fsids. ' +
                          'I\'m going to keep trying, but in the ' +
                          'meanwhile, could you check to see if they\'re '+
                          'properly formatted? An easy way to guarantee ' +
                          'this is to do the following command in stata:' +
                          ' gen FSID = regexs(0) if ' +
                          'regexm(YOUROLDFSID,"[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9]")'
                          'This extracts only the fsid from the column.')
                    print('\n\n\n\n', info.json())
                '''
                
                # Assign it to the dataframe.
                df['pids'].loc[df.pids == fsid] = newid
                
                # Get the end time.
                end = time()
                
                # Print the time total.
                tot = tot + (end-start)
                num += 1
                av = tot/num
                if num%25 == 1:
                    print('\nMinutes Left:', round(((len(allids)-num)*av)/60,2))
                
        
        # Fix the first and other nan.
        if header: 
            df.pids.iloc[0] = first
        
        if overwrite:
            # Write back to the sheet.
            df['pids_old'].loc[(df['pids'].notnull()) & (df['pids_old'] != df['pids'])] = df['pids']
            if google_sheet == True:
                self._google_write(sheet_list[i],f'{sheet_name}!{idcol}1:{idcol}{len(df.pids_old.values)}', text = list(df.pids_old.values))
            else:
                full_df[idcol - 1] = df['pids']
                if sheet_list[i][-3:]:
                    full_df.to_csv(sheet_list[i], header=False, index=False)
                else:
                    full_df.to_excel(sheet_list[i], header=False, index=False)
            
            print(str(len(allids) - len(bad_ids)) + " real changes made")
        
        if len(bad_ids) > 1:
            print(str(len(bad_ids)) + " fsids got no information and may have something wrong with them")
        
        if write_changed:
            newlist = list(new_ids)
            with open(self.outfile[:-4] + '.csv', 'w') as chg_out:
                chg_out.write('old_id,new_id\n')
                for i in range(len(idlist)):
                    try:
                        chg_out.write(idlist[i]+','+newlist[i]+'\n')
                    except:
                        chg_out.write(idlist[i]+','+''+'\n')
        return (bad_ids, allids)
            

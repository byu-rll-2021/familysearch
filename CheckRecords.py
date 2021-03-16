# -*- coding: utf-8 -*-
"""
Created on Thu May 31 12:52:19 2018

@author: bbranchf
"""

import pandas as pd
import sys
import re
import time
import requests

def CheckRecords(self, sheet, idcol, out_col, record_type='any', cen_year='', header=True, token=None):
    
    if re.match(r'http', sheet):
        sheet = re.search(r"(?<=spreadsheets/d/)(.+)(?=/edit)", sheet)[1]
    
    # Get an API token.
    if token is None:
        token = self.Authenticate()
    
    # Read the ids.
    try:
        df = pd.DataFrame(self._google_read(sheet,'Sheet1!{0}:{0}'.format(idcol.upper())), columns=['pids'])
    except:
        time.sleep(5)
        try:
            df = pd.DataFrame(self._google_read(sheet,'Sheet1!{0}:{0}'.format(idcol.upper())), columns=['pids'])
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise
    
    if record_type == 'census':
        hrefs = [record_type + cen_year + ' link']
    else:
        hrefs = [record_type + ' link']

    # Get a list of pids.
    df['pids'] = df['pids'].str.extract('([0-9A-Z]{4}-[0-9A-Z]{3}[0-9A-Z]*)', expand=False)
    idlist = df['pids'].fillna('')
    
    # Initialize total time.
    tot = 0.0
    num = 1
    
    in_line = True
    
    #Loop through each row of the infile
    for x in range(len(idlist)):
        
        #Give Helpful Errors if data is bad/account for common errors that aren't important to fix
        if idlist[x] == '':
            continue
        
        # Check if we have 200 and mark the start.
        if ids == '':
            ids = data.iat[x,1]
            your_infile_but_cooler[data.iat[x,1]] = data.iat[x,0]
        else:
            ids = ids + ',' + data.iat[x,1]
            your_infile_but_cooler[data.iat[x,1]] = data.iat[x,0]


        # Continue if we have a full array.
        if (((x + 1) % 200 == 0) or (x == row_count - 1 )) and x!= 0:
            # Reset the run variable.
            # Make the request to get the 200 people
            info = requests.get('http://api.familysearch.org/platform/tree/persons?pids=%s' %(ids), 
                               headers={'Authorization': 'Bearer %s' %(token), 'Accept':'application/json'})
            
            ##Try a lot to get the request to actually work
            for z in range(1000):
                if z == 5:
                    print('Having some problems finding your fsids. ' +
                          'I\'m going to keep trying, but in the ' +
                          'meanwhile, could you check to see if they\'re '+
                          'properly formatted? An easy way to guarentee ' +
                          'this is to do the following command in stata:' +
                          ' gen FSID = regexs(0) if ' +
                          'regexm(YOUROLDFSID,"[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9]")'
                          'This extracts only the fsid from the column.')
                try:
                    persons = info.json()['persons']
                    break
                except:
                    info = requests.get('http://api.familysearch.org/platform/tree/persons?pids=%s' %(ids), 
                                    headers={'Authorization': 'Bearer %s' %(token), 
                                             'Accept':'application/json'})
        try:
            entry_list = pull.json()['entries']
            count = 0
            for i in range(len(entry_list)):
                if re.search(regex, entry_list[i]['title']):
                    hrefs.append(entry_list[i]['links']['source-linker']['href'])
                    break
                count += 1
                if count == len(entry_list):
                    hrefs.append('')
        except:
            hrefs.append('')
        
        # Get the end time.
        end = time()
        
        # Print the time total.
        tot = tot + (end-start)
        num += 1
        av = tot/num
        if num % 200 == 1:
            print(str(len(hrefs)) + " of " + str(df.shape[0]))
            print('\nMinutes Left:', round(((len(idlist)-num)*av)/60,2))
    
        if len(hrefs) != num and in_line:
            print("Warning: The references may not be in line with the corresponding FSIDs")
            print("The first instance of them being off occured at line " + num)
            in_line = False
    
    # Fix the first and other nan.
    df = pd.DataFrame(hrefs).fillna('')
    df.columns = ['records']
        
    # Write back to the sheet.
    self._google_write(sheet,'Sheet1!{0}1:{0}{1}'.format(out_col.upper(), len(df.records.values)), text = list(df.records.values))
    
    
# -*- coding: utf-8 -*-
"""
Created on Wed May 30 14:28:05 2018

@author: bbranchf
"""

import sys

sys.path.append(r'R:\JoePriceResearch\Python\Anaconda3\Lib\site-packages')

import time
import pandas as pd
import re
import requests


def GetRecordHints(self, sheet, idcolstr, idcolint, out_col, record_type='any', cen_year='', header=True, google_sheet=True, token=None, delim=',', links=True):
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
    if re.match(r'http', sheet):
        sheet = re.search(r"(?<=spreadsheets/d/)(.+)(?=/edit)", sheet)[1]
    
    # Get an API token.
    if token is None:
        token = self.Authenticate()
    
    # Read the ids.
    if google_sheet:
        try:
            ids = pd.Series([x[0] for x in self._google_read(sheet,'Sheet1!{0}:{0}'.format(idcolstr.upper()))])
        except:
            time.sleep(5)
            try:
                ids = pd.Series([x[0] for x in self._google_read(sheet,'Sheet1!{0}:{0}'.format(idcolstr.upper()))])
            except:
                print("Unexpected error:", sys.exc_info()[0])
                raise            
    else:

        if sheet[-3:] == 'dta':
            full_df = pd.read_stata(sheet)
        else:
            full_df = pd.read_csv(sheet, header=0, sep=delim)
        # Read the ids.
        ids = full_df.iloc[:,idcolint]
    
    # assigning what to look for 
    if record_type == 'census':
        if cen_year != '':
            regex = '[Cc]ensus, ' + str(cen_year)
        else:
            regex = '[Cc]ensus'
    elif record_type == 'death':
        regex = '[Gg]rave|[Oo]bit|[Dd]eath|[Bb]urial'
    elif record_type == 'birth':
        regex = '[Bb]irth'
    elif record_type == 'marriage':
        regex = '[Mm]arriage|[Mm]arital|[Ww]edding'
    elif record_type == 'any':
        regex = ''
    else:
        record_type = input("\nThe record_type variable didn't match any of the possibilities" +
                            "\nplease input any, census, death, marriage or birth\n")
        if record_type == 'census':
            cen_year = input("\nWhich year would you like")
        self.GetRecordHints(sheet=sheet, idcolstr=idcolstr, idcolint=idcolint, out_col=out_col, record_type=record_type, cen_year=cen_year)
    
    # considering the presence of headers
    if google_sheet:
        if header and links:
            if record_type == 'census':
                records = [record_type + cen_year + ' link']
            else:
                records = [record_type + ' link']
        elif header and not links:
            records = ['record hint titles']
        else:
            records = []
    else:
        records = []
        
    # Get a list of pids.
    idlist = ids.str.extract('([0-9A-Z]{4}-[0-9A-Z]{3}[0-9A-Z]*)', expand=False).fillna('')
    
    # Initialize total time.
    tot = 0.0
    
    if header:
        num = 1
    else:
        num = 0
    
    in_line = True
    
    # establishing a connection
    with requests.Session() as s:
        # let them know who we are and what format to retrieve data
        s.headers.update({'Authorization': 'Bearer %s' %(token),
                          'Accept':'application/json'})

    
    for fsid in idlist:
        start = time.time()
        if fsid != '':
            pull = s.get(f'http://api.familysearch.org/platform/tree/persons/{fsid}/matches?collection=https://familysearch.org/platform/collections/records')
            if pull.status_code != 200:
                for i in range(3):
                    pull = s.get(f'http://api.familysearch.org/platform/tree/persons/{fsid}/matches?collection=https://familysearch.org/platform/collections/records')
                    if pull.status_code == 200:
                        break
                    elif i == 2:
                        print(f'no record hints retrieved for {fsid}')

            pers_recs = [fsid]
            try:
                entry_list = pull.json()['entries']
                for i in range(len(entry_list)): # ! BOTTLENECK ! : LOOPING over with thse checks will add lots of time
                    if record_type == 'any':
                        pers_recs.append(entry_list[i]['id']) # if something other and record title is desird change this line to have the path to that
                    elif re.search(regex, entry_list[i]['title']):
                        if links:
                            records.append(entry_list[i]['links']['source-linker']['href'])
                            break
                        else:
                            pers_recs.append(entry_list[i]['id']) 
                    if record_type!= 'any' and i == len(entry_list) - 1:
                        records.append('')
                        
            except Exception as e:
                print('\n\n There Has been an error \n')
                print(e)

            records.append(';'.join(pers_recs))
        else:
            records.append('')
            
        # Get the end time.
        end = time.time()
        
        # Print the time total.
        tot = tot + (end-start)
        num += 1
        av = tot/num
        if num % 50 == 0:
            print(str(len(records)) + " of " + str(ids.shape[0]))
            print('average time per person: ', round(av))
            print('Minutes Left:', round(((len(idlist)-num)*av)/60, 3), '\n')
        
        if in_line and len(records) != num:
            print("Warning: The references may not be in line with the corresponding FSIDs")
            print("The first instance of them being off occured at line " + str(num))
            in_line = False
    
    if google_sheet:
        # Fix the first and other nan
        df = pd.DataFrame(records, columns=['records']).fillna('')
            
        # Write back to the sheet
        self._google_write(sheet,'Sheet1!{0}1:{0}{1}'.format(out_col.upper(), len(df.records.values)), text = list(df.records.values))

    else:
        full_df['record_hints'] = pd.Series(records)
        full_df.to_csv(self.outfile, index=False, header=header)
        
        
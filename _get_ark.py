# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 16:21:06 2018

@author: cookchr2
"""


'''
This function was intended to be run right after running ScrapePerson
Though it could be used in other ways, you might have to tweak it to 
make it do what you want


'''

'''
Documentation for this function and Example code for use can be found at
R:\JoePriceResearch\Python\all_code\FamilySearch1\Documentation\_get_ark.txt
'''

import pandas as pd
import requests
import re
import time

def _remove_non_ascii_1(text):
    '''
    This function removes non ascii characters from a string.
    '''
    try:
        stuff = ''.join(i for i in text if ord(i)<128)
    except:
        stuff = ''
    return stuff



def _get_ark(self, input_token = 'BLANK', file_type='csv', merge=True):
    t0 = time.time()
    t1 = 0
    t2 = 0

    '''
    This function retrives all the ARKIDS and Source Descriptions for your
    Dataset, after a scrape
    '''
    print('Actually Running')
    
    # Read in Data
    if (file_type == 'stata') | (file_type == '.dta'):
        in_data = pd.read_stata(self.outfile[:-4] + '.csv')
    else:
        in_data = pd.read_csv(self.outfile[:-4] + '.csv')
    
    in_data = in_data.fillna('')
    
    # Get the row count.
    row_count = in_data.shape[0]
        
    #Make sure the user is actually putting in a token
    if input_token == 'BLANK':
        token = self.Authenticate()
    else:
        token = input_token
    
    #Declaring our reference objects
    reference = []
    descIDs = []
    row_output = {}
    
    ref_cache = []
    descIDs_cache = []
    
    #loop through each row in the dataframe
    for x in range(row_count):
        
        #Append/Add data to our list 
        descIDs += [descID for descID in in_data.at[x, 'sources'].split(';') if descID != '']
        fsid = in_data.at[x, 'FSID']
        uid = in_data.at[x, 'uid']
        descIDS_list = [descID for descID in in_data.at[x, 'sources'].split(';') if descID != '']
        reference = (x, descIDS_list, fsid, uid)

        ref_cache.append(reference)
        # Once the list is long enough query family search about our descIDs
        for ID in reference[1]:
            descIDs_cache.append(ID)
            if len(descIDs_cache) == 30:
                row_output = self.Ping_API(ref_cache, descIDs_cache, token, row_output)
                ref_cache = [ref_cache[-1]]
                descIDs_cache = []
                    
        if (x + 1) % 100 == 0:
            if t1 == 0:
                t1 = t0
            else:
                t1 = t2
            t2 = time.time()
            avg_time = (t2 - t0)/x 
            print('\nAvg Time: ' + str(round(avg_time, 3)) + ' Seconds/Person')
            print('Est. time remaining: ' + str(round(avg_time * (row_count - x) / 60, 2)) + ' minutes')


    row_output = self.Ping_API(ref_cache,descIDs_cache, token, row_output)

    #format data
    out_data = pd.DataFrame.from_dict(row_output, orient='index')
    
    #Rename Columns
    out_data.columns = ['arkids','Source_Titles','FSID','uid']
    
    # Make .dta compatible
    out_data = out_data.applymap(str)  
    in_data = in_data.applymap(str)

    if merge:
        # merge the data
        try:
            out_data = in_data.merge(out_data, on=['uid', 'FSID'], how='outer')
        except:
            out_data.to_csv(self.outfile[:-4] + '_ark.csv', index=False)
            print('The data did not merge properly but ' + 
                  'YOUROUTFILENAME_ark.csv should have all of the information')
    
    #save
    if (file_type == 'stata') | (file_type == '.dta'):
        out_data.to_stata(self.outfile[:-4] + '.dta', write_index=False, version=117)
    
    else:
        out_data.to_csv(self.outfile[:-4] + '.csv', index=False)

    t_full = time.time()
	
    print('Total Time: ' + str(round((t_full - t0),2)) + ' Seconds')
    print('Avg Time: ' + str(round((t_full - t0)/row_count,2)) + ' Seconds/Person')

    return pd.DataFrame.from_dict(row_output, orient='index')



def Ping_API(self,reference,descIDs, token, row_output):
    descIDs = ','.join(descIDs)
    failcnt = 0
    #Repeat until we get it right
    
    arkreq = requests.get('https://api.familysearch.org/platform/sources/descriptions?sdids=%s' %(descIDs), headers={'Authorization': 'Bearer %s' %(token), 'Accept':'application/json'})
    while(True):
        try:
            sourceDescriptions = arkreq.json()['sourceDescriptions']
            break
            if arkreq.status_code != 401:
                sourceDescriptions = arkreq.json()['persons']
                break
            else:
                token = self.Authenticate()
        except:
            descIDs = descIDs.replace(',,',',')
            descIDs = descIDs.replace(',,',',')
            descIDs = descIDs.replace(',,',',')                
            failcnt += 1
            if failcnt > 5:
                print('moving on; These Description IDs are being skipped: ')
                print('The status code was:', arkreq.status_code)
                print(descIDs)
                arkreq = ''
                sourceDescriptions = []
                break
            arkreq = requests.get('https://api.familysearch.org/platform/sources/descriptions?sdids=%s' %(descIDs), headers={'Authorization': 'Bearer %s' %(token), 'Accept':'application/json'})

    #Loop through each record we got back from FamilySearch
    for rec in sourceDescriptions:
        try:
            #Extract the ark, title and id of the source
            ark = _remove_non_ascii_1(re.search('[0-9A-Z]{4}-[0-9A-Z]{3}[0-9A-Z]?', rec['about']).group(0))
            title = _remove_non_ascii_1(rec['titles'][0]['value'])
            m = re.search('"(.+?)"', title)
            if m:
                title = m.group(1)

            idnum = rec['id']
            
            #Find the matching record from our reference list
            for ref in reference:
                if idnum in ref[1]:
                    #Grab the inputs we want in the outfile
                    ex = ref[0]
                    fsid = ref[2]
                    uid = ref[3]
                    #Make or add to a row in the output
                    if ex in row_output:
                        row_output[ex] = (row_output[ex][0] + '|' + ark, row_output[ex][1] + '|' + title,fsid, str(uid))
                    else:
                        row_output[ex] = (ark, title,fsid, str(uid))
        except AttributeError:
            pass
        except KeyError:
            pass
    return row_output


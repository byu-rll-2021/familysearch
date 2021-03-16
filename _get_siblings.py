# -*- coding: utf-8 -*-
"""
Created on Fri Mar  2 12:00:45 2018

@author: cookchr2
"""
import pandas as pd
import requests
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


def _get_siblings(self, input_token = 'BLANK'):
    '''
    This function retrives all the Sibling information for you
    Dataset, after a NONBASIC scrape
    '''
    
    #Read in Data
    try:
        in_data = pd.read_csv(self.outfile[:-4] + '.csv').fillna('')
    except:
        filename = input("I couldn't find your file. Please give the name with the file extension again")
        in_data = pd.read_csv(filename).fillna('')
    
    # Get the row count.
    row_count = in_data.shape[0]
    
    #Put in your own token manually Sorry!
    if input_token == 'BLANK':
        token = self.token
    else:
        token = input_token
    
    #Declaring our reference objects
    reference = []
    sibIDs = ''
    row_output = {}
    
    # making base time variables for progress report
    t0 = time.time()
    t1 = 0
    t2 = 0
    
    #loop through each row in the dataframe
    for x in range(row_count):
        #Append/Add data to our list 
        if sibIDs == '':
            sibIDs = in_data.at[x, 'sibling_FSIDs'].replace(';',',')
            uid = in_data.at[x, 'uid']
            sibIDs_list = in_data.at[x, 'sibling_FSIDs'].split(';')
        else:
            sibIDs += in_data.at[x, 'sibling_FSIDs'].replace(';',',')
            uid = in_data.at[x, 'uid']
            sibIDs_list = in_data.at[x, 'sibling_FSIDs'].split(';')
        reference.append((x,sibIDs_list,uid))
        
        #Once the list is long enough query family search about our descIDs
        if len(sibIDs) > 1600 or x + 1 == row_count :
            sibIDs = sibIDs[:-1]
            info = requests.get('http://api.familysearch.org/platform/tree/persons?pids=%s' %(sibIDs), headers={'Authorization': 'Bearer %s' %(token), 'Accept':'application/json'})
            
            failcnt = 0
            #Repeat until we get it right
            while(True):
                try:
                    if info.status_code != 401:
                        persons = info.json()['persons']
                        break
                    else:
                        token = self.Authenticate()
                except:
                    print('failing')
                    failcnt += 1
                    if failcnt > 5:
                        info = ''
                        break
                    info = requests.get('http://api.familysearch.org/platform/tree/persons?pids=%s' %(sibIDs), headers={'Authorization': 'Bearer %s' %(token), 'Accept':'application/json'})
            
            #Loop through each record we got back from FamilySearch
            for guy in persons:
                try:
                    FSID = _remove_non_ascii_1(guy['id'])
                except KeyError:
                    FSID = ''
                try:
                    name = _remove_non_ascii_1(guy['display']['name'])
                except KeyError:
                    name = ''
                try:
                    birthdate = _remove_non_ascii_1(guy['display']['birthDate'])
                except KeyError:
                    birthdate = ''
                try:
                    sex = _remove_non_ascii_1(guy['display']['gender'])
                except KeyError:
                    sex = ''
                #get birthplace
                try:
                	birthplace = _remove_non_ascii_1(guy['display']['birthPlace'])
                except KeyError:
                	birthplace = ''
                #get death date
                try:
                	deathdate = _remove_non_ascii_1(guy['display']['deathDate'])
                except KeyError:
                	deathdate = ''
                #get death place
                try:
                	deathplace = _remove_non_ascii_1(guy['display']['deathPlace'])
                except KeyError:
                	deathplace = ''
                #get burial date and place
                try:
                	burialdate = ''
                	burialplace = ''
                	for bur in guy['facts']:
                		if bur['type'] == 'http://gedcomx.org/Burial':
                			try:
                				burialdate = _remove_non_ascii_1(bur['date']['normalized'][0]['value'])
                			except KeyError:
                				burialdate = ''
                				
                			try:
                				burialplace = _remove_non_ascii_1(bur['place']['normalized'][0]['value'])
                			except KeyError:
                				burialplace = ''
                except KeyError:
                	burialdate = ''
                	burialplace = '' 
                
                #Find the matching record from our reference list
                for ref in reference:
                    if FSID in ref[1]:
                        #Grab the inputs we want in the outfile
                        ex = ref[0]
                        uid = ref[2]
                        #Make or add to a row in the output
                        if ex in row_output:
                            row_output[ex] = {'sibling_FSIDs' : row_output[ex]['sibling_FSIDs'] + ';' + FSID, \
                                      'sibling_names' : row_output[ex]['sibling_names'] + ';' + name , \
                                      'sibling_birthdates' : row_output[ex]['sibling_birthdates'] + ';' + birthdate, \
                                      'sibling_sexes' : row_output[ex]['sibling_sexes'] + ';' + sex, \
                                      'sibling_birthplaces' : row_output[ex]['sibling_birthplaces'] + ';' + birthplace, \
                                      'sibling_deathdates' : row_output[ex]['sibling_deathdates'] + ';' + deathdate, \
                                      'sibling_deathplaces' : row_output[ex]['sibling_deathplaces'] + ';' + deathplace, \
                                      'sibling_burialdates' : row_output[ex]['sibling_burialdates'] + ';' + burialdate, \
                                      'sibling_burialplaces' : row_output[ex]['sibling_burialplaces'] + ';' + burialplace, \
                                      'uid' : str(uid)}
                        else:
                            row_output[ex] = {'sibling_FSIDs' : FSID, \
                                      'sibling_names' : name, \
                                      'sibling_birthdates' : birthdate, \
                                      'sibling_sexes' : sex, \
                                      'sibling_birthplaces' : birthplace, \
                                      'sibling_deathdates' : deathdate, \
                                      'sibling_deathplaces' : deathplace, \
                                      'sibling_burialdates' : burialdate, \
                                      'sibling_burialplaces' : burialplace, \
                                      'uid' : str(uid)}
            # Clear out the old familysearch query
            reference = []
            sibIDs = ''
        
        if (x + 1) % 2000 == 0:
            if t1 == 0:
                t1 = t0
            else:
                t1 = t2
            t2 = time.time()
            avg_time = (t2 - t0)/x 
            print('Avg Time: ' + str(round(avg_time, 3)) + ' Seconds/Record')
            print('Est. time remaining: ' + str(round(avg_time * (row_count - x) / 60, 3)) + ' minutes')

    #format data
    out_data = pd.DataFrame.from_dict(row_output, orient='index')
    
    print(str(row_count) + ' total siblings scraped')
    
    # out_data.uid = out_data.uid.astype(int)
    
    #save
    try:
        pd.read_csv(self.outfile[:-4] + '.csv', header=0).merge(out_data, on='uid').to_csv(self.outfile[:-4] + '.csv', index=False, header=True)
    except Exception as e:
        print('The merge did not work correctly but the file should be saved' +
              ' as YOUROUTFLIENAME_sib_info.csv')
        print('this is apparently the reaosn why', e)
        out_data.to_csv(self.outfile[:-4] + '_sib.csv', index = False)
        
    t_full = time.time()
    
    print('Total Time: ' + str(round((t_full - t0),2)) + ' Seconds')
    print('Avg Time: ' + str(round((t_full - t0)/row_count,2)) + ' Seconds/Record')

    
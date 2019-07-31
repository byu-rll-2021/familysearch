# -*- coding: utf-8 -*-
"""
Created on Mon Jun 11 15:04:52 2018

This is a program that gathers data on the ascendency/descendency
charts of info to make google sheets for ways to coordinate family history
efforts by identifying required tasks that are relatively simple. The checks
are rather naive such as the maiden name is registered as false whenever it
does not exactly match the fathers name which may be missing or have a 
slightly different spelling.

@author: bbranchf
"""

import os
import time
import re

import pandas as pd
import requests


def DescendancySheet(self, start_id, token=None, relatives='ancestry', max_iter=20, small_batch=True, census=True):
    '''
    This function uses the descendancy/ancestry node of the
    familysearch api to get all fo the relatives FSIDs to be scraped.
    This gets four generations at once so it would appear to be a better
    way to get the inital data than scraping everyone iteratively
    A file with a unique identifier and the FSIDs of the family immediate
    ancestors/ descendants
    
    parameters
    ----------
    start_id (str) = the id to use as refernce and get the generations above 
                    and/or below them
                    
    key (str)      = this is the api key that may be passed in manually if the 
                    use does not want to use the object's key
                    
    relatives (str) = This is to declare wether to go up, down or both 
                    directions in the tree to get people
                    
    max_iter (int)  = The process will stop when no more people are on the line
                    or this number of iterations is reached. This should be 
                    approximately the number of generations away from the start
                    individual that will be grabbed
    
    '''
    
    # saving the orginal outfile name as we will change it in the function
    orig_out = self.outfile
    out_stub = self.outfile[:-4]
    
    # getting an API token if one was not already given
    if token is None:
        token = self.Authenticate()
    
    # initializing the list of ids to be added to
    fam_ids = []
    
    # getting ancestry info from familysearch
    if relatives == 'ancestry' or relatives == 'both':
        pull = requests.get(f'http://api.familysearch.org/platform/tree/ancestry?person={start_id}', 
                            headers={'Authorization': f'Bearer {token}', 
                                     'Accept':'application/json'})
        if pull.status_code == 410:
            print('The person that was requested has been deleted')
            raise KeyError
            
        for peep in pull.json()['persons']:
            if small_batch and 10 > int(re.sub('-S', '', peep['display']['ascendancyNumber'])):
                fam_ids.append(peep['id'])
            elif not small_batch:
                fam_ids.append(peep['id'])
                
        pd.DataFrame({'pid':fam_ids}).to_csv(self.infile[:-4] + '.csv', index=True, header=False)
        
    elif relatives == 'descendancy':
        with open(self.infile, 'w') as in_file:
            in_file.write(f'9026289,KWNM-H83\n283478652,{start_id}')
    # in the case of an invalid selection get a new input and try again
    else:
        relatives = input('\nThe option you selcted was invalid, please ' +
                          "choose 'ancestry', 'descendancy' or 'both'")
        self.DescendancySheet(start_id=start_id, token=token, relatives=relatives)

    # grabbing the FSIDs of the family members
    self.ScrapePerson(basic=False)
    
    for z in range(1, max_iter):
        # getting fsids of family members
        
        # getting the basic scrape data
        df = pd.read_csv(self.outfile, header=0)
        
        # reassigning the outfile for the scrape so there is no overwriting
        self.outfile = out_stub + f'{z}.csv'
        
        # caching ids as to not get any duplicates
        if z == 1:
            all_ids = set([x for x in df['FSID']])
        else:
            for x in [x for x in df['FSID']]:
                all_ids.add(x)
        
        # initalizing a list of ids not yet scraped
        new_ids = set()
        
        # looping through FSID columns and getting them all into a list
        cols_to_split = ['spouse_FSIDs', 'kid_FSIDs']
        for col in cols_to_split:
            ser = df[col].fillna('').str.split(';')
            for x in [y for y in ser if type(y) == list]:
                for y in [y for y in x if y != '']:
                    if y not in all_ids:
                        new_ids.add(y)

        # making the scrape infile
        scrape = pd.DataFrame({'pid' : list(new_ids)})
        scrape.to_csv(self.infile[:-4] + '.csv', index=True, header=False)
        
        #confirming that there are people to scrape
        if len(new_ids) > 0: 
            # getting the data on the family
            if len(new_ids) == 1: # ScrapePerson doesn't work with only one entry
                with open(self.infile, 'a') as in_file:
                    in_file.write('9026289,KWNM-H83')
            self.ScrapePerson(basic=False)
                
        else:
            break
    
    # reading and merging the files together into one
    master = pd.read_csv(orig_out, header=0)
    for y in range(1, z):
        temp = pd.read_csv(out_stub + f'{y}.csv')
        master = master.append(temp, ignore_index=True)
        # deleting the files after they are read in and appended
        os.remove(out_stub + f'{y}.csv')
    
    # making the uid unique again
    master['uid'] = master.index
    
    # resetting the outfile to the original    
    self.outfile = orig_out
    
    # writing the full dataframe to a file for the ark and record hint scrape
    master.to_csv(self.outfile, index=False, header=True)
    
    print('\nGeting attached Record Info')
    # getting the attached records
    self._get_ark()
    
    print('\nGetting Record Hints')
    # getting record hints
    self.GetRecordHints(sheet=self.outfile, idcol=1, out_col=20,
                        header=True, google_sheet=False, links=False)
    
    print('\nGetting possible duplicates')
    # getting possible duplicates
    self.GetDups(file=self.outfile, header=True)
    
    self.MakeSheet(start_id=start_id, census=census)
    

def _grab_fsids(self, scraped_info, to_scrape, parents = False):
    # getting the basic scrape data
    df = pd.read_csv(scraped_info, header=0)
    
    # initializing a cache of FSIDs for a second scrape
    all_ids = set([x for x in df['FSID']])
    
    # looping through FSID columns and getting them all into a list
    if parents:
        cols_to_split = ['spouse_FSIDs', 'kid_FSIDs', 'dad_FSIDs', 'mom_FSIDs']
    else:
        cols_to_split = ['spouse_FSIDs', 'kid_FSIDs']
    for col in cols_to_split:
            ser = df[col].str.split(';')
            for x in [y for y in ser if type(y) == list]:
                for y in [y for y in x if y != '']:  
                    all_ids.add(y)

    # making the scrape infile
    scrape = pd.DataFrame({'pid' : list(all_ids)})
    scrape.to_csv(to_scrape, index=True, header=False)    
    
    # reassigning the infile to be scraped
    self.infile = self.infile[:-4] + f'{x}.csv'
    
    
def GetDups(self, file, header=True, col='FSID', token=None):
    '''
    get possible duplicates from the API
    '''
    
    # Initialize total time.
    tot = 0.0
    
    # storing the inital data
    orig = pd.read_csv(file, header=0)
    
    to_check = [x for x in orig[col]]
    poss_dups = []
    num = 0
    for pid in to_check:
        start = time.time()
        
        # initialize a list of possible duplicates for the id
        temp_dups = []
        for i in range(5):
            pull = requests.get(f'http://api.familysearch.org/platform/tree/persons/{pid}/matches', 
                                headers={'Authorization': f'Bearer {token}', 
                                         'Accept':'application/json'})
            if pull.status_code == 200:
                for entry in pull.json()['entries']:
                    temp_dups.append(entry['id'])
                break
            elif pull.status_code == 204:
                break
            elif pull.status_code == 401:
                token = self.Authenticate()
                i -= 1
        if pull.status_code != 200:
            poss_dups.append('')
        else:
            poss_dups.append(','.join(temp_dups))
        
        # Get the end time.
        end = time.time()
        
        # Print the time total.
        tot = tot + (end-start)
        num += 1
        av = tot/num
        if num % 25 == 0:
            print(str(num) + " of " + str(len(to_check)))
            print('Minutes Left:', round(((len(to_check)-num)*av)/60, 2))
    
    orig['poss_dups'] = poss_dups
    orig.to_csv(file, index=False, header=header)
    
    
def MakeSheet(self, start_id, census=True):
    '''
    turning the scraped data into the final product
    '''
    
    df = pd.read_csv(self.outfile, header=0).fillna('')
    
    # removing the extra ID that may have been added do the scrape would run
    df = df[df.FSID != 'KWNM-H83']
    
    # grabbing birth and death year from dates
    df['birthyear'] = df['pr_birthdate'].str.extract('([0-9]{4})', expand=False).fillna('')
    df['deathyear'] = df['pr_deathdate'].str.extract('([0-9]{4})', expand=False).fillna('')
    
    # making the lifespan variable
    df['lifespan'] = df['birthyear'].str.cat(df['deathyear'], na_rep='', sep='-')
    df['lifespan'] = df['lifespan'].str.replace('^-$', '')
    
    # making years numeric values
    df['birthyear'] = pd.to_numeric(df['birthyear'])
    df['deathyear'] = pd.to_numeric(df['deathyear'])
    
    if census:
        # checking for relevant censuses
        census_years = [1850, 1860, 1870, 1880, 1900, 1910, 1920, 1930, 1940]
        cen_to_get = []
        
        for lifespan in df['lifespan']:
            if re.search(r'[0-9]{4}-[0-9]{4}', lifespan):
                temp = []
                for yr in census_years:
                    if yr > int(re.search(r'([0-9]{4})', lifespan)[1]) and yr < int(re.search(r'-([0-9]{4})', lifespan)[1]):
                        temp.append(str(yr))
                cen_to_get.append(';'.join(temp))
            else:
                cen_to_get.append('')
        df['Census Records Needed'] = cen_to_get
    
    # getting last names for maiden name checks
    df['surname'] = [x[-1] for x in df['pr_name'].str.split(' ')]
    df['dad_surname'] = [x[-1] for x in df['dad_names'].str.split(' ')]
    
    # making final maiden name 
    df['maiden_name'] = df['surname'] == df['dad_surname']
    df['maiden_name'] = ['NA' if df.loc[x,'pr_sex'] != 'Female' else 'Complete' if df.loc[x,'maiden_name'] else 'Needed' for x in df.index]
    
    # making presence of mother or father on tree a boolean
    df['mother'] = df['mom_FSIDs'].str.match('[A-Z0-9]{4}-[A-Z0-9]{3}[A-Z0-9]*')
    df['father'] = df['dad_FSIDs'].str.match('[A-Z0-9]{4}-[A-Z0-9]{3}[A-Z0-9]*')
    
    # checking for day month year format of birthdate
    df['full_birthdate'] = df.pr_birthdate.str.match('^[0-9]+ \w+ [0-9]{4}$')
    
    # making possible duplicates 
    df['poss_dups'] = df['poss_dups'].str.match('[A-Z0-9]{4}-[A-Z0-9]{3,}')
    
    # making death info a boolean
    df['deathyear'] = df['pr_deathdate'].str.contains('[0-9]{4}').fillna(False)
    
    # making a married boolean
    df['married'] = df['spouse_FSIDs'].str.match('\w').fillna(False)
    
    # checking for different record types
    df['birth_record'] = df['Source_Titles'].str.contains('[Bb]irth')
    df['death_record'] = df['Source_Titles'].str.contains('[Dd]eath|[Oo]bit|[Gg]rave')
    df['marriage_record'] = df['Source_Titles'].str.contains('[Mm]arr|[Ww]edding')
    
    # checking for record hints
    #df['record_hints']
    
    # making the columns outfile format
    df['marriage_record'] = ['No Spouse' if not df.loc[x,'married'] else 'Complete' if df.loc[x,'marriage_record'] else 'Needed' for x in df.index]
    for col_name in ['birth_record', 'death_record', 'full_birthdate', 'mother', 'father', 'deathyear']:#, 'record_hints']:
        df[col_name] = ['Complete' if df.loc[x, col_name] else 'Needed' for x in df.index]
        
    for col_name in ['poss_dups', 'record_hints']:
        df[col_name] = ['Yes' if df.loc[x, col_name] else '' for x in df.index]
    
    # making a column with links to the persons familysearch profile
    df['Profile Link'] = 'https://www.familysearch.org/tree/person/details/' + df['FSID']
    
    # dropping extra information and ordering columns
    df = df.reindex(['FSID', 'pr_name', 'lifespan', 'full_birthdate', \
                     'maiden_name', 'mother', 'father', \
                     'deathyear', 'birth_record', \
                     'death_record', 'marriage_record', \
                     'record_hints', 'poss_dups', \
                     'Census Records Needed'], axis='columns')
    
    # cleaning up the names
    df = df.rename(index=str, columns={'pr_name' : 'Name', \
                   'lifespan' : 'Lifespan', 'full_birthdate' : 'Full Birthdate', \
                   'maiden_name' : 'Maiden Name', 'mother' : 'Mother', \
                   'father' : 'Father', 'poss_dups' : 'Possible Duplicates', \
                   'deathyear' : 'Death Date', 'birth_record' : 'Birth Record',\
                   'death_record' : 'Death Record', \
                   'marriage_record' : 'Marriage Record', \
                   'record_hints' : 'Record Hints'})
    
    # writing the final product
    df.to_csv('descendancy_sheet_' + start_id + '.csv', index=False, header=True)

    
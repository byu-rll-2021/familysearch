# -*- coding: utf-8 -*-
"""
Created on Fri Oct 27 17:18:33 2017

@author: tannerse & cookchr2 & bbranchf
"""
###############################################################################
######## YOUR PROVIDED INDEX MUST UNIQUELY IDENTIFY OBSERVATIONS ##############
#### The code merges using this id and it will break if it isn't unique #######
###############################################################################

'''
Recommended Batch Sizes: 
    Basic = True:
        in theory there is no cap, the outfile is only opened for appending in 
        this case so the file size shouldn't slow down the program at all. Of
        course, this is theoretical and there has not been extensive testing 
        with large files as of yet. 
    Basic = False:
        This one makes two different files and merges them at the end. This 
        will take longer the bigger the infiles are but if you split it up
        then you will likely need to concatenate the files when the merge is
        finished anyways so the time/hassle tradeoff is something you need to
        consider for your project. If the infile has less than 200,000 FSIDs
        you will likely be best off doing it all in one. 
    fam_death:
        This option shouldn't change the time it takes significantly as it does
        not involve an extra API call we just don't need all of the information
        sometimes so I figured I would add the option to not get it
'''

'''
Documentation, including example code for this function can be found at
R:\JoePriceResearch\Python\all_code\FamilySearch1\Documentation\ScrapePerson.txt
'''

import pandas as pd
import numpy as np
import requests
import re
import time
import os
import json

max_people = 200

def ScrapePerson(self, basic=True, fam_death=True,
                 file_type='.csv', sibs=False, DataFrame=None): 
    '''
    Scrapes the person information from the familysearch API.
    
    Parameters
    ----------
    basic (bool) =  True:
                    gets life events of person and fsids of parents, spouses
                    and children
                    False:
                    gets everything in basic plus names, birthdates, and sexes
                    of spouses, parents and children
    
    fam_death (bool) =  True: get info beyond birthdate and place (default)
                        False: only get birth info for parents
            
    input_key (string) = the authentication key that you would like to use for 
                            the API calls to family search. The FamilySearch
                            object that must be initialized before using this
                            will have one that will be used by default if 
                            no argument is given
                            
    file_type (string) = the way you would like the file to be saved. takes 
                         'stata', '.dta' or anything else will just give you
                         a csv
                         
    sibs (bool) = Whether or not to get sibling information beyond FSID
    '''
    
    print('Actually Running')
    t0 = time.time()
    t1 = 0
    t2 = 0
    
    n_fam = 0

    new_files = True
    """
    try:
        max1 = pd.read_csv(self.outfile[:-4] + '.csv').shape[0]
        if not basic:
            max2 = pd.read_csv(self.outfile[:-4] + '_fam_info.csv').shape[0]
        else:
            max2 = 0
        data = pd.read_csv(self.infile, header=None)[[0,1]]
        data = data.iloc[min(max1, max2):data.shape[0], :]
        new_files = False
        
    except FileNotFoundError:
        new_files = True
        data = pd.read_csv(self.infile, header=None)[[0,1]].dropna()
    except pd.errors.EmptyDataError:
        new_files = True
        data = pd.read_csv(self.infile, header=None)[[0,1]].dropna()
    except:
        raise
    """
    if DataFrame is None:
        # Read the file and remove any missing fsids.
        data = pd.read_csv(self.infile, header=None)[[0,1]].dropna()
    else:
        data = DataFrame.apply(str)
    
    # Get the row count.
    row_count = data.shape[0]
    
    # Define the id list.
    ids = ''

    #Need to make this because order isn't preserved
    your_infile_but_cooler = {}
    stata_out = []
    
    #prepping for non-basic data:
    if (not basic):
        followupFSIDs = set()
        reference = []
        cache_followupFSIDs = []
        cache_reference = []
        
    if new_files:    
        with open(self.outfile[:-4] + '.csv', 'w') as basic_info:
            basic_info.write('FSID,uid,pr_name,pr_birthdate,pr_sex,pr_birthplace,'+
                             'pr_deathdate,pr_deathplace,pr_burialdate,' +
                             'pr_burialplace,spouse_FSID,marriages,marriageplaces'+
                             ',kid_FSIDs,dad_FSIDs,mom_FSIDs,sources\n')
        
        if not basic:
            with open(self.outfile[:-4] + '_fam_info.csv', 'w') as fam_info:
                if fam_death:
                    fam_info.write('uid,spouse_name,spouse_birthdate,spouse_birthplaces,' +
                                   'spouse_FSID,dad_FSIDs,mom_FSIDs,kid_FSIDs,' +
                                   'spouse_deathdates,spouse_deathplaces,' +
                                   'spouse_burialdates,spouse_burialplaces,dad_names,' +
                                   'dad_birthdates,dad_birthplaces,dad_deathdates,' +
                                   'dad_deathplaces,dad_burialdates,dad_burialplaces,' +
                                   'mom_names,mom_birthdates,mom_birthplaces,' +
                                   'mom_deathdates,mom_deathplaces,mom_burialdates,' +
                                   'mom_burialplaces,sibling_names,sibling_FSIDs,' +
                                   'sibling_birthdates,sibling_sexes,kid_names,' +
                                   'kid_sexes,kid_birthdates,kid_birthplaces,'+
                                   'kid_deathdates, kid_deathplaces,' +
                                   'kid_burialdates, kid_burialplaces\n')
                elif not fam_death:
                    fam_info.write('uid,spouse_name,dad_names,dad_birthdates,' +
                                   'mom_names,mom_birthdates,sibling_names,' +
                                   'sibling_FSIDs,sibling_birthdates,sibling_sexes,' +
                                   'kid_names,kid_birthdates,kid_sexes')
            
    # opening the files to be written
    with open(self.outfile[:-4] + '.csv', 'a') as basic_info, open(self.outfile[:-4] + '_fam_info.csv', 'a') as fam_info:
        with requests.Session() as session:
            
            session.headers.update({'Authorization': 'Bearer %s' %(self.token),
                                    'Accept':'application/json'})
            
            #Loop through each row of the infile
            for x in range(row_count):
                
                #Give Helpful Errors if data is bad/account for common errors that aren't important to fix
                if data.iat[x,1] == '':
                    continue
                
                # Check if we have max_people and mark the start.
                if ids == '':
                    ids = data.iat[x,1]
                    if data.iat[x,1] in your_infile_but_cooler:
                        your_infile_but_cooler[data.iat[x,1]].append(data.iat[x,0])
                    else:
                        your_infile_but_cooler[data.iat[x,1]] = [data.iat[x,0]]
                else:
                    ids = ids + ',' + data.iat[x,1]
                    if data.iat[x,1] in your_infile_but_cooler:
                        your_infile_but_cooler[data.iat[x,1]].append(data.iat[x,0])
                    else:
                        your_infile_but_cooler[data.iat[x,1]] = [data.iat[x,0]]
                        
        
                # Continue if we have a full array.
                if (((x + 1) % max_people == 0) or (x == row_count - 1 )) and x!= 0:
                    # Reset the run variable.
                    # Make the request to get the max_people people
                    info = session.get('http://api.familysearch.org/platform/tree/persons?pids=%s' %(ids))
                    
                    #print(info.status_code)
                    # good response
                    
                    ##Try a lot to get the request to actually work
                    for z in range(15):
                        if z == 5:
                            print(info.status_code)
                            print('Bad IDS:\n', ids)
                            print('\nHaving some problems finding your fsids. ' +
                                  'I\'m going to keep trying, but in the ' +
                                  'meanwhile, could you check to see if they\'re '+
                                  'properly formatted? An easy way to guarentee ' +
                                  'this is to do the following command in stata:' +
                                  ' gen FSID = regexs(0) if ' +
                                  'regexm(YOUROLDFSID,"[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9]")'
                                  'This extracts only the fsid from the column.')
                        elif z == 14:
                            print('The given ID\'s caused some issues we couldn\'t ' +
                                  'fix for you so you will need to look over them ' +
                                  'for any issues and try again')
                            raise KeyError
                        try:
                            persons = info.json()['persons']
                            break
                        except:
                            if info.status_code == 401:
                                self.token = self.Authenticate()
                                info = session.get('http://api.familysearch.org/platform/tree/persons?pids=%s' %(ids))
                                continue
                            time.sleep(2)
                            info = session.get('http://api.familysearch.org/platform/tree/persons?pids=%s' %(ids), 
                                            headers={'Authorization': 'Bearer %s' %(self.token), 
                                                     'Accept':'application/json'})
                        
                    
                    #Loop through each person (guy) in the json we got back from FamilySearch
                    for guy in persons:
                        
                        #Initialize everything for a non-basic scrape
                        if(not basic):
                            kids_ = []
                            spouses_ = []
                            moms_ = []
                            dads_ = []
                            siblings_ = []
                            ind_= []
                            relationships = {'kids': kids_ , 'spouses': spouses_, 'moms': moms_ , 'dads': dads_, 'siblings' : siblings_, 'uid' : ind_}
                        
                        #Get fsid
                        try:
                            fsid = _remove_non_ascii_1(guy['id'])
                        except KeyError:
                            fsid = ''
                        #store fsid
                        if not basic:
                            ind_ = your_infile_but_cooler[fsid]
                            relationships['uid'] = your_infile_but_cooler[fsid]
                        #get name
                        try:
                            name = _remove_non_ascii_1(guy['display']['name'])
                        except KeyError:
                            name = ''
                        #get birthdate
                        try:
                            birth = _remove_non_ascii_1(guy['display']['birthDate'])
                        except KeyError:
                            birth = ''
                        #get gender
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
                            death = _remove_non_ascii_1(guy['display']['deathDate'])
                        except KeyError:
                            death = ''
                        #get death place
                        try:
                            deathplace = _remove_non_ascii_1(guy['display']['deathPlace'])
                        except KeyError:
                            deathplace = ''
                        #get burial date and place
                        try:
                            burial = ''
                            burialplace = ''
                            for bur in guy['facts']:
                                if bur['type'] == 'http://gedcomx.org/Burial':
                                    try:
                                        burial = _remove_non_ascii_1(bur['date']['normalized'][0]['value'])
                                    except KeyError:
                                        burial = ''
                                        
                                    try:
                                        burialplace = _remove_non_ascii_1(bur['place']['normalized'][0]['value'])
                                    except KeyError:
                                        burialplace = ''
                        except KeyError:
                            burial = ''
                            burialplace = ''        
                            
                        
                        #initialize the next round of stuff we're going to grab
                        marriages = ''
                        marplace = ''
                        spouseid = ''
                        
                        #Loop through each relationship in the json
                        try:
                            for marriage in info.json()['relationships']:
                                place = 1
                        except KeyError:
                            return info.json() 
                        for marriage in info.json()['relationships']:
                            try:
                                #If it's actually a couple relationship, and it matches the FSID of the person we're on, grab the marriage
                                if marriage['type'] == 'http://gedcomx.org/Couple':
                                    if (marriage['person1']['resourceId'] == fsid or marriage['person2']['resourceId'] == fsid): #and marriage['facts'][0]['type'] == 'http://gedcomx.org/Marriage':
                                        isthere = False
                                        #Grab spouse
                                        try:
                                            
                                            if marriage['person1']['resourceId'] == fsid:
                                                spouseid = _remove_non_ascii_1(spouseid + marriage['person2']['resourceId'] + ';')
                                                isthere = True
                                                if(not basic):
                                                    relationships['spouses'].append(marriage['person2']['resourceId'])
                                                    followupFSIDs.add(marriage['person2']['resourceId'])
                                                    #Scrape spouse for non-basic scrape
                                                    if(len(followupFSIDs) == max_people): #Prep a batch if full
                                                        cache_followupFSIDs.append(followupFSIDs)
                                                        for i in relationships['uid']:
                                                            real = dict(relationships)
                                                            real['uid'] = i
                                                            reference.append(real)
                                                        followupFSIDs = set()
                                                        relationships = {'kids': kids_ , 'spouses': spouses_, 'moms': moms_ , 'dads': dads_, 'siblings' : siblings_, 'uid' : ind_}
                                                        cache_reference.append(reference)
                                                        reference = []
                                                    
                                            else:
                                                spouseid = _remove_non_ascii_1(spouseid + marriage['person1']['resourceId'] + ';')
                                                isthere = True
                                                if(not basic):
                                                    relationships['spouses'].append(marriage['person1']['resourceId'])
                                                    followupFSIDs.add(marriage['person1']['resourceId'])
                                                    #scrape spouse for non-basic scrape
                                                    if(len(followupFSIDs) == max_people): #Prep a batch if full
                                                        cache_followupFSIDs.append(followupFSIDs)
                                                        for i in relationships['uid']:
                                                            real = dict(relationships)
                                                            real['uid'] = i
                                                            reference.append(real)
                                                        followupFSIDs = set()
                                                        relationships = {'kids': kids_ , 'spouses': spouses_, 'moms': moms_ , 'dads': dads_, 'siblings' : siblings_, 'uid' : ind_}
                                                        cache_reference.append(reference)
                                                        reference = []
                                                    
                                                    
                                        except (KeyError, IndexError):
                                            pass
    
                                        
                                        
                                        #grab marriage date
                                        try:
                                            marriages = marriages + _remove_non_ascii_1(marriage['facts'][0]['date']['normalized'][0]['value']) + ';'
                                        except (KeyError, IndexError):
                                            if isthere:
                                                marriages = marriages + ';'
                                                
                                        
                                        #grab marriage place
                                        try:
                                            marplace = marplace + _remove_non_ascii_1(marriage['facts'][0]['place']['normalized'][0]['value']) + ';'
                                        except (KeyError, IndexError):
                                            if isthere:
                                                marplace = marplace + ';'
                                        
                            except (KeyError, IndexError): #I know this seems redundant. It's for the if condition. 
                                pass
        
                        
                        if len(marriages) > 0:
                            marriages = marriages[:-1] #removing last semicolon
                        if len(marplace) > 0:
                            marplace = marplace[:-1] #again...
                        if len(spouseid) > 0:
                            spouseid = spouseid[:-1] #just removing the last semicolon
                        
                        #Initialize kid variables
                        kidids = ''
                        kidlist = []
                        try:
                            #Loop through each family our person is a part of
                            for fam in guy['display']['familiesAsParent']:
                                #Loop through kids in that family
                                for child in fam['children']:
                                    #if we don't already have the kid, add them
                                    if (child['resourceId']) not in kidlist:
                                        kidids = _remove_non_ascii_1(kidids + child['resourceId'] + ';')
                                        kidlist.append(child['resourceId'])
                                        #Scrape kid for non-basic scrape
                                        if(not basic):
                                            relationships['kids'].append(child['resourceId'])
                                            followupFSIDs.add(child['resourceId'])
                                            if(len(followupFSIDs) == max_people): #Prep a batch if full
                                                cache_followupFSIDs.append(followupFSIDs)
                                                for i in relationships['uid']:
                                                    real = dict(relationships)
                                                    real['uid'] = i
                                                    reference.append(real)
                                                followupFSIDs = set()
                                                relationships = {'kids': kids_ , 'spouses': spouses_, 'moms': moms_ , 'dads': dads_, 'siblings' : siblings_, 'uid' : ind_}
                                                cache_reference.append(reference)
                                                reference = []
                                #Get spouses we don't have a marraige for
                                try:
                                    if _remove_non_ascii_1(fam['parent1']['resourceId']) not in spouseid and _remove_non_ascii_1(fam['parent1']['resourceId']) != fsid:
                                        if spouseid == '':
                                            spouseid = _remove_non_ascii_1(fam['parent1']['resourceId'])
                                        else:
                                            spouseid = spouseid + ';' + _remove_non_ascii_1(fam['parent1']['resourceId'])
                                            marplace = marplace + ';'
                                            marriages = marriages + ';'
                                            if(not basic):
                                                relationships['spouses'].append(_remove_non_ascii_1(fam['parent1']['resourceId']))
                                                followupFSIDs.add(_remove_non_ascii_1(fam['parent1']['resourceId']))
                                                if(len(followupFSIDs) == max_people): #Prep a batch if full
                                                    cache_followupFSIDs.append(followupFSIDs)
                                                    for i in relationships['uid']:
                                                        real = dict(relationships)
                                                        real['uid'] = i
                                                        reference.append(real)
                                                    followupFSIDs = set()
                                                    relationships = {'kids': kids_ , 'spouses': spouses_, 'moms': moms_ , 'dads': dads_, 'siblings' : siblings_, 'uid' : ind_}
                                                    cache_reference.append(reference)
                                                    reference = []
                                                    
                                    elif _remove_non_ascii_1(fam['parent2']['resourceId']) not in spouseid and _remove_non_ascii_1(fam['parent2']['resourceId']) != fsid:
                                        if spouseid == '':
                                            spouseid = _remove_non_ascii_1(fam['parent1']['resourceId'])
                                        else:
                                            spouseid = spouseid + ';' + _remove_non_ascii_1(fam['parent1']['resourceId'])
                                            marplace = marplace + ';'
                                            marriages = marriages + ';'
                                            if(not basic):
                                                relationships['spouses'].append(_remove_non_ascii_1(fam['parent1']['resourceId']))
                                                followupFSIDs.add(_remove_non_ascii_1(fam['parent1']['resourceId']))
                                                if(len(followupFSIDs) == max_people): #Prep a batch if full
                                                    cache_followupFSIDs.append(followupFSIDs)
                                                    for i in relationships['uid']:
                                                        real = dict(relationships)
                                                        real['uid'] = i
                                                        reference.append(real)
                                                    followupFSIDs = set()
                                                    relationships = {'kids': kids_ , 'spouses': spouses_, 'moms': moms_ , 'dads': dads_, 'siblings' : siblings_, 'uid' : ind_}
                                                    cache_reference.append(reference)
                                                    reference = []
                                except KeyError:
                                    pass
                        except KeyError:
                            pass
                        
                        #removing trailing semicolon
                        if len(kidids) > 0:
                            kidids = kidids[:-1]
                        
                        #get dad fsid
                        dadsid = ''
                        try:
                            #loop through each family our fsid is a part of
                            for fam in guy['display']['familiesAsChild']:
                                try:
                                    #get dad
                                    dadsid = _remove_non_ascii_1(dadsid + fam['parent1']['resourceId'] + ';')
                                    #scrape dad if not basic
                                    if(not basic):
                                        relationships['dads'].append(fam['parent1']['resourceId'])
                                        followupFSIDs.add(fam['parent1']['resourceId'])
                                        if(len(followupFSIDs) == max_people): #Prep a batch if full
                                            cache_followupFSIDs.append(followupFSIDs)
                                            for i in relationships['uid']:
                                                real = dict(relationships)
                                                real['uid'] = i
                                                reference.append(real)
                                            followupFSIDs = set()
                                            relationships = {'kids': kids_ , 'spouses': spouses_, 'moms': moms_ , 'dads': dads_, 'siblings' : siblings_, 'uid' : ind_}
                                            cache_reference.append(reference)
                                            reference = []
                                        
                                        
                                except KeyError:
                                    pass
                        except KeyError:
                            pass
                        
                        #clean dad variable
                        if len(dadsid) > 0:
                            dadsid = dadsid[:-1]
                            
                        #get mom fsid
                        momsid = ''
                        try:
                            #loop through each family our fsid is a part of
                            for fam in guy['display']['familiesAsChild']:
                                try:
                                    
                                    momsid = _remove_non_ascii_1(momsid + fam['parent2']['resourceId'] + ';') #FYI I've checked, and the mom is always parent2, even when there's no dad
                                    #scrape mom if not basic
                                    if(not basic):
                                        relationships['moms'].append(fam['parent2']['resourceId'])
                                        followupFSIDs.add(fam['parent2']['resourceId'])
                                        if(len(followupFSIDs) == max_people): #Prep a batch if full
                                            cache_followupFSIDs.append(followupFSIDs)
                                            for i in relationships['uid']:
                                                real = dict(relationships)
                                                real['uid'] = i
                                                reference.append(real)
                                            followupFSIDs = set()
                                            relationships = {'kids': kids_ , 'spouses': spouses_, 'moms': moms_ , 'dads': dads_, 'siblings' : siblings_, 'uid' : ind_}
                                            cache_reference.append(reference)
                                            reference = []
                                        
                                except KeyError:
                                    pass
                        except KeyError:
                            pass
                        #clean mom
                        if len(momsid) > 0:
                            momsid = momsid[:-1]
        
                        #get description ids. For arkids you'll have to use _get_ark() afterwards
                        sources = []
                        try:
                            for source in guy['sources']:
                                sources.append(_remove_non_ascii_1(source['descriptionId'])) ##Sorry, but these are "Description Ids" NOT ARKIDS!!! But they can be used to get the arkid
                        except KeyError:
                            pass     
                        
                        #create output row
                        for ind in your_infile_but_cooler[fsid]:
                            a_row = [fsid, str(ind), re.sub(r'\,',r'',name), re.sub(r'\,',r'',birth), re.sub(r'\,',r'',sex),  \
                                re.sub(r'\,',r':',birthplace), re.sub(r'\,',r'',death), re.sub(r'\,',r':',deathplace), re.sub(r'\,',r'',burial), re.sub(r'\,',r':',burialplace),\
                                re.sub(r'\,',r'',spouseid), re.sub(r'\,',r'',marriages), re.sub(r'\,',r':',marplace), \
                                re.sub(r'\,',r'',kidids), re.sub(r'\,',r'',dadsid), \
                                re.sub(r'\,',r'',momsid), str(';'.join(sources))]
                            
                            # removed from the data to be input as it is redundant
                            # re.sub(r'\,',r'',spouse), re.sub(r'\,', r'',kids), 
                            # re.sub(r'\,',r'',kidbirths), re.sub(r'\,',r'',kidgenders), re.sub(r'\,',r'',dads), 
                            # re.sub(r'\,',r'',dadbirths), re.sub(r'\,',r'',moms),      
                            # re.sub(r'\,',r'',mombirths), re.sub(r'\,',r'',sibs), 
                            # re.sub(r'\,',r'',sibids), re.sub(r'\,',r'',sibbirths), re.sub(r'\,',r'',sibgenders), 
                            
                            #clean data
                            for row in a_row:
                                row = _remove_non_ascii_1(row)
            
                            #append to file
                            stata_out.append(a_row) 
                            
                        if not basic:
                            for i in relationships['uid']:
                                real = dict(relationships)
                                real['uid'] = i
                                reference.append(real)
                        
                    #Create out dataframe    
                    stata_out_pd = pd.DataFrame(stata_out, columns=['FSID', 'uid', 'pr_name', \
                        'pr_birthdate', 'pr_sex', 'pr_birthplace', 'pr_deathdate', 'pr_deathplace', 'pr_burialdate', 'pr_burialplace', \
                        'spouse_FSID', 'marriages', 'marriageplaces', 'kid_FSIDs', 'dad_FSIDs', 'mom_FSIDs', \
                        'sources'])
                    
                    stata_out_pd.to_csv(basic_info, index = False, header = False)
                    #Reinitialize stuff
                    ids = ''
                    your_infile_but_cooler = {}
                    stata_out = []
                    
                    #Running non-basic batches secondary scrape
                    if not basic:
                        for i in range(len(cache_reference)):
                            self.ScrapeFamily(cache_reference[i], self.outfile, cache_followupFSIDs[i], self.token, opened_file=fam_info, fam_death=fam_death, sibs=sibs)
                            n_fam += max_people
                        cache_followupFSIDs = []
                        cache_reference = []
                    
                    if (x + 1) % 600 == 0:
                        if t1 == 0:
                            t1 = t0
                        else:
                            t1 = t2
                        t2 = time.time()
                        avg_time = (t2 - t0)/x 
                        print('Avg Time: ' + str(round(avg_time, 3)) + ' Seconds/Record')
                        print('Est. time remaining: ' + str(round(avg_time * (row_count - x) / 60, 3)) + ' minutes')
            
        #complete whatever secondary batch remains uncompleted.        
        if not basic:
            self.ScrapeFamily(reference, self.outfile, followupFSIDs, self.token, opened_file=fam_info, fam_death=fam_death, sibs=sibs)
            n_fam += len(followupFSIDs)
            print(str(n_fam) + ' total family members scraped')

    if not basic:
        basic_info = pd.read_csv(self.outfile[:-4] + ".csv", header=0).applymap(str)
        fam_info = pd.read_csv(self.outfile[:-4] + '_fam_info.csv', header=0).sort_values(by='uid').reset_index(drop=True).applymap(str)
        
        # merging data for families that were in different API calls
        fam_info = _condense_faminfo(fam_info)
        
        # ^ sorting and resetting index so pandas doesn't throw a fit
#        try:
            # merging basic and familydata into a single dataset
        basic_info = basic_info.drop(['dad_FSIDs', 'mom_FSIDs', 'kid_FSIDs', 'spouse_FSID'], axis = 1)
        final_df = basic_info.merge(fam_info,
                                    on='uid', validate="1:1",
                                    how='outer').sort_values(by='uid').replace('nan','')
        if (file_type == 'stata') | (file_type == ".dta"):
            try:
                final_df.fillna('').to_stata(self.outfile[:-4] + '.dta', version=117)
            except:
                final_df.fillna('').to_csv(self.outfile[:-4] + '.csv',
                                index=False, header=True)
        else:
            final_df.fillna('').to_csv(self.outfile[:-4] + '.csv',
                            index=False, header=True)
            os.remove(self.outfile[:-4] + '_fam_info.csv') 
            
    
#        except:
#            print("Unexpected error:", sys.exc_info()[0])
#            print('The final datasets did not merge correctly your outfile ' +
#                  'name and "YOUROUTFILENAME_fam_info.csv" have all of the ' +
#                  'data but you will have to merge them yourself.')
            
            
    else:
        # deleting the fam_info file it creates by default
        try:
            os.remove(self.outfile[:-4] + '_fam_info.csv')
        except FileNotFoundError:
            pass
            
        if (file_type == 'stata') | (file_type == '.dta'):
            final_df = pd.read_csv(self.outfile[:-4] + '.csv', header = 0).sort_values(by='uid')
            try:
                final_df.to_stata(self.outfile[:-4] + '.dta', version=117)
                os.remove(self.outfile[:-4] + '.csv')
            except:
                print('Sorry, the python to_stata function isn\'t very good,' +
                      ' so the stata file didn\'t save. (Don\'t worry, it\'s' +
                      ' saved as a csv instead) Look for YOUROUTFILENAME.csv' +
                      ' in your directory, and then use (in stata) import ' +
                      'delimited YOURINFILENAME.csv, clear to load your data' +
                      ' into stata. Sorry about that!') 
        else:
            final_df = pd.read_csv(self.outfile[:-4] + '.csv', header = 0).sort_values(by='uid')

        
    t_full = time.time()
	
    print('Total Time: ' + str(round((t_full - t0),2)) + ' Seconds')
    print('Avg Time: ' + str(round((t_full - t0)/row_count,3)) + ' Seconds/Record')
    
    data.columns = ['ind', 'pid']
    
    if data.shape[0] - final_df.shape[0] > 1:
        print('There are ' + str(data.shape[0] - final_df.shape[0]) + ' observations that we couldn\'t scrape. These are probably deleted. Try running the deleted pid cleaner to fix this')
    if data.shape[0] - final_df.shape[0] == 1:
        print('There is ' + str(data.shape[0] - final_df.shape[0]) + ' observation that we couldn\'t scrape. It is probably deleted. Try running the deleted pid cleaner to fix this')
    
    if not basic:
        return final_df
    
def _condense_faminfo(fam_info):
    
    return_info = {}
    
    '''
    if fsid doesn't have semicolons but it isn't empty, replace the corresponding nan values with ''
        fam_info['spouse_name'] = fam_info.loc[(fam_info.spouse_FSID.str.contains(';') == False) & (fam_info.spouse_FSID.isnull() == False)]['spouse_name'].fillna('')

    '''
    
    fam_info = fam_info.fillna('')    
    
    for row in fam_info.iterrows():
        if row[1]['uid'] not in return_info:
            return_info[row[1]['uid']] = row[1]
        else:
            new_row = []
            for i, v in row[1].iteritems():
                if i != 'uid':
                    new_row.append(str(return_info[row[1]['uid']][i]) + ';' + str(v))
                else:
                    new_row.append(str(v))

            return_info[row[1]['uid']] = pd.Series(new_row, index = list(row[1].index))
            
    for key in return_info:
        if pd.isnull(return_info[key]['spouse_name']):
            spouse_names = ['']*3
        else:
            spouse_names = return_info[key]['spouse_name'].split(';')
            
        if pd.isnull(return_info[key]['spouse_FSID']):
            spouse_FSIDs = []
        else:
            spouse_FSIDs = return_info[key]['spouse_FSID'].split(';')
            
            
        if pd.isnull(return_info[key]['spouse_birthdate']):
            spouse_birthdates = ['']*3
        else:
            spouse_birthdates = return_info[key]['spouse_birthdate'].split(';')
            
        if pd.isnull(return_info[key]['spouse_birthplaces']):
            spouse_birthplaces = ['']*3
        else:
            spouse_birthplaces = return_info[key]['spouse_birthplaces'].split(';')
        if pd.isnull(return_info[key]['spouse_deathdates']):
            spouse_deathdates = ['']*3
        else:
            spouse_deathdates = return_info[key]['spouse_deathdates'].split(';')
        if pd.isnull(return_info[key]['spouse_deathplaces']):
            spouse_deathplaces = ['']*3
        else:
            spouse_deathplaces = return_info[key]['spouse_deathplaces'].split(';')
        if pd.isnull(return_info[key]['spouse_burialdates']):
            spouse_burialdates = ['']*3
        else:
            spouse_burialdates = return_info[key]['spouse_burialdates'].split(';')
        if pd.isnull(return_info[key]['spouse_burialplaces']):
            spouse_burialplaces = ['']*3
        else:
            spouse_burialplaces = return_info[key]['spouse_burialplaces'].split(';')
        if pd.isnull(return_info[key]['dad_names']):
            dad_names = ['']*3
        else:
            dad_names = return_info[key]['dad_names'].split(';')
        if pd.isnull(return_info[key]['dad_FSIDs']):
            dad_FSIDs = []
        else:
            dad_FSIDs = return_info[key]['dad_FSIDs'].split(';')
        if pd.isnull(return_info[key]['dad_birthdates']):
            dad_birthdates = ['']*3
        else:
            dad_birthdates = return_info[key]['dad_birthdates'].split(';')
        if pd.isnull(return_info[key]['dad_birthplaces']):
            dad_birthplaces = ['']*3
        else:
            dad_birthplaces = return_info[key]['dad_birthplaces'].split(';')
        if pd.isnull(return_info[key]['dad_deathdates']):
            dad_deathdates = ['']*3
        else:
            dad_deathdates = return_info[key]['dad_deathdates'].split(';')
        if pd.isnull(return_info[key]['dad_deathplaces']):
            dad_deathplaces = ['']*3
        else:
            dad_deathplaces = return_info[key]['dad_deathplaces'].split(';')
        if pd.isnull(return_info[key]['dad_burialdates']):
            dad_burialdates = ['']*3
        else:
            dad_burialdates = return_info[key]['dad_burialdates'].split(';')
        if pd.isnull(return_info[key]['dad_burialplaces']):
            dad_burialplaces = ['']*3
        else:
            dad_burialplaces = return_info[key]['dad_burialplaces'].split(';')
        if pd.isnull(return_info[key]['mom_names']):
            mom_names = ['']*3
        else:
            mom_names = return_info[key]['mom_names'].split(';')
        if pd.isnull(return_info[key]['mom_FSIDs']):
            mom_FSIDs = []
        else:
            mom_FSIDs = return_info[key]['mom_FSIDs'].split(';')
        if pd.isnull(return_info[key]['mom_birthdates']):
            mom_birthdates = ['']*3
        else:
            mom_birthdates = return_info[key]['mom_birthdates'].split(';')
        if pd.isnull(return_info[key]['mom_birthplaces']):
            mom_birthplaces = ['']*3
        else:
            mom_birthplaces = return_info[key]['mom_birthplaces'].split(';')
        
        if pd.isnull(return_info[key]['mom_deathdates']):
            mom_deathdates = ['']*3
        else:
            mom_deathdates = return_info[key]['mom_deathdates'].split(';')
        
        if pd.isnull(return_info[key]['mom_deathplaces']):
            mom_deathplaces  = ['']*3
        else:
            mom_deathplaces  = return_info[key]['mom_deathplaces'].split(';')
        
        if pd.isnull(return_info[key]['mom_burialdates']):
            mom_burialdates = ['']*3
        else:
            mom_burialdates = return_info[key]['mom_burialdates'].split(';')
        
        if pd.isnull(return_info[key]['mom_burialplaces']):
            mom_burialplaces = ['']*3
        else:
            mom_burialplaces = return_info[key]['mom_burialplaces'].split(';')
        
        if pd.isnull(return_info[key]['sibling_names']):
            sibling_names = ['']*3
        else:
            sibling_names = return_info[key]['sibling_names'].split(';')
        
        if pd.isnull(return_info[key]['sibling_FSIDs']):
            sibling_FSIDs = []
        else:
            sibling_FSIDs = return_info[key]['sibling_FSIDs'].split(';')
        
        if pd.isnull(return_info[key]['sibling_birthdates']):
            sibling_birthdates = ['']*3
        else:
            sibling_birthdates = return_info[key]['sibling_birthdates'].split(';')
        
        if pd.isnull(return_info[key]['sibling_sexes']):
            sibling_sexes = ['']*3
        else:
            sibling_sexes = return_info[key]['sibling_sexes'].split(';')
        
        if pd.isnull(return_info[key]['kid_names']):
            kid_names = ['']*3
        else:
            kid_names = return_info[key]['kid_names'].split(';')
        
        if pd.isnull(return_info[key]['kid_FSIDs']):
            kid_FSIDs = []
        else:
            kid_FSIDs = return_info[key]['kid_FSIDs'].split(';')
        
        if pd.isnull(return_info[key]['kid_birthdates']):
            kid_birthdates = ['']*3
        else:
            kid_birthdates = return_info[key]['kid_birthdates'].split(';')
        
        if pd.isnull(return_info[key]['kid_sexes']):
            kid_sexes = ['']*3
        else:
            kid_sexes = return_info[key]['kid_sexes'].split(';')
        
        if pd.isnull(return_info[key]['kid_birthplaces']):
            kid_birthplaces = ['']*3
        else:
            kid_birthplaces = return_info[key]['kid_birthplaces'].split(';')
        
        if pd.isnull(return_info[key]['kid_deathdates']):
            kid_deathdates = ['']*3
        else:
            kid_deathdates = return_info[key]['kid_deathdates'].split(';')
        
        if pd.isnull(return_info[key][' kid_deathplaces']):
            kid_deathplaces = ['']*3
        else:
            kid_deathplaces = return_info[key][' kid_deathplaces'].split(';')
        
        if pd.isnull(return_info[key]['kid_burialdates']):
            kid_burialdates = ['']*3
        else:
            kid_burialdates = return_info[key]['kid_burialdates'].split(';')
        
        if pd.isnull(return_info[key][' kid_burialplaces']):
            kid_burialplaces = ['']*3
        else:
            kid_burialplaces = return_info[key][' kid_burialplaces'].split(';')
        
        spouse_names_new = []
        spouse_FSIDs_new = []
        spouse_birthdates_new = []
        spouse_birthplaces_new = []
        spouse_deathdates_new = []
        spouse_deathplaces_new = []
        spouse_burialdates_new = []
        spouse_burialplaces_new = []
        dad_names_new = []
        dad_FSIDs_new = []
        dad_birthdates_new = []
        dad_birthplaces_new = []
        dad_deathdates_new = []
        dad_deathplaces_new = []
        dad_burialdates_new = []
        dad_burialplaces_new = []
        mom_names_new = []
        mom_FSIDs_new = []
        mom_birthdates_new = []
        mom_birthplaces_new = []
        mom_deathdates_new = []
        mom_deathplaces_new = []
        mom_burialdates_new = []
        mom_burialplaces_new = []
        sibling_names_new = []
        sibling_FSIDs_new = []
        sibling_birthdates_new = []
        sibling_sexes_new = []
        kid_names_new = []
        kid_FSIDs_new = []
        kid_birthdates_new = []
        kid_sexes_new = []
        kid_birthplaces_new = []
        kid_deathdates_new = []
        kid_deathplaces_new = []
        kid_burialdates_new = []
        kid_burialplaces_new = []
        
        for i, fsid in enumerate(spouse_FSIDs):
            if fsid not in spouse_FSIDs_new and fsid != '' and fsid != 'nan':
                spouse_FSIDs_new.append(fsid)
                spouse_birthdates_new.append(spouse_birthdates[i])
                spouse_birthplaces_new.append(spouse_birthplaces[i])
                spouse_deathdates_new.append(spouse_deathdates[i])
                spouse_deathplaces_new.append(spouse_deathplaces[i])
                spouse_burialdates_new.append(spouse_burialdates[i])
                spouse_burialplaces_new.append(spouse_burialplaces[i])
                spouse_names_new.append(spouse_names[i])
            else:
                for j, fsjd in enumerate(spouse_FSIDs_new):
                    if fsid == fsjd:
                        if spouse_birthdates_new[j] == '':
                            spouse_birthdates_new[j] = spouse_birthdates[i]
                        elif spouse_birthdates[i] != '' and spouse_birthdates[i] != spouse_birthdates_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 111')
                            
                        if spouse_birthplaces_new[j] == '':
                            spouse_birthplaces_new[j] = spouse_birthplaces[i]
                        elif spouse_birthplaces[i] != '' and spouse_birthplaces[i] != spouse_birthplaces_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 112')
                            
                        if spouse_deathdates_new[j] == '':
                            spouse_deathdates_new[j] = spouse_deathdates[i]
                        elif spouse_deathdates[i] != '' and spouse_deathdates[i] != spouse_deathdates_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 113')
                            
                        if spouse_deathplaces_new[j] == '':
                            spouse_deathplaces_new[j] = spouse_deathplaces[i]
                        elif spouse_deathplaces[i] != '' and spouse_deathplaces[i] != spouse_deathplaces_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 114')
                            
                        if spouse_burialdates_new[j] == '':
                            spouse_burialdates_new[j] = spouse_burialdates[i]
                        elif spouse_burialdates[i] != '' and spouse_burialdates[i] != spouse_burialdates_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 115')
                            
                        if spouse_burialplaces_new[j] == '':
                            spouse_burialplaces_new[j] = spouse_burialplaces[i]
                        elif spouse_burialplaces[i] != '' and spouse_burialplaces[i] != spouse_burialplaces_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 116')
                            
                        if spouse_names_new[j] == '':
                            spouse_names_new[j] = spouse_names[i]
                        elif spouse_names[i] != '' and spouse_names[i] != spouse_names_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 117')
        for i, fsid in enumerate(dad_FSIDs):
            if fsid not in dad_FSIDs_new and fsid != '' and fsid != 'nan':
                dad_FSIDs_new.append(fsid)
                dad_names_new.append(dad_names[i])
                dad_birthdates_new.append(dad_birthdates[i])
                dad_birthplaces_new.append(dad_birthplaces[i])
                dad_deathdates_new.append(dad_deathdates[i])
                dad_deathplaces_new.append(dad_deathplaces[i])
                dad_burialdates_new.append(dad_burialdates[i])
                dad_burialplaces_new.append(dad_burialplaces[i])
            else:
                for j, fsjd in enumerate(dad_FSIDs_new):
                    if fsid == fsjd:
                        if dad_names_new[j] == '':
                            dad_names_new[j] = dad_names[i]
                        elif dad_names[i] != '' and dad_names[i] != dad_names_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 121')
                            
                        if dad_birthdates_new[j] == '':
                            dad_birthdates_new[j] = dad_birthdates[i]
                        elif dad_birthdates[i] != '' and dad_birthdates[i] != dad_birthdates_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 122')
                            
                        if dad_birthplaces_new[j] == '':
                            dad_birthplaces_new[j] = dad_birthplaces[i]
                        elif dad_birthplaces[i] != '' and dad_birthplaces[i] != dad_birthplaces_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 123')
                            
                        if dad_deathdates_new[j] == '':
                            dad_deathdates_new[j] = dad_deathdates[i]
                        elif dad_deathdates[i] != '' and dad_deathdates[i] != dad_deathdates_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 124')
                            
                        if dad_deathplaces_new[j] == '':
                            dad_deathplaces_new[j] = dad_deathplaces[i]
                        elif dad_deathplaces[i] != '' and dad_deathplaces[i] != dad_deathplaces_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 125')
                            
                        if dad_burialdates_new[j] == '':
                            dad_burialdates_new[j] = dad_burialdates[i]
                        elif dad_burialdates[i] != '' and dad_burialdates[i] != dad_burialdates_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 126')
                            
                        if dad_burialplaces_new[j] == '':
                            dad_burialplaces_new[j] = dad_burialplaces[i]
                        elif dad_burialplaces[i] != '' and dad_burialplaces[i] != dad_burialplaces_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 127')

        for i, fsid in enumerate(mom_FSIDs):
            if fsid not in mom_FSIDs_new and fsid != '' and fsid != 'nan':
                mom_FSIDs_new.append(fsid)
                mom_names_new.append(mom_names[i])
                mom_birthdates_new.append(mom_birthdates[i])
                mom_birthplaces_new.append(mom_birthplaces[i])
                mom_deathdates_new.append(mom_deathdates[i])
                mom_deathplaces_new.append(mom_deathplaces[i])
                mom_burialdates_new.append(mom_burialdates[i])
                mom_burialplaces_new.append(mom_burialplaces[i])
            else:
                for j, fsjd in enumerate(mom_FSIDs_new):
                    if fsid == fsjd:
                        if mom_names_new[j] == '':
                            mom_names_new[j] = mom_names[i]
                        elif mom_names[i] != '' and mom_names[i] != mom_names_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 131')
                            
                        if mom_birthdates_new[j] == '':
                            mom_birthdates_new[j] = mom_birthdates[i]
                        elif mom_birthdates[i] != '' and mom_birthdates[i] != mom_birthdates_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 132')
                            
                        if mom_birthplaces_new[j] == '':
                            mom_birthplaces_new[j] = mom_birthplaces[i]
                        elif mom_birthplaces[i] != '' and mom_birthplaces[i] != mom_birthplaces_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 133')
                            
                        if mom_deathdates_new[j] == '':
                            mom_deathdates_new[j] = mom_deathdates[i]
                        elif mom_deathdates[i] != '' and mom_deathdates[i] != mom_deathdates_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 134')
                            
                        if mom_deathplaces_new[j] == '':
                            mom_deathplaces_new[j] = mom_deathplaces[i]
                        elif mom_deathplaces[i] != '' and mom_deathplaces[i] != mom_deathplaces_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 135')
                            
                        if mom_burialdates_new[j] == '':
                            mom_burialdates_new[j] = mom_burialdates[i]
                        elif mom_burialdates[i] != '' and mom_burialdates[i] != mom_burialdates_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 136')
                            
                        if mom_burialplaces_new[j] == '':
                            mom_burialplaces_new[j] = mom_burialplaces[i]
                        elif mom_burialplaces[i] != '' and mom_burialplaces[i] != mom_burialplaces_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 137')

        for i, fsid in enumerate(sibling_FSIDs):
            if fsid not in sibling_FSIDs_new and fsid != '' and fsid != 'nan':
                sibling_FSIDs_new.append(fsid)
                try:
                    sibling_names_new.append(sibling_names[i])
                except IndexError:
                    pass
                try:
                    sibling_birthdates_new.append(sibling_birthdates[i])
                except IndexError:
                    pass
                try:
                    sibling_sexes_new.append(sibling_sexes[i])
                except IndexError:
                    pass

        for i, fsid in enumerate(kid_FSIDs):
            if fsid not in kid_FSIDs_new and fsid != '' and fsid != 'nan':
                kid_FSIDs_new.append(fsid)
                kid_names_new.append(kid_names[i])
                kid_birthdates_new.append(kid_birthdates[i])
                kid_sexes_new.append(kid_sexes[i])
                kid_birthplaces_new.append(kid_birthplaces[i])
                kid_deathdates_new.append(kid_deathdates[i])
                kid_deathplaces_new.append(kid_deathplaces[i])
                kid_burialdates_new.append(kid_burialdates[i])
                kid_burialplaces_new.append(kid_burialplaces[i])
            else:
                for j, fsjd in enumerate(kid_FSIDs_new):
                    if fsid == fsjd:
                        if kid_names_new[j] == '':
                            kid_names_new[j] = kid_names[i]
                        elif kid_names[i] != '' and kid_names[i] != kid_names_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 151')
                            
                        if kid_birthdates_new[j] == '':
                            kid_birthdates_new[j] = kid_birthdates[i]
                        elif kid_birthdates[i] != '' and kid_birthdates[i] != kid_birthdates_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 152')
                            
                        if kid_sexes_new[j] == '':
                            kid_sexes_new[j] = kid_sexes[i]
                        elif kid_sexes[i] != '' and kid_sexes[i] != kid_sexes_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 153')
                            
                        if kid_birthplaces_new[j] == '':
                            kid_birthplaces_new[j] = kid_birthplaces[i]
                        elif kid_birthplaces[i] != '' and kid_birthplaces[i] != kid_birthplaces_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 154')
                            
                        if kid_deathdates_new[j] == '':
                            kid_deathdates_new[j] = kid_deathdates[i]
                        elif kid_deathdates[i] != '' and kid_deathdates[i] != kid_deathdates_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 155')
                            
                        if kid_deathplaces_new[j] == '':
                            kid_deathplaces_new[j] = kid_deathplaces[i]
                        elif kid_deathplaces[i] != '' and kid_deathplaces[i] != kid_deathplaces_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 156')
                            
                        if kid_burialdates_new[j] == '':
                            kid_burialdates_new[j] = kid_burialdates[i]
                        elif kid_burialdates[i] != '' and kid_burialdates[i] != kid_burialdates_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 157')
                
                        if kid_burialplaces_new[j] == '':
                            kid_burialplaces_new[j] = kid_burialplaces[i]
                        elif kid_burialplaces[i] != '' and kid_burialplaces[i] != kid_burialplaces_new[j]:
                            raise ValueError('Something Inexcusable has happened. Tell Chris. ERROR CODE 158')
                            
        spouse_names_new = ';'.join(spouse_names_new)
        spouse_FSIDs_new = ';'.join(spouse_FSIDs_new)
        spouse_birthdates_new = ';'.join(spouse_birthdates_new)
        spouse_birthplaces_new = ';'.join(spouse_birthplaces_new)
        spouse_deathdates_new = ';'.join(spouse_deathdates_new)
        spouse_deathplaces_new = ';'.join(spouse_deathplaces_new)
        spouse_burialdates_new = ';'.join(spouse_burialdates_new)
        spouse_burialplaces_new = ';'.join(spouse_burialplaces_new)
        dad_names_new = ';'.join(dad_names_new)
        dad_FSIDs_new = ';'.join(dad_FSIDs_new)
        dad_birthdates_new = ';'.join(dad_birthdates_new)
        dad_birthplaces_new = ';'.join(dad_birthplaces_new)
        dad_deathdates_new = ';'.join(dad_deathdates_new)
        dad_deathplaces_new = ';'.join(dad_deathplaces_new)
        dad_burialdates_new = ';'.join(dad_burialdates_new)
        dad_burialplaces_new = ';'.join(dad_burialplaces_new)
        mom_names_new = ';'.join(mom_names_new)
        mom_FSIDs_new = ';'.join(mom_FSIDs_new)
        mom_birthdates_new =';'.join(mom_birthdates_new)
        mom_birthplaces_new = ';'.join(mom_birthplaces_new)
        mom_deathdates_new = ';'.join(mom_deathdates_new)
        mom_deathplaces_new = ';'.join(mom_deathplaces_new)
        mom_burialdates_new = ';'.join(mom_burialdates_new)
        mom_burialplaces_new = ';'.join(mom_burialplaces_new)
        sibling_names_new = ';'.join(sibling_names_new)
        sibling_FSIDs_new = ';'.join(sibling_FSIDs_new)
        sibling_birthdates_new = ';'.join(sibling_birthdates_new)
        sibling_sexes_new = ';'.join(sibling_sexes_new)
        kid_names_new = ';'.join(kid_names_new)
        kid_FSIDs_new = ';'.join(kid_FSIDs_new)
        kid_birthdates_new = ';'.join(kid_birthdates_new)
        kid_sexes_new = ';'.join(kid_sexes_new)
        kid_birthplaces_new = ';'.join(kid_birthplaces_new)
        kid_deathdates_new = ';'.join(kid_deathdates_new)
        kid_deathplaces_new = ';'.join(kid_deathplaces_new)
        kid_burialdates_new = ';'.join(kid_burialdates_new)
        kid_burialplaces_new = ';'.join(kid_burialplaces_new)
        
        return_info[key] = pd.Series([return_info[key]['uid'], spouse_names_new,
                                     spouse_FSIDs_new, spouse_birthdates_new,
                   spouse_birthplaces_new, spouse_deathdates_new, spouse_deathplaces_new,
                   spouse_burialdates_new, spouse_burialplaces_new,
                   dad_names_new, dad_FSIDs_new, dad_birthdates_new, dad_birthplaces_new,
                   dad_deathdates_new, dad_deathplaces_new, dad_burialdates_new,
                   dad_burialplaces_new,
                   mom_names_new, mom_FSIDs_new, mom_birthdates_new, mom_birthplaces_new,
                   mom_deathdates_new, mom_deathplaces_new, mom_burialdates_new,
                   mom_burialplaces_new,
                   sibling_names_new, sibling_FSIDs_new, sibling_birthdates_new,
                   sibling_sexes_new,
                   kid_names_new, kid_FSIDs_new, kid_birthdates_new, kid_sexes_new,
                   kid_birthplaces_new, kid_deathdates_new, kid_deathplaces_new,
                   kid_burialdates_new, kid_burialplaces_new], index = ['uid', 'spouse_name', \
                             'spouse_FSIDs', \
                             'spouse_birthdates', 'spouse_birthplaces', \
                             'spouse_deathdates', 'spouse_deathplaces', \
                             'spouse_burialdates', 'spouse_burialplaces', \
                             'dad_names', 'dad_FSIDs', 'dad_birthdates', \
                             'dad_birthplaces',\
                             'dad_deathdates', 'dad_deathplaces', \
                             'dad_burialdates', 'dad_burialplaces', \
                             'mom_names', 'mom_FSIDs', 'mom_birthdates', \
                             'mom_birthplaces',\
                             'mom_deathdates', 'mom_deathplaces', \
                             'mom_burialdates', 'mom_burialplaces', \
                             'sibling_names', 'sibling_FSIDs', \
                             'sibling_birthdates', 'sibling_sexes', \
                             'kid_names', 'kid_FSIDs', 'kid_birthdates', \
                             'kid_sexes', \
                             'kid_birthplaces', 'kid_deathdates', \
                             'kid_deathplaces', 'kid_burialdates', \
                             'kid_burialplaces'])
    
    

                

    return pd.DataFrame(return_info).transpose()
                    
                    
    '''
    if not pd.isnull(cell):
        if pd.isnull(fam_info.at[i, col]):
            fam_info.at[i, col] = fam_info.at[i + 1,col]
        elif re.search(".+;$", str(fam_info.at[i, col])):
            fam_info.at[i, col] += str(fam_info.at[i + 1, col])
        else:
            fam_info.at[i,col] += ';' + str(fam_info.at[i + 1, col])
    fam_info.at[i + 1, col] = np.nan
    '''
    return return_info

def _remove_non_ascii_1(text):
    '''
    This function removes non ascii characters from a string.
    '''
    try:
        stuff = ''.join(i for i in text if ord(i)<128)
    except:
        stuff = ''
    return stuff



def Modify_Row(row, args):
    '''
    This function combines the family information with the initial scrape info
    '''
    global merged_ref
    #merged_ref = args
    (merged_ref) = args
    for ref in merged_ref:
        if str(row['uid']) == str(ref['uid']): 
            if row['spouse_name'] == "":
                row['spouse_name'] = ref['spouse_name']
            elif len(ref['spouse_name']) > 0:
                row['spouse_name'] = row['spouse_name'] + ';' + ref['spouse_name']
                
            if row['kid_names'] == "":
                row['kid_names'] = ref['kid_names']
            elif len(ref['kid_names']) > 0:
                row['kid_names'] = row['kid_names'] + ';' + ref['kid_names']
                
            if row['kid_birthdates'] == "":
                row['kid_birthdates'] = ref['kid_birthdates']
            elif len(ref['kid_birthdates']) > 0:
                row['kid_birthdates'] = row['kid_birthdates'] + ';' + ref['kid_birthdates']
                
            if row['kid_sexes'] == "":
                row['kid_sexes'] = ref['kid_sexes']
            elif len(ref['kid_sexes']) > 0:
                row['kid_sexes'] = row['kid_sexes'] + ';' + ref['kid_sexes']
                
            if row['dad_names'] == "":
                row['dad_names'] = ';'.join(ref['dad_names'])
            elif len(ref['dad_names']) > 0:
                row['dad_names'] = row['dad_names'] + ';' + ref['dad_names']
                
            if row['dad_birthdates'] == "":
                row['dad_birthdates'] = ref['dad_birthdates']
            elif len(ref['dad_birthdates']) > 0:
                row['dad_birthdates'] = row['dad_birthdates'] + ';' + ref['dad_birthdates']
                
            if row['mom_names'] == "":
                row['mom_names'] = ref['mom_names']
            elif len(ref['mom_names']) > 0:
                row['mom_names'] = row['mom_names'] + ';' + ref['mom_names']
                
            if row['mom_birthdates'] == "":
                row['mom_birthdates'] = ref['mom_birthdates']
            elif len(ref['mom_birthdates']) > 0:
                row['mom_birthdates'] = row['mom_birthdates'] + ';' + ref['mom_birthdates']
                
            if row['sibling_FSIDs'] == "":
                row['sibling_FSIDs'] = ref['sibling_FSIDs']
            elif len(ref['sibling_FSIDs']) > 0:
                row['sibling_FSIDs'] = row['sibling_FSIDs'] + ';' + ref['sibling_FSIDs']
                
            if row['sibling_names'] == "":
                row['sibling_names'] = ref['sibling_names']
            elif len(ref['sibling_names']) > 0:
                row['sibling_names'] = row['sibling_names'] + ';' + ref['sibling_names']
                
            if row['sibling_birthdates'] == "":
                row['sibling_birthdates'] = ref['sibling_birthdates']
            elif len(ref['sibling_birthdates']) > 0:
                row['sibling_birthdates'] = row['sibling_birthdates'] + ';' + ref['sibling_birthdates']
                
            if row['sibling_sexes'] == "":
                row['sibling_sexes'] = ref['sibling_sexes']
            elif len(ref['sibling_sexes']) > 0:
                row['sibling_sexes'] = row['sibling_sexes'] + ';' + ref['sibling_sexes']
                
            
            #For behold! Thy overly long names doth offend me. Therefore every name that is over 244 characters long shall
            #not enter the rest of STATA, but shall be cast out;
            '''
            row['spouse_name'] = row['spouse_name'][:244]
            row['kid_names'] = row['kid_names'][:244]
            row['kid_birthdates'] = row['kid_birthdates'][:244]
            row['kid_sexes'] = row['kid_sexes'][:244]
            row['dad_names'] = row['dad_names'][:244]
            row['dad_birthdates'] = row['dad_birthdates'][:244]
            row['mom_names'] = row['mom_names'][:244]
            row['mom_birthdates'] = row['mom_birthdates'][:244]
            row['sibling_names'] = row['sibling_names'][:244]
            row['sibling_birthdates'] = row['sibling_birthdates'][:244]
            row['sibling_sexes'] = row['sibling_sexes'][:244]
            '''
            return row
    return row
    
    
def ScrapeFamily(self, reference, outfile, ids_set, key, opened_file, fam_death, sibs):
    '''
    This is a helper function that runs the family scrape after the initial scrape is run.
    It will not ever be called if basic=True
    '''
    # out = pd.read_csv(outfile[:-4] + '.csv', header = 0)
    out = pd.DataFrame([], columns=['FSID', 'uid', 'pr_name', 'pr_birthdate', \
                       'pr_sex', 'pr_birthplace', 'pr_deathdate', \
                       'pr_deathplace', 'spouse_name', 'spouse_FSID', \
                       'marriages', 'marriageplaces', 'kid_names', \
                       'kid_FSIDs', 'kid_birthdates', 'kid_sexes', \
                       'dad_names', 'dad_FSIDs', 'dad_birthdates', \
                       'mom_names', 'mom_FSIDs', 'mom_birthdates', \
                       'sibling_names', 'sibling_FSIDs', 'sibling_birthdates',\
                       'sibling_sexes', 'hints', 'sources'])
    out = out.fillna('')
    ids = ','.join(ids_set)
    
    pull = requests.get('http://api.familysearch.org/platform/tree/persons?pids=%s' %(ids), 
                               headers={'Authorization': 'Bearer %s' %(key), 
                                        'Accept':'application/json'})
    for _ in range(5):            
        try:                         
            if pull.status_code != 401:
                persons = pull.json()['persons']
                break
            elif pull.status_code == 429:
                wait = (int(pull.headers['Retry-After'])*1.1)
                print('Throttled, waiting {0: .1f} seconds!'.format(wait))
                time.sleep(wait)
            else:
                self.token = self.Authenticate()
        except:
            pull = requests.get('http://api.familysearch.org/platform/tree/persons?pids=%s' %(ids), 
                            headers={'Authorization': 'Bearer %s' %(self.token), 
                                     'Accept':'application/json'})
                            
    names_etc = []
    
    for guy in persons:
        # Get personal Data
        try:
            fsid = _remove_non_ascii_1(guy['id'])
        except KeyError:
            fsid = ''
        try:
            name = _remove_non_ascii_1(guy['display']['name'])
        except KeyError:
            name = ''
        try:
            birth = _remove_non_ascii_1(guy['display']['birthDate'])
        except KeyError:
            birth = ''
        try:
            sex = _remove_non_ascii_1(guy['display']['gender'])
        except KeyError:
            sex = ''
        # Get additional family information
        if fam_death:
            #get birthplace
            try:
            	birthplace = _remove_non_ascii_1(guy['display']['birthPlace'])
            except KeyError:
            	birthplace = ''
            #get death date
            try:
            	death = _remove_non_ascii_1(guy['display']['deathDate'])
            except KeyError:
            	death = ''
            #get death place
            try:
            	deathplace = _remove_non_ascii_1(guy['display']['deathPlace'])
            except KeyError:
            	deathplace = ''
            #get burial date and place
            try:
            	burial = ''
            	burialplace = ''
            	for bur in guy['facts']:
            		if bur['type'] == 'http://gedcomx.org/Burial':
            			try:
            				burial = _remove_non_ascii_1(bur['date']['normalized'][0]['value'])
            			except KeyError:
            				burial = ''
            				
            			try:
            				burialplace = _remove_non_ascii_1(bur['place']['normalized'][0]['value'])
            			except KeyError:
            				burialplace = ''
            except KeyError:
            	burial = ''
            	burialplace = ''  
        
        else:
            birthplace = ''
            death = ''
            deathplace = ''
            burial = ''
            burialplace = ''
        
          
        #Get a list of the kids IDs. this is to obtain sibling IDS from the parents
        kidids = ''
        kidlist = []
        try:
            for fam in guy['display']['familiesAsParent']:
                try:
                    for child in fam['children']:
                        try:
                            if (child['resourceId']) not in kidlist:
                                kidids = _remove_non_ascii_1(kidids + child['resourceId'] + ';')
                                kidlist.append(child['resourceId'])
                        except KeyError:
                            pass
                except KeyError:
                    pass
        except KeyError:
            pass
        
        if len(kidids) > 0:
            kidids = kidids[:-1]
            
        info = {'id': fsid, 'name': name, 'birthdate' : birth, 'sex' : sex,\
                'kidids' : kidids, 'birthplace' : birthplace, \
                'deathdate' : death, 'deathplace' : deathplace, \
                'burialdate' : burial, 'burialplace' : burialplace}
        names_etc.append(info)
        
        
    #Next we're going to do an m:1 merge with reference
    merged_ref = []
    
    for rec in reference:    
        spouse_name = []
        spouse_FSID = []
        spouse_birthdate = []
        kid_names = []
        kid_FSIDs = []
        kid_birthdates = []
        kid_sexes = []
        dad_names = []
        dad_FSIDs = []
        dad_birthdates = []
        mom_names = []
        mom_FSIDs = []
        mom_birthdates = []
        sibling_names = []
        sibling_FSIDs = []
        sibling_birthdates = []
        sibling_sexes = []
        if fam_death:
            spouse_birthplaces = []
            spouse_deathdates = []
            spouse_deathplaces = []
            spouse_burialdates = []
            spouse_burialplaces = []
            kid_birthplaces = []
            kid_deathdates = []
            kid_deathplaces = []
            kid_burialdates = []
            kid_burialplaces = []
            dad_birthplaces = []
            dad_deathdates = []
            dad_deathplaces = []
            dad_burialdates = []
            dad_burialplaces = []
            mom_birthplaces = []
            mom_deathdates = []
            mom_deathplaces = []
            mom_burialdates = []
            mom_burialplaces = []
            
        
        mom_beat_you_to_it_dad = False
             
        
        for fsid_ in rec['kids']:   
            has_friends = False
            for etc in names_etc:
                if fsid_ == etc['id'] and has_friends == False:
                    has_friends = True
                    kid_names.append(etc['name'])
                    kid_FSIDs.append(etc['id'])
                    kid_birthdates.append(etc['birthdate'])
                    kid_sexes.append(etc['sex'])
                    if fam_death:
                        kid_birthplaces.append(etc['birthplace'])
                        kid_deathdates.append(etc['deathdate'])
                        kid_deathplaces.append(etc['deathplace'])
                        kid_burialdates.append(etc['burialdate'])
                        kid_burialplaces.append(etc['burialplace'])
                    break
            if has_friends == False:
                kid_names.append('')
                kid_FSIDs.append('')
                kid_birthdates.append('')
                kid_sexes.append('')
                if fam_death:
                    kid_birthplaces.append('')
                    kid_deathdates.append('')
                    kid_deathplaces.append('')
                    kid_burialdates.append('')
                    kid_burialplaces.append('')

        for fsid_ in rec['spouses']:
            has_friends = False
            for etc in names_etc:       
                if has_friends == False and fsid_ == etc['id']:
                    has_friends = True
                    spouse_name.append(etc['name'])
                    spouse_FSID.append(etc['id'])
                    spouse_birthdate.append(etc['birthdate'])
                    if fam_death:
                        spouse_birthplaces.append(etc['birthplace'])
                        spouse_deathdates.append(etc['deathdate'])
                        spouse_deathplaces.append(etc['deathplace'])
                        spouse_burialdates.append(etc['burialdate'])
                        spouse_burialplaces.append(etc['burialplace'])
                    break
            if has_friends == False:
                spouse_name.append('')
                spouse_FSID.append('')
                spouse_birthdate.append('')
                if fam_death:
                    spouse_birthplaces.append('')
                    spouse_deathdates.append('')
                    spouse_deathplaces.append('')
                    spouse_burialdates.append('')
                    spouse_burialplaces.append('')
               
        
        for fsid_ in rec['moms']:
            has_friends = False
            for etc in names_etc:    
                if fsid_ == etc['id'] and has_friends == False:
                    has_friends = True
                    mom_names.append(etc['name'])
                    mom_FSIDs.append(etc['id'])
                    mom_birthdates.append(etc['birthdate'])
                    sibling_FSIDs.append(etc['kidids'])
                    mom_beat_you_to_it_dad = True
                    if fam_death:
                        mom_birthplaces.append(etc['birthplace'])
                        mom_deathdates.append(etc['deathdate'])
                        mom_deathplaces.append(etc['deathplace'])
                        mom_burialdates.append(etc['burialdate'])
                        mom_burialplaces.append(etc['burialplace'])
                    break
            if has_friends == False:
                mom_names.append('')
                mom_FSIDs.append('')
                mom_birthdates.append('')
                if fam_death:
                    mom_birthplaces.append('')
                    mom_deathdates.append('')
                    mom_deathplaces.append('')
                    mom_burialdates.append('')
                    mom_burialplaces.append('')

                    
        for fsid_ in rec['dads']:
            has_friends = False
            for etc in names_etc:   
                if fsid_ == etc['id'] and has_friends == False:
                    has_friends = True
                    dad_names.append(etc['name'])
                    dad_FSIDs.append(etc['id'])
                    dad_birthdates.append(etc['birthdate'])
                    if not mom_beat_you_to_it_dad:
                        sibling_FSIDs.append(etc['kidids'])
                    if fam_death:
                        dad_birthplaces.append(etc['birthplace'])
                        dad_deathdates.append(etc['deathdate'])
                        dad_deathplaces.append(etc['deathplace'])
                        dad_burialdates.append(etc['burialdate'])
                        dad_burialplaces.append(etc['burialplace'])
                    break
            if has_friends == False:
                    dad_names.append('')
                    dad_FSIDs.append('')
                    dad_birthdates.append('')
                    if not mom_beat_you_to_it_dad:
                        sibling_FSIDs.append('')
                    if fam_death:
                        dad_birthplaces.append('')
                        dad_deathdates.append('')
                        dad_deathplaces.append('')
                        dad_burialdates.append('')
                        dad_burialplaces.append('')
              
                    
        for fsid_ in rec['siblings']:
            has_friends = False
            for etc in names_etc:            
                if fsid_ == etc['id'] and has_friends == False:
                    has_friends = True
                    sibling_names.append(etc['name'])
                    sibling_FSIDs.append(etc['id'])
                    sibling_birthdates.append(etc['birthdate'])
                    sibling_sexes.append(etc['sex'])
                    break
            if has_friends == False:
                sibling_names.append('')
                sibling_FSIDs.append('')
                sibling_birthdates.append('')
                sibling_sexes.append('')

        
        # creating a dictionary with all of the information that was grabbed            
        merged = {'spouse_names':spouse_name, 'spouse_FSID': spouse_FSID, \
                  'spouse_birthdates' : spouse_birthdate, \
                  'spouse_birthplaces' : spouse_birthplaces, \
                  'spouse_deathdates' : spouse_deathdates, \
                  'spouse_deathplaces' : spouse_deathplaces, \
                  'spouse_burialdates' : spouse_burialdates, \
                  'spouse_burialplaces' : spouse_burialplaces, \
                  'kid_names': kid_names, 'kid_FSIDs': kid_FSIDs, \
                  'kid_birthdates': kid_birthdates, \
                  'kid_birthplaces' : kid_birthplaces, \
                  'kid_deathdates' : kid_deathdates, \
                  'kid_deathplaces' : kid_deathplaces, \
                  'kid_burialdates' : kid_burialdates, \
                  'kid_burialplaces' : kid_burialplaces, \
                  'kid_sexes':kid_sexes, 'dad_names':dad_names, \
                  'dad_FSIDs':dad_FSIDs, 'dad_birthdates': dad_birthdates, \
                  'dad_birthplaces' : dad_birthplaces, \
                  'dad_deathdates' : dad_deathdates, \
                  'dad_deathplaces' : dad_deathplaces, \
                  'dad_burialdates' : dad_burialdates, \
                  'dad_burialplaces' : dad_burialplaces, \
                  'mom_names': mom_names, 'mom_FSIDs': mom_FSIDs, \
                  'mom_birthdates': mom_birthdates, \
                  'mom_birthplaces' : mom_birthplaces, \
                  'mom_deathdates' : mom_deathdates, \
                  'mom_deathplaces' : mom_deathplaces, \
                  'mom_burialdates' : mom_burialdates, \
                  'mom_burialplaces' : mom_burialplaces, \
                  'sibling_names':sibling_names, \
                  'sibling_FSIDs': sibling_FSIDs, \
                  'sibling_birthdates':sibling_birthdates, \
                  'sibling_sexes':sibling_sexes, 'uid': rec['uid']}
        
        # making multiple values for single observations semi-colon delimited
        for key in merged.keys():
            if type(merged[key]) == list:
                merged[key] = ";".join(merged[key])
        
        # adding dictionary to list to be made into dataframe
        merged_ref.append(merged)
                    
    # And finally, we do a 1:1 merge with the final data.
    # arg = (merged_ref,)
    '''
    if sibs:
        pass
        # implement the GetSiblings() function here
    '''  
        
    # out_df.apply(Modify_Row, axis=0, args=arg)
    # saving family information to file
    out_df = pd.DataFrame(merged_ref).replace('', np.nan)

    if fam_death:
        out_df = pd.DataFrame(merged_ref).reindex(['uid', 'spouse_names', \
                             'spouse_birthdates', 'spouse_birthplaces', \
                             'spouse_FSID', 'dad_FSIDs','mom_FSIDs','kid_FSIDs', \
                             'spouse_deathdates', 'spouse_deathplaces', \
                             'spouse_burialdates', 'spouse_burialplaces', \
                             'dad_names', 'dad_birthdates', \
                             'dad_birthplaces',\
                             'dad_deathdates', 'dad_deathplaces', \
                             'dad_burialdates', 'dad_burialplaces', \
                             'mom_names', 'mom_birthdates', \
                             'mom_birthplaces',\
                             'mom_deathdates', 'mom_deathplaces', \
                             'mom_burialdates', 'mom_burialplaces', \
                             'sibling_names', 'sibling_FSIDs', \
                             'sibling_birthdates', 'sibling_sexes', \
                             'kid_names', 'kid_birthdates', \
                             'kid_sexes', \
                             'kid_birthplaces', 'kid_deathdates', \
                             'kid_deathplaces', 'kid_burialdates', \
                             'kid_burialplaces',], axis=1)
    else:
        raise ValueError('THISHASNOTBEENIMPLEMENTEDCORRECTLYERROR')
        out_df = pd.DataFrame(merged_ref).reindex(['uid', 'spouse_names', \
                             'dad_names', 'dad_birthdates', 'mom_names', \
                             'mom_birthdates', 'sibling_names', \
                             'sibling_FSIDs', 'sibling_birthdates', \
                             'sibling_sexes', 'kid_names', 'kid_birthdates', \
                             'kid_sexes'], axis='columns')

    out_df.dropna(axis=0, how='all').sort_values(by='uid').to_csv(opened_file, index = False, header = False)
    
    # sending the sibling FSIDs for the sibling scrape
    # return (merged_ref, sibling_FSIDs)
'''
def ScrapeSiblings(self, merged_ref, key):
    \'''
    This is meant to build on the ScrapeFamily function to 
    allow it to get the sibling information that requires an 
    extra API call
    \'''
    
    ids = []
    id_cache = []
    
    for ref in merged_ref:
        for fsid in ref['kid_FSIDs'].split(';'):
            if fsid != '':
                ids.append(fsid)
    ids = list(set(ids))
    for i in range(200, len(ids) + 200, 200):
        id_cache.append(ids[i-200:i])
    
    for chunk in id_cache:
        ids = ','.join(chunk)         
        pull = requests.get('http://api.familysearch.org/platform/tree/persons?pids=%s' %(ids), 
                                   headers={'Authorization': 'Bearer %s' %(key), 
                                            'Accept':'application/json'})
        while(True):            
            try:                         
                if pull.status_code != 401:
                    persons = pull.json()['persons']
                    break
                else:
                    key = self.Authenticate()
            except:
                pull = requests.get('http://api.familysearch.org/platform/tree/persons?pids=%s' %(ids), 
                                headers={'Authorization': 'Bearer %s' %(key), 
                                         'Accept':'application/json'})
        
        for guy in persons:            
            #Get fsid
            try:
                fsid = _remove_non_ascii_1(guy['id'])
            except KeyError:
                fsid = ''
            #store fsid
            if not basic:
                ind_ = str(your_infile_but_cooler[fsid])
                relationships['uid'] = str(your_infile_but_cooler[fsid])
            #get name
            try:
                name = _remove_non_ascii_1(guy['display']['name'])
            except KeyError:
                name = ''
            #get birthdate
            try:
                birth = _remove_non_ascii_1(guy['display']['birthDate'])
            except KeyError:
                birth = ''
            #get gender
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
                death = _remove_non_ascii_1(guy['display']['deathDate'])
            except KeyError:
                death = ''
            #get death place
            try:
                deathplace = _remove_non_ascii_1(guy['display']['deathPlace'])
            except KeyError:
                deathplace = ''
            #get burial date and place
            try:
                burial = ''
                burialplace = ''
                for bur in guy['facts']:
                    if bur['type'] == 'http://gedcomx.org/Burial':
                        try:
                            burial = _remove_non_ascii_1(bur['date']['normalized'][0]['value'])
                        except KeyError:
                            burial = ''
                            
                        try:
                            burialplace = _remove_non_ascii_1(bur['place']['normalized'][0]['value'])
                        except KeyError:
                            burialplace = ''
            except KeyError:
                burial = ''
                burialplace = ''
            
        sibling_names = []
        sibling_FSIDs = []
        sibling_birthdates = []
        sibling_sexes = []
        
        for fsid_ in rec['siblings']:
                for etc in names_etc:            
                    if fsid_ == etc['id']:
                        sibling_names.append(etc['name'])
                        sibling_FSIDs.append(etc['id'])
                        sibling_birthdates.append(etc['birthdate'])
                        sibling_sexes.append(etc['sex'])
                        break
'''

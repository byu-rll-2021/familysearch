# -*- coding: utf-8 -*-
"""
This is the thid iteration of the find code. I updated the name so that old 
will still run for testing though we should probably update the code and make
the old version offically deprecated. I used the old Find function as a basis
for this function and gutted a lot of excess, inefficiency and bad practice. I 
tried to use more descriptive variable names and make the code easier to
follow. The main change that I made for being able to follow what the function
is actually doing is changing lists of info to be dictionaries so instead of
memorising an index that corresponds to a kind of data there will be names that
should make it more clear what is found at the given location.

This of course does not mean that what I wrote has not committed similar sins
though I do believe that they are less agregious if that is the case. There is
more optimizing that can be done. I left FIXME notes at cases like that which
will take more time to improve than I am able to give right now.

I stopped trying to optimize things for the scoring and just made a change to
dictionaries instead of lists. This is not because the code beyond line 317
is perfect. The scoring is really large, arbitrary and full of a variety of
moving parts. I did not want to gte lost in there once I dove in. 

I plan to test our old scoring method compared to the familysearch algorithm
and see which one performs better as the API now returns a score with the
search and should sort its output to have the best match first.


Created: 5 June 2019
Author: Ben Branchflower
"""
import sys
sys.path.append(r'R:\JoePriceResearch\Python\Anaconda3\Lib\site-packages')

import re
from time import sleep

import numpy as np
import pandas as pd
import requests
from jellyfish import jaro_distance
from pandas.errors import EmptyDataError
import csv

   

def FindPerson(self, names=None, report=False, token=None, token_report=True,
               write_names_dict=True, count=10, verbosity=0):
    '''
    Searches for the data for an individual and creates match scores for 
    the top three search results.
        
    Match scores are a long and illustrious tradition here at Joe Price Labs.
    We pride ourselves in creating the best and finest. Our scores over 6.5 
    correctly predict a match with 99.99% accuracy [citation needed]. We also 
    find that scores below 4 are usually a no match.
    
    Ultimately we need everything to have the names given below, so you can
    either order your data in exactly the given order and give no dictionary,
    or if you just have a few parameters you can pass in a dictionary mapping
    your variable names to those given below.
    
    Parameters
    ----------
    names     - A dictionary getting the appropriate column names.
    report    - Whether the program prints the full scoring and error report.
    count     - max number of returned results
    verbosity - a number which when increased cause more things to be printed
                to standard out
    '''
    
    # constants

    # use the token passed in manually instead of the default
    if token is not None:
        self.token = token
    
    
    varlist = ['index', 'givenName', 'surname', 'sex', 'birthLikeDate',
               'birthLikePlace', 'deathLikeDate', 'deathLikePlace',
               'marriageLikeDate', 'marriageLikePlace', 'residenceDate',
               'residencePlace', 'fatherGivenName', 'fatherSurname',
               'fatherBirthLikePlace', 'motherGivenName', 'motherSurname',
               'motherBirthLikePlace', 'parentGivenName', 'parentSurname',
               'parentBirthLikePlace', 'spouseGivenName', 'spouseSurname']
    
    # Read in the input file.
    if names is None:
        df = pd.read_csv(self.infile, header=None)
    else:
        try:
            df = pd.read_csv(self.infile)
        except UnicodeDecodeError as e:
            print(e)
            print('UnicodeDecodeError : the function will try with a',
                  'different encoding that may or may not work, this is often',
                  'due to special characters from a stata file')
            df = pd.read_csv(self.infile, encoding='latin1')
    
    # writing the names used for user reference later or to be copied 
    with open(self.outfile[:-4] + '_names_dict.txt', 'w') as names_dict:
        names_dict.write(str(names))

    # Rename the columns as specified.
    # FIXME: use the column name standardization function when it is ready
    df.rename(columns=names, inplace=True)
    
    df = _check_start(df, self.outfile)
    
    # Get the number of rows.
    row_count = len(df)
    
    # Make sure we have all of the necessary columns.

    
    # Make all columns string.
    df.fillna('', inplace=True)
    df = df.astype(str)
    
    # cleaning up the data
    for var in df.columns:
        if 'Date' in var:
            df[var] = df[var].str.replace('\.[0-9]+','')
        if 'Name' in var:
            df[var] = df[var].str.replace('\s+',' ')
        if 'Place' in var:
            df[var] = df[var].str.replace(':|;\s?',', ')



    # FIXME: standardize input from variables like sex and dates


    # Loop over rows in the dataframe.
    allresults = []
    tracker = []
    
    self._timer('on')
    
    # initialize the session object
    search_session = requests.Session()
    # update headers
    search_session.headers.update({'Authorization': f'Bearer {self.token}',
                            'Accept':'application/x-gedcomx-atom+json',
                            'X-FS-Feature-Tag':'generic.search.terms'})
    
    person_session = requests.Session()
    person_session.headers.update({'Authorization': f'Bearer {self.token}',
                            'Accept':'application/json'})
    
    # opening outfiles
    out = open(self.outfile, 'a')
    
    
    # print(df)
    print(df.index)
    
    for i in range(20): #(df.shape[0]):
        # Form the search query.

        q_string = f'http://api.familysearch.org/platform/tree/search?count={count}&'
    
        if verbosity > 3:
            print(df.iloc[i,:])
            
        q_string += '&'.join([re.sub(' ', '+', f'q.{col}={val}'.strip(' .')) if 'Date' not in col else f'q.{col}=+{val}'for col, val in zip(df.columns, df.iloc[i,:]) if val != ''])
        # example query string, using the new generic parameters so our form is slightly different
        # ?start=0&count=20&q=motherGivenName:Clarissa+surname:Heaton+givenName:Israel+fatherSurname:Heaton+motherSurname:Hoyt+fatherGivenName:Jonathan
        
        if verbosity > 2:
            print(q_string)


        # Make the search request        
        response = self._ping_api(q_string, search_session, verbosity)
        
        # If there are no search results, write to the outfile.
        if response.status_code != 200:
            # Write to a csv
            out.write(','.join([str(i), '','0','','','0','','','0','']) + '\n')
            # Turn the timer off
            self._timer('off', row_count)
            continue

        # Make results dictionary format
        resp_dict = response.json()
        results = resp_dict['entries']
                    
        # Ensure we have the pids.
        results = [(x['content']['gedcomx']['persons'][0]['id'], x['score']) for x in results]
        track = results + [i]
        
        '''
        This is the command to write to a csv file
        The commented section is for an output where each individual
        has three lines (name, potential pids, match score)
        
        The other code block outputs each person on a single line.
        '''
        
        
        with open(self.outfile, 'a', newline='') as csvFile:
            writer = csv.writer(csvFile)
            for j in range(1):
                writer.writerow([x[j] for x in results])
        csvFile.close()
        '''
        with open(self.outfile, 'a', newline='') as csvFile:
            writer = csv.writer(csvFile)
            #writer.writerow(results)
            writer.writerow(df.iloc[i,:])
            for j in range(2):
                writer.writerow([x[j] for x in results])
            writer.writerow([''])
        csvFile.close()
        '''
        # Append to allresults.
        allresults.append(results)
        tracker.append(track)
        '''     
        # Continue if we have less than 190 ids.
        # FIXME: 180 should prevent us from ever having an issue as long as max_results sits at 10
        # if we change that we should adjust this accordingly, make sure we don't get more than 200
        if sum([len(x) for x in allresults]) <= 190 and i != df.index[-1]:
            print(sum([len(x) for x in allresults]))
            continue

        
        url = 'http://api.familysearch.org/platform/tree/persons?pids={}'.format(','.join([pid for result_list in allresults for pid, score in result_list]))
        response = self._ping_api(url, person_session, verbosity)
            
        # Get the data.
        resp_dict = response.json()
        
        # Loop to get the information.

        # Define an array for all of the info.
        potential_info_lists = [[]]*len(allresults)
        
        for person in resp_dict['persons']:
            for j, result in enumerate(allresults):
                if person['id'] in [x[0] for x in result]:
                    potential_info_lists[j] = potential_info_lists[j] + [person]
                    
        print('\n\n\n', resp_dict['persons'], '\n\n\n',potential_info_lists,'\n\n\n', allresults)
        # FIXME: this block should be replicated by the line below but I don't really understand it so I can't be certain
        # potential_info_lists = [[person for person in resp_dict['persons'] if person in result] for result in allresults]   
        
        family_pids = set()
        parent_pids = []
         Parse the information in a usable way.
        for j, people in enumerate(potential_info_lists):
            for k, tup in enumerate(people):
                print(people)

                person = tup[0]
                person_info_dict = {'pid':person['id'], 'score':tup[1]}
                person_info_dict.update({token:person['display'].get(token, '') for token in ['name', 'birthDate', 'birthPlace', 'deathDate','deathPlace','gender']})
                try:
                    # add spouse
                    if person['id'] == person['display']['familiesAsParent'][0]['parent1']['resourceId']: 
                        person_info_dict['spouse'] = person['display']['familiesAsParent'][0]['parent2'].get('resourceId', '')
                    else:
                        person_info_dict['spouse'] = person['display']['familiesAsParent'][0]['parent1'].get('resourceId', '')
                    if person_info_dict.get('spouse', '') != '':
                        family_pids.add(person_info_dict.get('spouse', ''))
                    # add child ids
                    children = [child['id'] for child in person['display']['familiesAsParent'][0]]
                    person_info_dict['children'] = children
                    family_pids = family_pids.union(set(children))
                except KeyError: # familiesAsParent may not be present
                    pass
                
                try:
                    parents = [person['display']['familiesAsChild'][0].get('parent1',''), person['display']['familiesAsChild'][0].get('parent2','')]
                    parents = [parent for parent in parents if parent != '']
                    person_info_dict['parents'] = parents
                    parent_pids.extend(parents)
                    family_pids = family_pids.union(set(parents))
                except KeyError: # familiesAsChild may not be present
                    pass
                    
                # Loop to get marriage info
                for rel in resp_dict['relationships']:
                    if rel['type'] == 'http://gedcomx.org/Couple' and person['id'] in [rel['person1']['resourceId'], rel['person2']['resourceId']]:
                        person_info_dict['marriageDate'] = rel['facts'][0]['date']['normalized'][0].get('value', '') # Marriage date
                        person_info_dict['marriagePlace'] = rel['facts'][0]['place']['normalized'][0].get('value', '') # Marriage place
                # Gender
                person_info_dict['gender'] = person['display'].get('gender','')

                # Reassign to potential_info_lists
                potential_info_lists[j][k] = person_info_dict
                    
                
        
        # Hit the API to get sibling ids
        # FIXME: This grabbing data for parents is done again in the next loop. We should change that as fewer API calls means less throttling
        for x in range(0, len(parent_pids), 200):
            # Get the data
            url = 'http://api.familysearch.org/platform/tree/persons?pids={}'.format(','.join(parents[x:x+199]))
            response = self._ping_api(url, person_session, verbosity)
            resp_dict = response.json()
            
            # Get all of the associated siblings. 
            # FIXME: this is a very inefficient way of doing this but I don't see how to do it otherwise with the current code structure
            for response_person in resp_dict['persons']:
                for potential_info_list in potential_info_lists:
                    for person_info_dict in potential_info_list:
                        if response_person['id'] in person_info_dict['parents']:
                            try:
                                siblings = [child['resourceId'] for child in response_person['display']['familiesAsParent'][0]['children'] if child['resourceId'] != person_info_dict['pid']]
                                person_info_dict['siblings'] = siblings
                                family_pids = family_pids.union(set(siblings))
                            except KeyError: # in case familiesAsParent is not present
                                pass
        
        # coercing family_pids back to a list for iteration by element order
        family_pids = list(family_pids)
        # Hit the API to scrape family info.
        for j in range(0, len(family_pids), 200):
            # grab the data
            url = 'http://api.familysearch.org/platform/tree/persons?pids={}'.format(','.join(family_pids[j:j+199]))
            response = self._ping_api(url, person_session, verbosity)
            resp_dict = response.json()
            
            # Loop to get the information.
            for response_person in resp_dict['persons']:
                
                response_person_info_dict = {'pid': response_person.get('id','')}
                response_person_info_dict.update({token: response_person['display'].get(token, '') for token in ['name', 'birthDate', 'birthPlace', 'deathDate','deathPlace','gender']})
                
                # Assign to the correct place.
                # FIXME: this seems like it is unnecessarily inefficient but I don't know how to fix it
                for potential_info_list in potential_info_lists:
                    for person_info_dict in potential_info_list: 
                        if response_person_info_dict['pid'] == person_info_dict['spouse']:
                            person_info_dict['spouse'] = response_person_info_dict
                            
                        if response_person_info_dict['pid'] in person_info_dict['children']:
                            for k, pid in enumerate(person_info_dict['children']):
                                if response_person_info_dict['pid'] == pid:
                                    person_info_dict['children'][k] = response_person_info_dict
                                    
                        if response_person_info_dict['pid'] in person_info_dict['parents']:
                            for k, pid in enumerate(person_info_dict['parents']):
                                if response_person_info_dict['pid'] == pid:
                                    person_info_dict['parents'][k] = response_person_info_dict
                                    
                        if response_person_info_dict['pid'] in person_info_dict['siblings']:
                            for k, pid in enumerate(person_info_dict['siblings']):
                                if response_person_info_dict['siblings'] == pid:
                                    person_info_dict['siblings'][k] = response_person_info_dict

        
        # FIXME: I tried to optimize a lot of things so that they work faster
        #       I gave up at this point because I don't want to try to really
        #       undertsand the scoring. I will simply update the values so that
        #       they work wiht the dictionaries instead of lists that I changed


        # Loop over all of the results.
        for potential_info_list in potential_info_lists:
            # Define the total scores and fsids array
            scores = []
            all_fsids = []
            
            # Find the index of the person of interest
            for y in tracker:
                try:
                    if potential_info_list[0][0] in y:
                        loop1 = y[-1]
                except Exception as e:
                    print(e)
                    print(potential_info_list,'\n',y)
                    print(potential_info_lists)
                    return potential_info_lists, potential_info_list, y, tracker
            # Loop over each of the matches and create a match score.
            # Here we define a counter that we use to loop.
            index = 0
            for person in potential_info_list:
            # while index < len(potential_info_list):
                # Reinitialize the variables.
                marriage_date, marriage_place, marriage_date_parents, marriage_place_parents = ['']*4
                fs_name, fs_birthdate, fs_birthplace, fs_deathdate, fs_deathplace = ['']*5
                fs_name_spouse, fs_birthdate_spouse, fs_birthplace_spouse, fs_deathdate_spouse, fs_deathplace_spouse = ['']*5
                fs_name_dad, fs_birthdate_dad, fs_birthplace_dad, fs_deathdate_dad, fs_deathplace_dad = ['']*5
                fs_name_mom, fs_birthdate_mom, fs_birthplace_mom, fs_deathdate_mom, fs_deathplace_mom = ['']*5
                
                # Get the main pid.
                mainid = person['id']
                
                # Get each of the variables we care about, pass if they don't exist.
                fs_name = person['name']
                fs_birthdate = person['birthDate']
                fs_birthplace = person['birthPlace']
                fs_deathdate = person['deathDate']
                fs_deathplace = person['deathPlace']
                
                #Reset all score variables.
                score = [0,'']
                score1 = [0,'']
                score2 = [0,'']
                score3 = [0,'']
                score4 = [0,'']
                mscore1 = [0,'']
                mscore2 = [0,'']
                dscore1 = [0,'']
                dscore2 = [0,'']
                sscore1 = [0,'']
                sscore2 = [0,'']
                mscore, dscore, sscore = ['']*3
                
                # Ensure we have relationships
                if person['spouse'] == '' and person['parents'] == [] and person['children'] == [] and person['siblings'] == []:
                    # Score full name
                    score1 = self._scorename('SelfName', df.name.iloc[loop1], fs_name)
                    
                    # Score birth date and birth place
                    score2 = self._scoreevent('SelfBirth', df.birthDate.iloc[loop1], df.birthPlace.iloc[loop1], fs_birthdate, fs_birthplace)
                    
                    # Tally the score and continue if it is good enough
                    score = [score[0] + score1[0] + score2[0], score[1] + score1[1] + score2[1]]    
                    if score[0] >= 3 and score1[0] >= 1 and score2[0] >= 1:
                        # Score death date and place.
                        score3 = self._scoreevent('SelfDeath', df.deathDate.iloc[loop1], df.deathPlace.iloc[loop1], fs_deathdate, fs_deathplace)
                        
                        # Keep the runing score current
                        score = [score[0] + score3[0],score[1] + score3[1]]
                        
                    # Append to the arrays
                    scores = scores + score
                    all_fsids.append(mainid)
                    
                    # Increment the index
                    continue
    
                # Get the marriage date and place.
                marriage_date = person['marriageDate']
                marriage_place = person['marriagePlace']
                
                # Define arrays for children and sibling names, birth dates, and birth places
                children = []
                children_birthdates = []
                children_birthplaces = []
                children_deathdates = []
                children_deathplaces = []
                siblings = []
                siblings_birthdates = []
                siblings_birthplaces = []
                siblings_deathdates = []
                siblings_deathplaces = []
                
                # Get spouse info if it exists
                if person['spouse'] != '':
                    fs_name_spouse = person['spouse']['name']
                    fs_birthdate_spouse = person['spouse']['birthDate']
                    fs_birthplace_spouse = person['spouse']['birthPlace']
                
                # Children info
                if person['children'] != []:
                    for y in person['children']:
                        children.append(y['name'])
                        children_birthdates.append(y['birthDate'])
                        children_birthplaces.append(y['birthPlace'])
                        children_deathdates.append(y['deathDate'])
                        children_deathplaces.append(y['deathPlace'])  
                
                # Parent info
                for y in person['parent']:
                    if y['gender'] == 'Female':
                        fs_name_mom = y['name']
                        fs_birthdate_mom = y['birthDate']
                        fs_birthplace_mom = y['birthPlace']
                    else:
                        fs_name_dad = y['name']
                        fs_birthdate_dad = y['birthDate']
                        fs_birthplace_dad = y['birthPlace']
                
                # Sibling info.
                if person['siblings'] != []:
                    for y in person[9]:
                        siblings.append(y[1])
                        siblings_birthdates.append(y['birthDate'])
                        siblings_birthplaces.append(y['birthPlace'])
                        siblings_deathdates.append(y['deathDate'])
                        siblings_deathplaces.append(y['deathPlace'])
                        
    
                # Now we will get on to scoring.            
                # Score full name.
                score1 = self._scorename('SelfName', df.name.iloc[loop1], fs_name)
                
                # Score birth date and birth place.
                score2 = self._scoreevent('SelfBirth', df.birthDate.iloc[loop1], df.birthPlace.iloc[loop1], fs_birthdate, fs_birthplace)
                
                # Tally the score and continue if it is good enough.
                score = [score[0] + score1[0] + score2[0], score[1] + score1[1] + score2[1]]    
                if score[0] >= 3 and score1[0] >= 1 and score2[0] >= 1:
                    # Score death date and place.
                    score3 = self._scoreevent('SelfDeath', df.deathDate.iloc[loop1], df.deathPlace.iloc[loop1], fs_deathdate, fs_deathplace)
                    
                    # Keep the runing score current.
                    score = [score[0] + score3[0],score[1] + score3[1]]
        
                    # Score full mother name, mother birth date, and mother birth place.
                    mscore1 = self._scorename('MomName', df.motherName.iloc[loop1], fs_name_mom)
                    mscore2 = self._scoreevent('MomBirth', df.motherBirthDate.iloc[loop1], df.motherBirthPlace.iloc[loop1], fs_birthdate_mom, fs_birthplace_mom)
                    
                    # Score full father name, father birth date, and father birth place.
                    dscore1 = self._scorename('DadName', df.fatherName.iloc[loop1],fs_name_dad)
                    dscore2 = self._scoreevent('DadBirth', df.fatherBirthDate.iloc[loop1], df.fatherBirthPlace.iloc[loop1], fs_birthdate_dad, fs_birthplace_dad)
                    
                    # Tally the score for mother and father.
                    mscore = mscore1[0] + mscore2[0]
                    dscore = dscore1[0] + dscore2[0]
                    
                    # Ensure names score at least a 1 and dates are not missing, 
                    # or that one of the parents scores at least a 1 on name a birth info.
                    if ((mscore1[0] >= 1 and dscore1[0] >= 1) and (df.motherBirthDate.iloc[loop1] == '' or df.fatherBirthDate.iloc[loop1] =='' or fs_birthdate_mom == ''  or fs_birthdate_dad == '')) or ((mscore1[0] >= 1 and mscore2[0] >= 1) or (dscore1[0] >= 1 and dscore2[0] >= 1)):
                        # Give points for the parent info.
                        # Mom is a great match.
                        if mscore >= 10:
                            if dscore >= 10:
                                score = [score[0] + 8, score[1] + 'ParentsPerfect; ']
                            elif dscore >= 5 and dscore < 10:
                                score = [score[0] + 6, score[1] + 'PerfectMomGoodDad; ']
                            elif dscore >= 2 and dscore < 5:
                                score = [score[0] + 3, score[1] + 'PerfectMomOkayDad; ']
                            else:
                                score = [score[0] + 2, score[1] + 'PerfectMom; ']
                                
                        # Mom is a good match.  
                        elif mscore >= 5 and mscore < 10:
                            if dscore >= 10:
                                score = [score[0] + 6, score[1] + 'GoodMomPerfectDad; ']
                            elif dscore >= 5 and dscore < 10:
                                score = [score[0] + 4, score[1] + 'GoodParents; ']
                            elif dscore >= 2 and dscore < 5:
                                score = [score[0] + 2, score[1] + 'GoodMomOkayDad; ']
                            else:
                                score = [score[0] + 1, score[1] + 'GoodMom; ']
                                
                        # Mom is an okay match.
                        elif mscore >= 2 and mscore < 5:
                            if dscore > 10:
                                score = [score[0] + 3, score[1] + 'OkayMomPerfectDad; ']
                            elif dscore >= 5 and dscore < 10:
                                score = [score[0] + 2, score[1] + 'OkayMomGoodDad; ']
                            elif dscore >= 2 and dscore < 5:
                                score = [score[0] + .5, score[1] + 'OkayParents; ']
                            
                        # Mom is not a good match.
                        else:
                            if dscore > 10:
                                score = [score[0] + 2, score[1] + 'PerfectDad; ']
                            elif dscore > 5 and dscore <= 10:
                                score = [score[0] + 1, score[1] + 'GoodDad; ']
                            elif dscore<=2 and [fs_birthdate_mom, fs_birthplace_mom, fs_birthplace_dad, fs_birthdate_dad] != ['','','',''] and [df.fatherBirthPlace.iloc[loop1], df.fatherBirthDate.iloc[loop1], df.motherBirthPlace.iloc[loop1], df.motherBirthDate.iloc[loop1]] != ['','','','']:
                                score = [score[0] -2, score[1] + 'BadParents; ']
       
                    else:
                        pass
                    
                    
                    # Score the spouse if the spouse name is not missing.
                    if df.spouseName.iloc[loop1] != '':
                        # Score full spouse name, spouse birth date, and spouse birth place.
                        sscore1 = self._scorename('SpouseName', df.spouseName.iloc[loop1],fs_name_spouse)
                        sscore2 = self._scoreevent('SpouseBirth', df.spouseBirthDate.iloc[loop1], df.spouseBirthPlace.iloc[loop1], fs_birthdate_spouse, fs_birthplace_spouse)
                        
                        # Tally the score.
                        sscore = sscore1[0] + sscore2[0]
                        
                        # Give points if both the name and birth scored at least 1.
                        if sscore >= 2 and sscore1[0] >= 1 and sscore2[0] >= 1:
                            # Give points for spouse info
                            # Perfect Spouse
                            if sscore > 10:
                                score = [score[0] + 3, score[1] + 'PerfectSpouse; ']
                                
                            # Good Spouse
                            elif sscore > 5 and sscore <= 10:
                                score = [score[0] + 1.5, score[1] + 'GoodSpouse; ']
              
                            # Okay Spouse
                            elif sscore > 2 and sscore <= 5:
                                 score = [score[0] + .5, score[1] + 'OkaySpouse; ']
                               
                            else:
                                pass
                                
                            #Give points for marriage
                            score4 = self._scoreevent('SelfMarriage', df.marriageDate.iloc[loop1], df.marriagePlace.iloc[loop1], marriage_date, marriage_place)
                            
                            # Increment the score.
                            score = [score[0] + score4[0], score[1] + score4[1]]
                            
                else:
                    pass
                
                
                # Score the kids and siblings if we have info.            
                # Replace birthyears with a 9999 if they are blank.
                for x in range(0,len(siblings_birthdates)):
                    if not re.search(r'[0-9][0-9][0-9][0-9]', siblings_birthdates[x]):
                        siblings_birthdates[x] = '9999'
                        
                for x in range(0,len(children_birthdates)):
                    if not re.search(r'[0-9][0-9][0-9][0-9]', children_birthdates[x]):
                        children_birthdates[x] = '9999'
                
                
                # Get the birthyears for each sibling to index the other strings.
                if siblings_birthdates != []:
                    for x in siblings_birthdates:
                        sib_years = [int(re.search(r'[0-9][0-9][0-9][0-9]', x).group()) for x in siblings_birthdates]                    
                    
                    # Order each array.
                    siblings = [x for (y,x) in sorted(zip(sib_years,siblings))]
                    siblings_birthdates = [x for (y,x) in sorted(zip(sib_years,siblings_birthdates))]
                    siblings_birthplaces = [x for (y,x) in sorted(zip(sib_years,siblings_birthplaces))]
                    siblings_deathdates = [x for (y,x) in sorted(zip(sib_years,siblings_deathdates))]
                    siblings_deathplaces = [x for (y,x) in sorted(zip(sib_years,siblings_deathplaces))]
                    sib_years = sorted(sib_years)
                
                # Get the birthyears for each child to index the other strings.
                if children_birthdates != []:
                    child_years = [int(re.search(r'[0-9][0-9][0-9][0-9]',x).group()) for x in children_birthdates]                    
                    
                    # Order each array.
                    children = [x for (y,x) in sorted(zip(child_years,children))]
                    children_birthdates = [x for (y,x) in sorted(zip(child_years,children_birthdates))]
                    children_birthplaces = [x for (y,x) in sorted(zip(child_years,children_birthplaces))]
                    children_deathdates = [x for (y,x) in sorted(zip(child_years,children_deathdates))]
                    children_deathplaces = [x for (y,x) in sorted(zip(child_years,children_deathplaces))]
                    child_years = sorted(child_years)
                
                # Replace birthyears with a 9999 if they are blank.
                for x in range(0,len(df.sibdates.iloc[loop1])):
                    if not re.search(r'[0-9][0-9][0-9][0-9]', df.sibdates.iloc[loop1][x]):
                        df.sibdates.iloc[loop1][x] = '9999'
                        
                for x in range(0,len(df.kiddates.iloc[loop1])):
                    if not re.search(r'[0-9][0-9][0-9][0-9]', df.kiddates.iloc[loop1][x]):
                        df.kiddates.iloc[loop1][x] = '9999'
                
                # Get the birth years for our list of siblings to index.
                if df.sibdates.iloc[loop1] != []:
                    sib_years1 = [int(re.search(r'[0-9][0-9][0-9][0-9]',x).group()) for x in df.sibdates.iloc[loop1]]                    
                else:
                    sib_years1 = []
    
                # Order each array.
                if sib_years1 != []:
                    siblings1 = [x for (y,x) in sorted(zip(sib_years1, df.sibs.iloc[loop1]))]
                    siblings_birthdates1 = [x for (y,x) in sorted(zip(sib_years1, df.sibdates.iloc[loop1]))]
                    siblings_birthplaces1 = [x for (y,x) in sorted(zip(sib_years1, df.sibplaces.iloc[loop1]))]
                    sib_years1 = sorted(sib_years1)
                else:
                    siblings1 = df.sibs.iloc[loop1]
                    siblings_birthdates1 = df.sibdates.iloc[loop1]
                    siblings_birthplaces1 = df.sibplaces.iloc[loop1]
    
                # Get the birthyears for our list of child to index the other strings.
                if df.kiddates.iloc[loop1] != []:
                    child_years1 = [int(re.search(r'[0-9][0-9][0-9][0-9]',x).group()) for x in df.kiddates.iloc[loop1]]                    
                else:
                    child_years1 = []
                
                # Order each array using child years if it exists.
                if child_years1 != []:
                    children1 = [x for (y,x) in sorted(zip(child_years1, df.kids.iloc[loop1]))]
                    children_birthdates1 = [x for (y,x) in sorted(zip(child_years1, df.kiddates.iloc[loop1]))]
                    children_birthplaces1 = [x for (y,x) in sorted(zip(child_years1, df.kidplaces.iloc[loop1]))]
                    child_years1 = sorted(child_years1)
                else:
                    children1 = df.kids.iloc[loop1]
                    children_birthdates1 = df.kiddates.iloc[loop1]
                    children_birthplaces1 = df.kidplaces.iloc[loop1]
    
                # Define a variable to check the index and the score variable.
                sib_check = -1
                kid_check = -1
                
                # Fix if there is a problem.
                if siblings1 == []:
                    siblings1 == ['']
                if siblings == []:
                    siblings == ['']
    
                # Loop over our siblings.
                for x in range(0,len(siblings1)):
                    # Loop over the Family Search siblings.
                    for y in range(0,len(siblings)):
                        # Check the first name.
                        if siblings1[x].split() == [] or siblings[y].split() == []:
                            jw = 0
                        elif siblings1[x].split()[0] == '' or siblings[y].split()[0] == '':
                            jw = 0
                        else:
                            jw = jaro_distance(siblings1[x].split()[0],siblings[y].split()[0])
                        
                        if jw >= .9:
                            # Continue only if the index is correct.
                            if y > sib_check:
                                # If either birthdate is blank, give a lower score and continue.
                                try:
                                    if siblings_birthdates1[x] == '' or siblings_birthdates[y] == '':
                                        sib_check = y
                                        score = [score[0] + .5, score[1] + 'Sibling Just Order; ']
                                        continue
                                
                                    # If the birthyear is close enough give a point and check exact match.
                                    elif abs(sib_years1[x] - sib_years[y]) <= 2:
                                        sib_check = y
                                        # Check exact birthdate and place.
                                        score_check = self._scoreevent('Sibling', siblings_birthdates1[x], siblings_birthplaces1[x], siblings_birthdates[y], siblings_birthplaces[y])
                                        
                                        if score_check[0] >= 7:
                                            score = [score[0] + 3, score[1] + 'Perfect Sibling; ']
                                        
                                        elif score_check[0] >= 4:
                                            score = [score[0] + 2, score[1] + 'Sibling Bonus; ']
                                        
                                        else:
                                            score = [score[0] + 1, score[1] + 'Sibling Order Year; ']
                                        
                                        continue
                                    
                                except KeyboardInterrupt:
                                    sys.exit(1)
                                    
                                except:
                                    sib_check = y
                                    score = [score[0] + .5, score[1] + 'Sibling Just Order; ']
                                    continue
                                
                # Reset the check score.
                score_check = 0
                
                # Fix if there is a problem.
                if children1 == []:
                    children1 == ['']
                if children == []:
                    children == ['']
                    
                # Loop over our siblings.
                for x in range(0,len(children1)):
                    # Loop over the Family Search siblings.
                    for y in range(0,len(children)):
                        # Check the first name.
                        if children1[x].split() == [] or children[y].split() == []:
                            jw = 0
                        elif children1[x].split()[0] == '' or children[y].split()[0] == '':
                            jw = 0
                        else:
                            jw = jaro_distance(children1[x].split()[0], children[y].split()[0])
                        
                        if jw >= .9:
                            # Continue only if the index is correct.
                            if y > kid_check:
                                # If either birthdate is blank, give a lower score and continue.
                                try:
                                    if children_birthdates1[x] == '' or children_birthdates[y] == '':
                                        kid_check = y
                                        score = [score[0] + .5, score[1] + 'Child Just Order; ']
                                        continue
                                
                                    # If the birthyear is close enough give a point and check exact match.
                                    elif abs(child_years1[x] - child_years[y]) <= 2:
                                        kid_check = y
                                        # Check exact birthdate and place.
                                        score_check = self._scoreevent('Child', children_birthdates1[x], children_birthplaces1[x], children_birthdates[y], children_birthplaces[y])
                                        
                                        if score_check[0] >= 7:
                                            score = [score[0] + 3, score[1] + 'Perfect Child; ']
                                        
                                        elif score_check[0] >= 4:
                                            score = [score[0] + 2, score[1] + 'Child Bonus; ']
                                        
                                        else:
                                            score = [score[0] + 1, score[1] + 'Child Order Year; ']
                                        
                                        continue
                                
                                except KeyboardInterrupt:
                                    sys.exit(1)
                                
                                except:
                                    kid_check = y
                                    score = [score[0] + .5, score[1] + 'Child Just Order; ']
                                    continue
                            
    
                # Append to the arrays.
                scores = scores + score
                all_fsids.append(mainid)
                
                # Increment the index.
                index += 1
    
            # Make sure all_fsids is at least length 3.
            while len(all_fsids) < 3:
                all_fsids.append('')
                
            # Define the write varible.
            write = []
            ind = 0
            for fsid in all_fsids:
                write.append(fsid)
                try:
                    write.append(str(scores[ind]))
                except:
                    write.append('0')
                ind += 1
                try:
                    write.append(str(scores[ind]))
                except:
                    write.append('')
                ind += 1
            
            print('got to writing')
            # Write to a csv.
            while True:
                try:
                    self._write_csv(str(df['index'].iloc[loop1]) + ',' + ','.join(write) + '\n')
                    break
                except:
                    sleep(10)
                    pass
            
            # Print out the score.
            if report:
                for x, y in enumerate(scores):
                    if re.search('[0-9]',str(y)):
                        print(str(y) + ': ' + scores[x+1][:-1])     
                print('\n')
            
        # Turn the timer off.
        self._timer('off', row_count=row_count, numobs=len(allresults))
    
        # Increment loop.

        # Reset the lists.
        allresults = []
        tracker = []
            
    # Write the finished file.
    self._finished()
    '''
    print('\nComplete!')


def _ping_api(self, url, session, verbosity):
    '''
    this function does the actual interaction the site
    '''
    
    SERVER_WAIT = 3
    MESSAGES = ['Cool your jets, bro.',
                'Slow your roll. The server can\'t keep up.',
                'Hey, take it easy there.',
                'Hey, have some pity on the server here.',
                'You think you can just make all the server requests you want, huh?',
                'Dude, let it rest for a bit, OK?',
                'We gotta take a break here...',
                'Make america great again!'] 
    
    for _ in range(5):
        response = session.get(url)      
        if verbosity > 3:
            print(f'The token being used is: {self.token}')
            print(response.headers)
        elif verbosity > 2:
            print(f'HTTP response status: {response.status_code}\n')
        
        if response.status_code in [200, 204]:
            break
        elif response.status_code == 401:
            self.token = self.Authenticate()
            continue
        elif response.status_code == 429:
            wait = int(response.headers['Retry-After']) * 1.1
            if verbosity > 0:
                print('Throttled, waiting {0: .1f} seconds! {1}'.format(wait, MESSAGES[np.random.randint(0, len(MESSAGES))]))
            sleep(wait)
        elif response.status_code >= 500:
            print('\n\n\nError:', response.status_code, '\n')
            sleep(SERVER_WAIT)
        else:
            print('Error:', response.status_code, '\n\n\n')
            print(url)
            print(response.headers)
            print(response.json())

    
    return response


def _check_start(df, outfile):
    '''
    this function checks the outfile to see where to restart after breaking
    '''
    
    # Check the output file.
    try:
        output = pd.read_csv(outfile, header=None)
        lastid = output.index.max()
    except (FileNotFoundError, EmptyDataError): # empty or non-existent file
        lastid = -1
    
    # Drop anything before the last id.
    return df.loc[df.index > lastid]


def _scoring():
    '''
    this function is the comparative advantage over the familysearch results
    dry. At least it was before they updated it. They may be doing a better job
    than they were before. As of 5 June 2019 we need to compare results to see
    which score we are more confident in
    '''

# a test case to check to see that things are working properly
if __name__ == '__main__':
    
    import os
    import sys

    sys.path.append(r'R:\JoePriceResearch\Python\Anaconda3\Lib\site-packages')

    os.chdir(r"R:\JoePriceResearch\Python\all_code")
    from FamilySearch1 import FamilySearch
    
    #fs = FamilySearch('bbranchf', 'chimps58', r'R:\JoePriceResearch\Python\all_code\FamilySearch1\test_data')
    fs = FamilySearch('laren.edwards', 'ledward5', r'R:\JoePriceResearch\Python\all_code\FamilySearch1\test_data')
    fs.infile = 'find_test_catholic.csv'
    fs.outfile = 'find_test_out.csv'
    
    '''
    The CSV open function below is just a lazy way to clear the file
    if you do not wish to append to previous information.
    '''
    '''
    with open(fs.outfile, 'w', newline='') as csvFile:
            writer = csv.writer(csvFile)
    csvFile.close()
    #'''
    
    '''
    Runs the FindPerson function for each row of the csv
    '''
    out = fs.FindPerson(names={}, verbosity=4)

'''
def _make_col_names(df):
    names_dict = {}
    for i, c in enumerate(df.columns):
        if re.search('.*(?:(?:=pr_)?(?:=[Bb]ir(?:th)?)|(?:=[Cc]hristen(?:ing)?))(?:=[Pp]lace)', c, flags=re.IGNORECASE):
            names_dict[i] = 'BirthLikePlace'
        elif re.search('.*(?:(?:=pr_)?(?:=[Bb]ir(?:th)?)|(?:=[Cc]hristen(?:ing)?))(?:=[Dd]ate)', c, flags=re.IGNORECASE):
            names_dict[i] = 'BirthLikeDate'
        elif 
'''        
            

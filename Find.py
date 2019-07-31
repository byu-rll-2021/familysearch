# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 17:52:08 2017
Updated on 4/27/2018 by Tanner S Eastmond.

@author: tannerse
"""
import sys
sys.path.append(r'R:\JoePriceResearch\Python\Anaconda3\Lib\site-packages')
import pandas as pd
import numpy as np
import requests
from time import sleep
import re
from jellyfish import jaro_distance

MESSAGES = ['Cool your jets, bro.', 'Slow your roll. The server can\'t keep up.', 'Hey, take it easy there.',
            'Hey, have some pity on the server here.', 'You think you can just make all the server requests you want, huh?',
            'Dude, let it rest for a bit, OK?', 'We gotta take a break here...','Make america great again!']


def Find(self, names=None, report=False, token=None, token_report=True):
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
    '''
    # Check the output file.
    try:
        output = pd.read_csv(self.outfile, header=None)
        lastid = output.index.max()
    except:
        lastid = -1
        pass
    
    # use the token passed in manually instead of the default
    if token is not None:
        self.token = token
    
    # Make a list of necessary variables.
    varlist = ['index', 'id', 'name', 'gender', 'birthDate', 'birthPlace', 
               'christeningDate', 'christeningPlace', 'deathDate', 'deathPlace', 
               'burialDate', 'burialPlace', 'marriageDate', 'marriagePlace', 
               'mid', 'motherName', 'mgender', 'motherBirthDate', 'motherBirthPlace', 
               'mcdate', 'mcplace', 'motherDeathDate', 'motherDeathPlace', 'mbudate', 
               'mbuplace', 'motherMarriageDate', 'motherMarriagePlace', 'did', 
               'fatherName', 'dgender', 'fatherBirthDate', 'fatherBirthPlace', 
               'dcdate', 'dcplace', 'fatherDeathDate', 'fatherDeathPlace', 
               'dbudate', 'dbuplace', 'fatherMarriageDate', 'fatherMarriagePlace', 
               'sid', 'spouseName', 'sgender', 'spouseBirthDate', 'spouseBirthPlace', 
               'scdate', 'scplace', 'spouseDeathDate', 'spouseDeathPlace', 'sbudate', 
               'sbuplace', 'spouseMarriageDate', 'spouseMarriagePlace', 'kids', 'kiddates', 
               'kidplaces', 'kidgenders', 'sibs', 'sibdates', 'sibplaces', 'sibgenders', 
               'resdate', 'resplace']
    
    # Read in the input file.
    if names is None:
        df = pd.read_csv(self.infile, header=None)
    else:
        try:
            df = pd.read_csv(self.infile)
        except UnicodeDecodeError:
            print(sys.exc_info()[0])
            print('UnicodeDecodeError : the function will try with a',
                  'different encoding that may or may not work')
            df = pd.read_csv(self.infile, encoding='latin1')
    
    # Define the names dictionary.
    if names is None:
        names = {0:'index', 1:'id', 2:'name', 3:'gender', 4:'birthDate', 5:'birthPlace',
                 6:'christeningDate', 7:'christeningPlace', 8:'deathDate', 9:'deathPlace', 10:'burialDate',
                 11:'burialPlace', 12:'marriageDate', 13:'marriagePlace', 14:'mid', 15:'motherName',
                 16:'mgender', 17:'motherBirthDate', 18:'motherBirthPlace', 19:'mcdate', 20:'mcplace',
                 21:'motherDeathDate', 22:'motherDeathPlace', 23:'mbudate', 24:'mbuplace', 25:'motherMarriageDate',
                 26:'motherMarriagePlace', 27:'did', 28:'fatherName', 29:'dgender', 30:'fatherBirthDate', 
                 31:'fatherBirthPlace', 32:'dcdate', 33:'dcplace', 34:'fatherDeathDate', 35:'fatherDeathPlace', 
                 36:'dbudate', 37:'dbuplace', 38:'fatherMarriageDate', 39:'fatherMarriagePlace',
                 40:'sid', 41:'spouseName', 42:'sgender', 43:'spouseBirthDate', 
                 44:'spouseBirthPlace', 45:'scdate', 46:'scplace', 47:'spouseDeathDate', 48:'spouseDeathPlace', 
                 49:'sbudate', 50:'sbuplace', 51:'spouseMarriageDate', 52:'spouseMarriagePlace', 53:'kids',
                 54:'kiddates', 55:'kidplaces', 56:'kidgenders', 57:'sibs', 
                 58:'sibdates', 59:'sibplaces', 60:'sibgenders', 61:'resdate',
                 62:'resplace'}
    
    if names is not None:
        with open(self.outfile[:-4] + '_names_dict.txt', 'w') as names_dict:
            names_dict.write(str(names))
    
    # Rename the columns as specified.
    df = df.rename(columns=names)
    
    # Drop anything before the last id.
    df = df.loc[df.index > lastid]
    
    # Get the number of rows.
    row_count = len(df)
    
    # Make sure we have all of the necessary columns.
    for x in varlist:
        if x not in df.columns:
            df[x] = ''
            
    # Make all columns string.
    for x in df.columns:
        df[x] = df[x].astype(str)
        
        # Fill with '' rather than nan.
        df.loc[df[x] == 'nan', x] = ''
        df[x] = df[x].fillna('')
        
        # Clean out decimals if dates.
        if re.search('Date',x):
            df[x] = df[x].str.replace('\.[0-9]+','')

    # Make each of the sibling and child variables lists.
    for x in ['kids', 'kiddates', 'kidplaces', 'kidgenders', 'sibs', 'sibdates', 'sibplaces', 'sibgenders']:
        df[x] = df[x].str.split(';')
        
    # Clean the data.
    for x in df.columns:
        try:
            # Replace double spaces in names.
            if re.search('[Nn]ame', x):
                df[x] = df[x].str.replace('[\s]+', ' ')
                
            # Replace colons or semicolons in places.
            elif re.search('[Pp]lace', x) and x not in ['kidplaces', 'sibplaces']:
                df[x] = df[x].str.replace(':|;', ', ')
        except:
            pass

    # Loop over rows in the dataframe.
    loop = 0
    allresults = []
    tracker = []
    while(True):
        # Turn on the timer.
        if allresults == []:
            self._timer('on')                
        
        
        # Stop when we hit the end.
        if loop >= row_count:
            break
                
        
        # Reinitialize the name variables we need to use.
        firstname, middlename, lastname, dadfirst, dadlast, dadmiddle, momfirst, mommiddle, momlast, wifefirst, wifemiddle, wifelast, husbandfirst, husbandmiddle, husbandlast = [''] * 15      


        # Clean all of the names.
        firstname, middlename, lastname, suffix = self._parse_name(df.name.iloc[loop])
        momfirst, mommiddle, momlast, suffix = self._parse_name(df.motherName.iloc[loop])
        dadfirst, dadmiddle, dadlast, suffix = self._parse_name(df.fatherName.iloc[loop])

        # Check the gender of the person and parse the spouse name.
        if df.gender.iloc[loop][:1].lower() == 'm':
            wifefirst, wifemiddle, wifelast, suffix = self._parse_name(df.spouseName.iloc[loop])
        else:
            husbandfirst, husbandmiddle, husbandlast, suffix = self._parse_name(df.spouseName.iloc[loop])
            
        # Kill the last name if it is a married name.
        if wifelast == lastname and wifelast != '' and df.gender.iloc[loop].lower() in ['male', 'm']:
            wifelast = ''
        elif husbandlast == lastname and husbandlast != '' and df.gender.iloc[loop].lower() in ['female', 'f']:
            lastname = ''

        # Use the dad's or mom's lastname if the name is blank.
        if df.name.iloc[loop] == '' and dadlast != '':
            lastname = dadlast
        elif df.name.iloc[loop] == '' and dadlast == '' and momlast != '':
            lastname = momlast
        elif df.name.iloc[loop] == '' and dadlast == '' and momlast == '':
            lastname = 'Unknown'
            

        # Form the search query.
        search = ''
        df['givenName'] = ''
        df['surname'] = ''
        for x in df.columns:
            # Filter for the search columns.
            if x in ['givenName', 'surname', 'gender', 'birthDate', 'birthPlace', 'christeningDate',
                     'christeningPlace','deathDate', 'deathPlace','burialDate', 
                     'burialPlace', 'marriageDate', 'marriagePlace'] or re.search('mother|father|spouse', str(x)):
                # Check if it is missing.
                if not pd.isnull(df[x].iloc[loop]) and df[x].iloc[loop] != '.' and df[x].iloc[loop] != '' and x == 'gender':
                    if df[x].iloc[loop].lower().strip() in ['male', 'm']:
                        # Append to the search string.
                        search = search + x + ':male+'
                    else:
                        # Append to the search string.
                        search = search + x + ':female+'
                        
                elif firstname != '.' and firstname != '' and x == 'givenName':
                    # Append to the search string.
                    search = search + x + ':"{}"~+'.format(re.sub(' ', '+', (firstname + ' ' + middlename).strip()))
                
                elif lastname != '.' and lastname != '' and x == 'surname':
                    # Append to the search string.
                    search = search + x + ':"{}"~+'.format(re.sub(' ', '+', lastname))
                
                elif not pd.isnull(df[x].iloc[loop]) and df[x].iloc[loop] != '.' and df[x].iloc[loop] != '':
                    # Append to the search string.
                    search = search + x + ':"{}"~+'.format(re.sub(' ', '+', df[x].iloc[loop]))
                    
        
        # Clean off the last plus from search.
        search = search[:-1]
        
        # Make the search request.
        check = 0
        if report:
            print(search)
        while True:
            # Query the API.
            try:
                #print(f'The key being used is: {self.key}')
                #print('http://api.familysearch.org/platform/tree/search?q={}'.format(search),'\n')
                pull = requests.get('http://api.familysearch.org/platform/tree/search?q={}'.format(search), 
                        headers={'Authorization': 'Bearer %s' %(self.token), 'Accept':'application/json'})
                #print(pull.status_code)
                #print(pull.headers)
            except:
                print('Struggling to access R-Drive...')
                sleep(10)
                
            if report:
                print('HTTP response status: ' + str(pull.status_code) + '\n')

            # Continue until we get a valid response in case we are throttled.
            if pull.status_code != 200 and pull.status_code != 204 and pull.status_code != 401:
                if pull.status_code == 429 and report:
                    wait = (int(pull.headers['Retry-After'])*1.1)
                    print('Throttled, waiting {0: .1f} seconds! {1}'.format(wait, MESSAGES[np.random.randint(0, len(MESSAGES))]))
                    sleep(wait)
                if pull.status_code == 400:
                    check += 20
                if pull.status_code == 500:
                    print(pull.headers)
                    check += 5
                if check >= 100:
                    break
            elif pull.status_code == 401:
                self.token = self.Authenticate()
            else:
                break

        # If there are no search results, write to the outfile.
        if pull.status_code == 204 or pull.status_code == 400 or pull.status_code == 500:
            # Write to a csv.
            while True:
                try:
                    self._write_csv(str(df['index'].iloc[loop]) + ',' + ','.join(['','0','','','0','','','0','']) + '\n')
                    break
                except:
                    sleep(10)
                    pass
                
            # Turn the timer off.
            self._timer('off', row_count)
            
            # Increment the loop and continue.
            loop += 1
            continue
        
        
        # Get the text of the search results.
        text = ''
        text = pull.json()


        # Clean the main person's dates.
        bday, bmonth, byear = self._parse_date(df.birthDate.iloc[loop])
        dday, dmonth, dyear = self._parse_date(df.deathDate.iloc[loop]) 
        
        """ # EDIT : 7 Aug 2018 we get throttled anyways so we may as well
            loop through all of the results it may end up making the code faster
        # Automatically keep the first three results.
        results = text['entries'][0:3]
        
        # Check if any search results have an exact match on birthday to keep them.
        if bday != '' and bmonth != '' and byear != '':
            for x in text['entries'][3:]:
                # Initialize the variables.
                bday1, bmonth1, byear1 = ['']*3
                
                # Parse the birth date.
                try:
                    bday1, bmonth1, byear1 = self._parse_date(x['content']['gedcomx']['persons'][0]['display']['birthDate'])
                except:
                    pass
                
                # Check if they are equal and keep the result.
                if bday == bday1 and bmonth == bmonth1 and byear == byear1:
                    results.append(x)
        """
        results = text['entries'][0:15]
                    
        # Ensure we have the pids.
        results = [x['content']['gedcomx']['persons'][0]['id'] for x in results]
        track = results + [loop]
                    
        # Append to allresults.
        allresults.append(results)
        tracker.append(track)
        
        # Continue if we have less than 185 ids.
        if sum([len(x) for x in allresults]) < 185 and loop + 1 < len(df):
            #print(sum([len(x) for x in allresults]))
            loop += 1
            continue

    
        # Define an array for all of the info.
        info1 = [[]]*len(allresults)
        
        # Define the search term.
        par = []
        for x in allresults:
            #print(len(x))
            par = par + x
        
        while True:
            # Query the API.
            try:
                #print(par==allresults)
                #print(len(allresults))
                #print(len(par))
                pull = requests.get('http://api.familysearch.org/platform/tree/persons?pids={}'.format(','.join(par)), 
                        headers={'Authorization': 'Bearer %s' %(self.token), 'Accept':'application/json'})
                #print(pull.status_code)
                #print(pull.headers)
            except:
                print('Struggling to access R-Drive...')
                sleep(10)

            # Continue until we get a valid response in case we are throttled.
            if pull.status_code != 200 and pull.status_code != 401: 
                sleep(10)
            elif pull.status_code == 401:
                self.token = self.Authenticate()
            else:
                break
            
        # Get the text.
        text = ''
        text = pull.json()
        
        # Loop to get the information.
        for x in text['persons']:
            for y, z in enumerate(allresults):
                if x['id'] in z:
                    info1[y] = info1[y] + [x]
                
        # Parse the information in a usable way.
        for i, x in enumerate(info1):
            for z, y in enumerate(x):
                # Define an empty list.
                list1 = []
                
                # Get each of the variables we care about, pass if they don't exist.
                try:
                    list1 = list1 + [y['id']] # Pid
                except:
                    list1 = list1 + ['']
                try:
                    list1 = list1 + [y['display']['name']] # Name
                except:
                    list1 = list1 + ['']
                try:
                    list1 = list1 + [y['display']['birthDate']] # Birth date
                except:
                    list1 = list1 + ['']
                try:
                    list1 = list1 + [y['display']['birthPlace']] # Birth place
                except:
                    list1 = list1 + ['']
                try:
                    list1 = list1 + [y['display']['deathDate']] # Death date
                except:
                    list1 = list1 + ['']
                try:
                    list1 = list1 + [y['display']['deathPlace']] # Death place
                except:
                    list1 = list1 + ['']
                try:
                    if y['id'] == y['display']['familiesAsParent'][0]['parent1']['resourceId']: # Spouse pid
                        list1 = list1 + [y['display']['familiesAsParent'][0]['parent2']['resourceId']] 
                    else:
                        list1 = list1 + [y['display']['familiesAsParent'][0]['parent1']['resourceId']]
                except:
                    list1 = list1 + ['']
                try:
                    list2 = []
                    for pid in y['display']['familiesAsParent'][0]['children']: # Children pids
                        list2 = list2 + [pid['resourceId']]
                    list1.append(list2)
                except:
                    list1.append([])
                try:
                    if 'parent1' in y['display']['familiesAsChild'][0].keys() and 'parent2' in y['display']['familiesAsChild'][0].keys(): # Parent pids
                        list1.append([y['display']['familiesAsChild'][0]['parent1']['resourceId'], y['display']['familiesAsChild'][0]['parent2']['resourceId']]) 
                    elif 'parent1' in y['display']['familiesAsChild'][0].keys():
                        list1.append([y['display']['familiesAsChild'][0]['parent1']['resourceId']]) 
                    elif 'parent2' in y['display']['familiesAsChild'][0].keys():
                        list1.append([y['display']['familiesAsChild'][0]['parent2']['resourceId']]) 
                    else:
                        list1.append([])
                except:
                    list1.append([])
                    
                # Make an empty list for siblings.
                list1.append([])
                
                # Loop to get marriage info.
                list1.append('')
                list1.append('')
                for rel in text['relationships']:
                    if rel['type'] == 'http://gedcomx.org/Couple' and list1[0] in [rel['person1']['resourceId'], rel['person2']['resourceId']]:
                        try:
                            list1[10] = rel['facts'][0]['date']['normalized'][0]['value'] # Marriage date
                        except:
                            pass
                        try:
                            list1[11] = rel['facts'][0]['place']['normalized'][0]['value'] # Marriage date
                        except:
                            pass
                      
                # Gender
                try:
                    list1 = list1 + [y['display']['gender']] # Gender
                except:
                    list1 = list1 + ['']
                                            
                # Reassign to info1.
                info1[i][z] = list1
        
        
        # Make a list of parent ids to hit the API and get sibling ids.
        parents = []
        for i, x in enumerate(info1):
            for z, y in enumerate(x):
                if len(y[8]) > 0:
                    parents.append(y[8][0])
        
        
        # Hit the API to get sibling ids.
        for x in range(0, len(parents), 200):
            while True:
                # Query the API.
                try:
                    #print(parents[x:x+199])
                    pull = requests.get('http://api.familysearch.org/platform/tree/persons?pids={}'.format(','.join(parents[x:x+199])), 
                            headers={'Authorization': 'Bearer %s' %(self.token), 'Accept':'application/json'})
                except:
                    print('Struggling to access R-Drive...')
                    sleep(10)
    
                # Continue until we get a valid response in case we are throttled.
                if pull.status_code != 200 and pull.status_code != 401: 
                    sleep(10)
                elif pull.status_code == 401:
                    self.token = self.Authenticate()
                else:
                    break
            
            # Get the text.
            text = ''
            text = pull.json()
            
            # Get all of the associated siblings.
            for a in text['persons']:
                for i, x in enumerate(info1):
                    for z, y in enumerate(x):
                        if a['id'] in y[8]:
                            list2 = []
                            try:
                                for pid in a['display']['familiesAsParent'][0]['children']: # Sibling pids
                                    if y[0] != pid['resourceId']:
                                        list2 = list2 + [pid['resourceId']]
                            except KeyError:
                                return text, a, info1, i, x, z, y, a['id'] 
                            y[9] = list2
                
        
        # Get all of the family ids in one place to scrape.
        family = []
        for i, x in enumerate(info1):
            for z, y in enumerate(x):
                if y[6] != '':
                    family.append(y[6])
                if len(y[7]) > 0:
                    for pid in y[7]:
                        family.append(pid)
                if len(y[8]) > 0:
                    for pid in y[8]:
                        family.append(pid)
                if len(y[9]) > 0:
                    for pid in y[9]:
                        family.append(pid)        
        

        # Hit the API to scrape family info.
        for x in range(0, len(family), 200):
            while True:
                # Query the API.
                try:
                    #print(family[x:x+199])
                    #print(len(family[x:x+199]))
                    pull = requests.get('http://api.familysearch.org/platform/tree/persons?pids={}'.format(','.join(family[x:x+199])), 
                            headers={'Authorization': 'Bearer %s' %(self.token), 'Accept':'application/json'})
                except:
                    print('Struggling to access R-Drive...')
                    sleep(10)                    
    
                # Continue until we get a valid response in case we are throttled.
                if pull.status_code != 200 and pull.status_code != 401: 
                    sleep(10)
                elif pull.status_code == 401:
                    self.token = self.Authenticate()
                else:
                    break
            
            # Get the text.
            text = ''
            text = pull.json()
            
            # Loop to get the information.
            for a in text['persons']:
                # Define an empty list.
                list1 = []
                
                # Get each of the variables we care about, pass if they don't exist.
                try:
                    list1 = list1 + [a['id']] # Pid
                except:
                    list1 = list1 + ['']
                try:
                    list1 = list1 + [a['display']['name']] # Name
                except:
                    list1 = list1 + ['']
                try:
                    list1 = list1 + [a['display']['birthDate']] # Birth date
                except:
                    list1 = list1 + ['']
                try:
                    list1 = list1 + [a['display']['birthPlace']] # Birth place
                except:
                    list1 = list1 + ['']
                try:
                    list1 = list1 + [a['display']['deathDate']] # Death date
                except:
                    list1 = list1 + ['']
                try:
                    list1 = list1 + [a['display']['deathPlace']] # Death place
                except:
                    list1 = list1 + ['']
                try:
                    list1 = list1 + [a['display']['gender']] # Gender
                except:
                    list1 = list1 + ['']
                    
                # Assign to the correct place.
                for i, x in enumerate(info1):
                    for z, y in enumerate(x): 
                        if list1[0] == y[6]:
                            y[6] = list1
                        if list1[0] in y[7]:
                            for pid in range(len(y[7])):
                                if list1[0] == y[7][pid]:
                                    y[7][pid] = list1
                        if list1[0] in y[8]:
                            for pid in range(len(y[8])):
                                if list1[0] == y[8][pid]:
                                    y[8][pid] = list1
                        if list1[0] in y[9]:
                            for pid in range(len(y[9])):
                                if list1[0] == y[9][pid]:
                                    y[9][pid] = list1


        # Loop over all of the results.
        for info2 in info1:
            # Define the total scores and fsids array.
            scores = []
            all_fsids = []
            
            if len(info2)==0:
                continue
            
            # Find the index of the person of interest.
            for y in tracker:
                try:
                    if info2[0][0] in y:
                        loop1 = y[-1]
                except:
                    print(info2,'\n',y,'its me!')
                    return info1, info2, y, tracker
            # Loop over each of the matches and create a match score.
            # Here we define a counter that we use to loop.
            index = 0
            while index < len(info2):
                # Reinitialize the variables.
                marriage_date, marriage_place, marriage_date_parents, marriage_place_parents = ['']*4
                fs_name, fs_birthdate, fs_birthplace, fs_deathdate, fs_deathplace = ['']*5
                fs_name_spouse, fs_birthdate_spouse, fs_birthplace_spouse, fs_deathdate_spouse, fs_deathplace_spouse = ['']*5
                fs_name_dad, fs_birthdate_dad, fs_birthplace_dad, fs_deathdate_dad, fs_deathplace_dad = ['']*5
                fs_name_mom, fs_birthdate_mom, fs_birthplace_mom, fs_deathdate_mom, fs_deathplace_mom = ['']*5
                
                # Get the main pid.
                mainid = info2[index][0]
                
                # Get each of the variables we care about, pass if they don't exist.
                fs_name = info2[index][1]
                fs_birthdate = info2[index][2]
                fs_birthplace = info2[index][3]
                fs_deathdate = info2[index][4]
                fs_deathplace = info2[index][5]
                
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
                
                # Ensure we have relationships.
                if info2[index][6] == '' and info2[index][7] == [] and info2[index][8] == [] and info2[index][9] == []:
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
                        
                    # Append to the arrays.
                    scores = scores + score
                    all_fsids.append(mainid)
                    
                    # Increment the index.
                    index += 1
                    continue
    
                # Get the marriage date and place.
                marriage_date = info2[index][10]
                marriage_place = info2[index][11]
                
                # Define arrays for children and sibling names, birth dates, and birth places.
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
                
                # Get spouse info if it exists.
                if info2[index][6] != '':
                    fs_name_spouse = info2[index][6][1]
                    fs_birthdate_spouse = info2[index][6][2]
                    fs_birthplace_spouse = info2[index][6][3]
                    fs_deathdate_spouse = info2[index][6][4]
                    fs_deathplace_spouse = info2[index][6][5]
                
                # Children info.
                if info2[index][7] != []:
                    for y in info2[index][7]:
                        children.append(y[1])
                        children_birthdates.append(y[2])
                        children_birthplaces.append(y[3])
                        children_deathdates.append(y[4])
                        children_deathplaces.append(y[5])  
                
                # Parent info.
                if info2[index][8] != []:
                    for y in info2[index][8]:
                        if y[6] == 'Female':
                            fs_name_mom = y[1]
                            fs_birthdate_mom = y[2]
                            fs_birthplace_mom = y[3]
                            fs_deathdate_mom = y[4]
                            fs_deathplace_mom = y[5]
                        else:
                            fs_name_dad = y[1]
                            fs_birthdate_dad = y[2]
                            fs_birthplace_dad = y[3]
                            fs_deathdate_dad = y[4]
                            fs_deathplace_dad = y[5]
                
                # Sibling info.
                if info2[index][9] != []:
                    for y in info2[index][9]:
                        siblings.append(y[1])
                        siblings_birthdates.append(y[2])
                        siblings_birthplaces.append(y[3])
                        siblings_deathdates.append(y[4])
                        siblings_deathplaces.append(y[5])
                        
    
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
        loop += 1        
        
        # Reset the lists.
        allresults = []
        tracker = []
            
    # Write the finished file.
    self._finished()
    
    print('\nComplete!')

if __name__ == '__main__':
    
    import os
    import sys
    
    sys.path.append(r'R:\JoePriceResearch\Python\Anaconda3\Lib\site-packages')

    os.chdir(r"R:\JoePriceResearch\Python\all_code")
    from FamilySearch1 import FamilySearch
    os.chdir(r"R:\JoePriceResearch\Python\all_code\FamilySearch1")
    from ArkSearch import ArkSearch
    
    fs = FamilySearch('bbranchf', 'chimps58', r'R:\JoePriceResearch\Python\all_code\FamilySearch1\test_data')
    fs.infile = 'find_test.csv'
    fs.outfile = 'find_test_out.csv'
    out = fs.Find(names={})

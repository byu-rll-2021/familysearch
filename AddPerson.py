 # -*- coding: utf-8 -*-
"""
This file contains the main body of the AddPerson method of the Familysearch
class.

Created: 23 July 2018
Last edited: 9 September 2019, Ben Busath


"""

import re
import sys
import requests
import pandas as pd
import json
import os
import time



def AddPerson(self,token=None,names=None,max_people=1):
    """
    This function creates profiles on familysearch based on the given
    information. Current possible person information that can be added 
    are given name, surname, gender, birthdate, birthplace, deathdate, deathplace,
    burialdate, burialplace, residence date, residence place.
    
    Input data requires unique numerical index column with label title 'index'
    
    PARAMETER INFO
    
    token: FS Authentication Token
    
    names: grabbing dictionary for renaming column labels. Required variable names
            are in the varlist python lsit.
    
    FIXME
    max_people: max people to be added within one API call. Not implemented yet,
                default set at 1
    """
    # 
    if token == None:
        token=self.Authenticate()
    
    df = pd.read_csv(self.infile)
    
    # Implement grabbing a dictionary so that the column names are consistent
    varlist=['index','given','surname','gender','birthdate','birthplace','deathdate','deathplace',
             'burialdate','burialplace','resdate','resplace']
    
    if names is None:
        df = pd.read_csv(self.infile)
    else:
        try:
            df = pd.read_csv(self.infile)
        except UnicodeDecodeError:
            print(sys.exc_info()[0])
            print('UnicodeDecodeError : the function will try with a',
                  'different encoding that may or may not work')
            df = pd.read_csv(self.infile, encoding='latin1')
            

    if names is not None:
        df = df.rename(columns=names)
    
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
        #if re.search('Date',x):
         #   df[x] = df[x].str.replace('\.[0-9]+','')

    persons_node = 'https://api.familysearch.org/platform/tree/persons/'
    
    # opening a file and a requests session to be used throughout the process
    with open(self.outfile, 'w') as outfile, requests.Session() as session:
        
        # these will be passed in with each request in the session
        session.headers.update({'Authorization' : f'Bearer {token}', 
                                'Content-type':'application/x-fs-v1+json'})
    
        # writing headers
        outfile.write('index,pid\n')
        
        row_count=len(df.index)
        for num,row_index in enumerate(df.index):
            self._timer('on')
            
            row = df.iloc[row_index,:]
          
            # assigning the variables
            index = row['index']
            gender = row['gender'].title()
            given = row['given'].title()
            surname = row['surname'].title()
            birthdate = row['birthdate'].title()
            birthplace = row['birthplace'].title()
            deathdate = row['deathdate'].title()
            deathplace = row['deathplace'].title()
            burialdate = row['burialdate'].title()
            burialplace = row['burialplace'].title()
            residencedate = row['resdate'].title()
            residenceplace = row['resplace'].title()
            # populating the dictionaries of information
            # fill in gender information
            gender_dict = {"type" : f"http://gedcomx.org/{gender}"}
            
            # fill in name information
            names_dict = [
                            {"type" : "http://gedcomx.org/BirthName",
                            "nameForms" : [
                                {"fullText" : f'{given} {surname}',
                                "parts" : [
                                    {"type" : "http://gedcomx.org/Given",
                                     "value" : f'{given}'},
                                    {"type" : "http://gedcomx.org/Surname",
                                     "value" : f'{surname}'}
                                ],
                                }
                            ],
                            "preferred" : True
                            }
                        ]
            
            # fill in birth information
            birth_dict=None
            if (birthdate!='')|(birthplace!=''):
                birth_dict = {"type" : "http://gedcomx.org/Birth"}
                if birthdate != '':
                    birth_dict['date'] = {'original':f'{birthdate}'}
                if birthplace != '':
                    birth_dict['place'] = {"original" : f'{birthplace}'}
                        
            
            # fillin death information
            death_dict=None
            if (deathdate!='')|(deathplace!=''):
                death_dict = {"type" : "http://gedcomx.org/Death"}
                if deathdate != '':
                    death_dict['date'] = {'original':f'{deathdate}'}
                if deathplace != '':
                    death_dict['place'] = {"original" : f'{deathplace}'}
                    
            
            # fill in burial information
            burial_dict=None
            if (burialdate!='')|(burialplace!=''):
                burial_dict = {"type" : "http://gedcomx.org/Burial"}
                if burialdate != '':
                    burial_dict['date'] = {'original':f'{burialdate}'}
                if burialplace != '':
                    burial_dict['place'] = {"original" : f'{burialplace}'}
            
            
            # fill in residence information
            residence_dict=None
            if (residencedate!='')|(residenceplace!=''):
                residence_dict = {"type" : "http://gedcomx.org/Residence"}
                if residencedate != '':
                    residence_dict['date'] = {'original':f'{residencedate}'}
                if residenceplace != '':
                    residence_dict['place'] = {"original" : f'{residenceplace}'}
            
            
            # adding the birth. death and other info into the facts list if provided
            facts_list=[birth_dict, death_dict, burial_dict, residence_dict]
            facts_list=[x for x in facts_list if x is not None]
        
            # read data on people to add
            to_post = []
            people_info = []
            for person in range(1):
                # adding all of the individual's information
                person_dict = {
                "living" : False,
                "gender" : gender_dict,
                "names" : names_dict,
                "facts" : facts_list
                }
                people_info.append(person_dict)
                if len(people_info) == max_people:
                    to_post.append({'persons' : people_info})
                    people_info = []
            
                if len(people_info) > 0:
                    to_post.append(people_info)
            
            # add the people to the tree
            for block in to_post:
                response = session.post(persons_node, data=json.dumps(block))
                if response.status_code == 201: # s successful addition
                    fsid = re.search('[A-Z0-9]{4}-[A-Z0-9]{3,4}',
                                     response.headers['link']).group()
                    
                    # write created id to file
                    outfile.write(f"{index},{fsid}\n")
                # throttled
                elif response.status_code == 429:
                    wait = (int(response.headers['Retry-After'])*1.1)
                    print('Throttled, waiting {0: .1f} seconds!'.format(wait))
                    time.sleep(wait)
                    
                elif response.status_code == 400:
                    print(400)
                    print('Bad Request')
                    continue
                else:
                    print('\nPotential Error, Status code:',
                                  response.status_code, '\n')
                    
                    print(f'Could not get values around line {num}, moving on')
            
            if num % 500 == 499:
                print(num + 1, f'of {row_count}')
                self._timer('off', row_count=row_count, numobs=max_people,
                            ndigits=4)

                    
                   

                


if __name__=='__main__':
    info={'gender' : ['Female'],
    'given' : ['Jane F'],
    'surname' : ['Doe'],
    'birthdate' : ['27 june 1900'],
    'birthplace' : ['Salt Lake City, Utah, United States'],
    'resdate' : ['1910'],
    'resplace' : ['Monument, Colorado, United States']
}
    infile = r'R:\JoePriceResearch\RA_work_folders\Ben_Busath\in.csv'
    outfile =r'R:\JoePriceResearch\RA_work_folders\Ben_Busath\out.csv'
    pd.DataFrame(info).reset_index().to_csv(infile)
    
    sys.path.append(r'R:\JoePriceResearch\Python\all_code')
    from FamilySearch1 import FamilySearch
    fs=FamilySearch('laren.edwards','ledward5',os.getcwd(),infile,outfile)
    fs.AddPerson()
    print(pd.read_csv(outfile).head())
    #results.headers
    #to_post

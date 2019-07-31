# -*- coding: utf-8 -*-
"""
This file contains the main body of the AddPerson method of the Familysearch
class.

Created: 23 July 2018
Last edited: 27 July 2018, Ben Branchflower

Currently just building the skeleton of the code and starting to fill in the
holes

"""

import re

import requests
import pandas as pd
import json

token = 'f1e7d5f8-9084-41d8-833b-a2772de075f2-prod' # 9 july 2019 11:40 AM
persons_node = 'https://api.familysearch.org/platform/tree/persons/'

max_people = 2

directory = ''
infile = ''


def AddPerson():
    """
    This function creates profiles on familysearch based on the given
    information. It requires a very specific format that is broken down
    into relatively small parts to help me and future editors see the process
    clearly
    
    Note: The intention is to implement this as part of the FamilySearch class
    but it is not currently being used as a method to facilitate testing. When
    the function is ready for beta testing self will be added where appropriate
    """
    # 
    df = pd.read_csv(infile, header=0)
    
    # Implement grabbing a dictionary so that the column names are consistent
    
    
    
    df = df.rename(columns=names)
    
    # FIXME: this loop will not grab any of the actual data for now
    for row_index in df.index:
        
        row = df.iloc[row_index,:]
        
        # assigning the variables
        gender = row['gender'].capitalize()
        given = row['given'].capitalize()
        surname = row['surname'].capitalize()
        birthdate = row['birthdate'].capitalize()
        birthplace = row['birthplace'].capitalize()
        deathdate = row['birthdate'].capitalize()
        deathplace = row['birthplace'].capitalize()
        burialdate = row['birthdate'].capitalize()
        burialplace = row['birthplace'].capitalize()
        
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
        birth_dict = {
                "type" : "http://gedcomx.org/Birth",
                "date" : {"original" : f'{birthdate}'},
                "place" : {"original" : f'{birthplace}'}
                }
        
        # fillin death information
        death_dict = {
                "type" : "http://gedcomx.org/Death",
                "date" : {"original" : f"{deathdate}"},
                "place" : {"original" : f'{deathplace}'}
                }
        
        # fill in burial information
        burial_dict = {
                "type" : "http://gedcomx.org/Burial",
                "date" : {"original" : f"{burialdate}"},
                "place" : {"original" : f'{burialplace}'}
                }
        
        # adding the birth. death and other info into the facts list
        facts_list=[birth_dict, death_dict, burial_dict]
        
    
        # read data on people to add
        to_post = []
        people_info = []
        for person in people:
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
    with requests.Session() as session:
        session.headers.update({'Authorization' : f'Bearer {token}', 
                                'Content-type':'application/x-fs-v1+json'})
        for block in to_post:
            response = session.post(persons_node, data=json.dumps(block))
            if response.status_code == 201: # s successful addition
                id_1 = re.search('[A-Z0-9]{4}-[A-Z0-9]{3,4}',
                                 response.headers['link']).group()
        
        
    
# test case, signle individual successfully added 24 July 2018
gender = 'Male'
given = 'Ben'
surname = 'Branchflower'
birthdate = '27 june 1995'
birthplace = 'Kamloops, British Columbia, Canada'
deathdate = '18 May 2012'
deathplace = 'Provo, Utah County, Utah, United States'
burialdate = '10 May 1943'
burialplace = 'Monrovia, Liberia'
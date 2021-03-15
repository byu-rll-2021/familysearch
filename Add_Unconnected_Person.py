# -*- coding: utf-8 -*-
"""
This is code under construction, with the goal of creating a function that will
read in entire families into Family Search that are unconnected to the rest of 
the Tree.

Last edited: 5/24/2019, Katie Stevens
"""
import json
import os
import re

import requests
import pandas as pd

"""
===============================================================================
VARIABLES:
===============================================================================
"""
os.chdir(r'R:\JoePriceResearch\Python\all_code')
from FamilySearch1 import FamilySearch
fs = FamilySearch('benbranchflower','chimps58',r'R:\JoePriceResearch\RA_work_folders\Katie_Stevens\Add_Unconnected_Person')
token = fs.token

pid_list = [] #| Keeps track of experimental pids to be deleted--can be deleted
              #| once the code is operational.
to_post = []

"""
===============================================================================
FUNCTIONS:
===============================================================================
"""
def Add_Person(infile,verbosity=0):
    """
    This function reads a list of people from a file and adds them to Family 
    Search. It prints their pid if it is successful. It is currently working
    well for a single person; it is sometimes having issues reading in multiple
    people.
    """
    # Accessing the API
    session = requests.Session()
    session.headers.update({'Authorization' : f'Bearer {token}', 
                                'Content-type':'application/x-fs-v1+json'})
    persons_node = 'https://api.familysearch.org/platform/tree/persons/'
    
    # Local variables
    infile = infile
    max_people = 1
    
    # Reading the file
    df = pd.read_csv(infile, header=0)
    df.dropna(how = 'all', inplace = True)
    
    if verbosity > 3:
        print(df)
    
    for row_index in df.index:
        
        row = df.iloc[row_index,:]
        
        # assigning the variables
        gender = row['gender'].capitalize()
        given = row['given'].capitalize()
        surname = row['surname'].capitalize()
        birthdate = row['birthdate']#.capitalize()
        birthplace = row['birthplace'].capitalize()
        deathdate = row['deathdate']#.capitalize()
        deathplace = row['deathplace'].capitalize()
        burialdate = row['burialdate']#.capitalize()
        burialplace = row['burialplace'].capitalize()
        
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
        facts_list = [birth_dict, death_dict, burial_dict]
        
        # Empty the person_info list
        person_info = []
        
        # Constructing the list we will post to Family Search
        person_dict = {
        "living" : False,
        "gender" : gender_dict,
        "names" : names_dict,
        "facts" : facts_list
        }
        person_info.append(person_dict)
    
        if len(person_info) == max_people:
            to_post.append({'persons' : person_info})
            person_info = []
            
        if len(person_info) > 0:
            to_post.append(person_info)
    
    # Posting the people to Family Search
    for block in to_post:
        if verbosity > 2:
            print(block)
        response = session.post(persons_node, data=json.dumps(block))
        if verbosity > 0:
            print("Resp:", response.status_code)
        if response.status_code == 201: # successful addition
            pid = re.search('[A-Z0-9]{4}-[A-Z0-9]{3,4}',
                             response.headers['link']).group()
            print("PID: ", pid)
            pid_list.append(pid)
        elif response.status_code == 400:
            print(response.headers['Warning'],'\n')
        else:
            print(response.status_code)
            
    # Export list of pids to be deleted
    with open("Pids_to_delete.csv", "a") as del_l:
        for pid in pid_list:
            del_l.write(pid + '\n')
            
    return pid_list


def _compile_dict():
    raise NotImplementedError

def Add_Couple_Relationship(husband_id, wife_id):
    """
    This function takes the pids of a wife and husband, and creates a couple
    relationship. This function is functional.
    
    ***Note: The order matters--either specify the inputs, or put a male first 
    and then a female
    """
    # Accessing the API
    session = requests.Session()
    session.headers.update({'Authorization' : f'Bearer {token}', 
                                'Content-Type':'application/x-fs-v1+json'})
    path = 'https://api.familysearch.org/platform/tree/relationships'
    
    contributor_id = 'KWNC-SP8' # Jacob Van Leeuwen's pid
    
    data_couple = {
      "relationships" : [ {
        "type" : "http://gedcomx.org/Couple",
        "person1" : {
          "resource" : f"https://api.familysearch.org/platform/tree/persons/{husband_id}",
          "resourceId" : husband_id
        },
        "person2" : {
          "resource" : f"https://api.familysearch.org/platform/tree/persons/{wife_id}",
          "resourceId" : wife_id
        },
        "facts" : [ {
          "attribution" : {
            "contributor" : {
              "resource" : f"https://api.familysearch.org/platform/users/agents/{contributor_id}"
            },
            "changeMessage" : "...change message..."
          },
          "type" : "http://gedcomx.org/Marriage",
          "date" : {
            "original" : "June 1800",
            "formal" : "+1800-06"
          },
          "place" : {
            "original" : "Provo, Utah, Utah, United States"
          }
        } ]
      } ]
    }
        
    resp = session.post(path, data=json.dumps(data_couple))
    print(resp.status_code)

def Delete_People(pids_l):
    """
    Deletes a list of people from Family Search. (Takes a list of pids, deletes each person.)
    """
    # Accessing the API
    session = requests.Session()
    session.headers.update({'Authorization' : f'Bearer {token}', 
                                'Content-type':'application/x-gedcomx-v1+json',
                                'X-Reason': 'This person does not exist.'})
                        
    # Deleting each person in the list
    for pid in pids_l:
        path = f'https://api.familysearch.org/platform/tree/persons/{pid}'
        resp = session.delete(path)
        
        # Print feedback
        print(resp.status_code)
        if resp.status_code == 410:
            print("Already deleted ", pid)
        elif resp.status_code not in (204, 410):
            print("failed to delete: ", pid)
            
            
def Add_Par_Chil_Rel(dad_id, mom_id, child_id, change_message='As listed on census',):
    """
    Creates parent-child relationship, given id's of parents and the child.
    """
    session = requests.Session()
    session.headers.update({'Authorization' : f'Bearer {token}', 
                                'Content-Type':'application/x-fs-v1+json',
                                'X-FS-Feature-Tag':'generic.relationship.terms'})
            
    path = 'https://api.familysearch.org/platform/tree/relationships'
    
    contributor_id = 'KWNC-SP8' # Jacob Van Leeuwen's pid

    p_c_data = {
    "childAndParentsRelationships" : [ {
        "parent1" : {
          "resource" : f"https://api.familysearch.org/platform/tree/persons/{dad_id}",
          "resourceId" : "GSVV-JS6"
        },
        "parent2" : {
          "resource" : f"https://api.familysearch.org/platform/tree/persons/{mom_id}",
          "resourceId" : mom_id
        },
        "child" : {
          "resource" : f"https://api.familysearch.org/platform/tree/persons/{child_id}",
          "resourceId" : child_id
        },
        "parent1Facts" : [ {
          "id" : "C.1",
          "attribution" : {
            "contributor" : {
              "resource" : f"https://api.familysearch.org/platform/users/agents/{contributor_id}"
            },
            "changeMessage" : change_message
          },
          "type" : "http://gedcomx.org/BiologicalParent"
        } ],
        "parent2Facts" : [ {
          "id" : "C.2",
          "attribution" : {
            "contributor" : {
              "resource" : f"https://api.familysearch.org/platform/users/agents/{contributor_id}"
            },
            "changeMessage" : change_message
          },
          "type" : "http://gedcomx.org/BiologicalParent"
        } ]
      } ]
    }
    
    resp = session.post(path, data=json.dumps(p_c_data))
    print(resp.status_code)
    return resp

            
if __name__ == '__main__':
    Delete_People(pd.read_csv('Pids_to_delete.csv').iloc[:,0])
    infile = 'test_people.csv'
    #try:
    dad_pid, mom_pid, kid_pid = Add_Person(infile,verbosity=2)
    df = pd.read_csv(infile)
    #except Exception as e:
        #Delete_People(pd.read_csv('Pids_to_dele'))
    #    print(e)
    
    Add_Couple_Relationship(dad_pid, mom_pid)
    Add_Par_Chil_Rel(dad_pid, mom_pid, kid_pid)
    
    # Delete_People(pd.read_csv('Pids_to_delete.csv').iloc[:,0])
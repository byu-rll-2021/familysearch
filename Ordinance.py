# -*- coding: utf-8 -*-
"""
This file is for the methods of the FamilySearch class that use the ordinance
information. The primary function is FindConverts which will find the people 
in the tree that received ordinances while they were alive and were
not born in the covenant. The logical process could likely be improved and is
not discouraged by any means as this was simply the way that seemed to do an 
adequate job without excessive effort to obtain them

Created: 22 January 2019
Author: Ben Branchflower
"""

import re
import time

import requests


def FindConverts(start_fsid):
    """
    this function identifies ancestors of an individual that were converts
    and returns a list of them
    
    *** NOTE ***
        * the methodology used should not get any individuals that are not
           convert but will likely only identify one individual as a convert in
           a family
           
    Parameters:
        
    Returns:
        a list on fsids of ancestors that were converts, as described in the
        note this is likley only a subset of the total converts.
    """
    
    session = requests.Session()
    session.headers.update({f'Authorization': f'Bearer {token}',
                            'Accept':'application/json'})
    # get ancestry of start individual
    ancestry = _get_ancestry_info(start_fsid, session)
    
    convert_list = []
    uncertain_list = []
    
    for person in ancestry:
        convert_status = _convert(person['id'], session)
        if convert_status and convert_status[0]:
            print(convert_status)
            if convert_status == "uncertain":
                uncertain_list.append(person)
            else:
                person.update({'baptismYear':convert_status[1]})
                convert_list.append(person)
    
    return pd.DataFrame(convert_list).drop('descendancyNumber', axis='columns',)

    
def  _get_ancestry_info(fsid, session):
    """
    Gets the information from the API about the ancestry of the starting 
    individual and keeps the bare bones
    """
    
    url = f'http://api.familysearch.org/platform/tree/ancestry?person={fsid}&generations=8'
    response = session.get(url)
    
    person_list = []
    for person in response.json()['persons']:
        person_info = person['display']
        person_info.update({'id':person['id']})
        person_list.append(person_info)
    
    return person_list

    
def _convert(fsid, session):
    """
    This function will use the ordinance info on people to infer whether a
    person received ordinances while they were alive
    
    Parameters:
        fsid (str) - the id of the individual to be considered
        session - the active Session object from the requests package that 
            will be used to make and receive the request with the familysearch
            servers
    
    Returns: 
        bool based on whether ordinances were completed 
        before death date.
        *** Also returns uncertain in the case where no death date is found
    """
    # get ordinance info on the person
    url = f'https://www.familysearch.org/tree-data/reservations/person/{fsid}/ordinances'
    resp = session.get(url)
    
    if resp.status_code == 200:
        # check if there is a baptism completed
        try:
            if resp.json()['data']['baptism']['status'] != 'Completed':
                return False
        except TypeError:
            print('failed\n', resp.json())
            print(resp.status_code)
            time.sleep(5)
            _convert(fsid, session)
        
        # check if the individual was born in the covenant
        try:
            if resp.json()['data']['sealingsToParents'][0]['bornInCovenant']:
                return False
        except KeyError:
            pass
            
        # get death year
        try:
            d_date = re.search(r'\d{4}$', resp.json()['data']['lifespanForRules'])[0]
        except TypeError: 
            return 'uncertain' # FIXME: Consider what to do in the case of a missing deathdate
        
        if int(d_date) < 1830:
            return False
        
        # get year of baptism
        try:
            bap_date = re.search(r'\d{4}$', resp.json()['data']['baptism']['completedDate'])[0]
        except KeyError:
            return False
        
        # declared a convert if baptised before death
        return int(bap_date) <= int(d_date), bap_date, 
    
    else:
        print(resp)


if __name__ == '__main__':
    price_data = FindConverts(price)
    price_data.to_csv(r'R:\JoePriceResearch\RA_work_folders\Ben_Branchflower\price_converts.csv', index=False)
# -*- coding: utf-8 -*-
"""
Created on Tue May 02 16:43:14 2017

@author: tannerse

Updated: 11 Jan 2019 Ben Branchflower
"""

import re
import time

import pandas as pd
import requests

# import sys
# from time import sleep

# sys.path.append('R:\\JoePriceResearch\\Python\\all_code')

# from selenium import webdriver
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys

token = "5d048c6b-5981-47d3-b421-cfa5eec5b77a-aws-prod " # obtained 2 Feb 2019 10:00 AM

# test person 
fsid = 'KWC2-K6Q'
fsid2 = 'KWCZ-JFF'

thomas = 'KWH3-DQT'

price = 'KWZG-XJ3'

# ordinance not done
no_ord_fsid = 'M53V-JCT'

# base_url
url = f'https://www.familysearch.org/tree-data/reservations/person/{no_ord_fsid}/ordinances'

 

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
    fsid = 'KWHJ-SFZ'
    out_data = FindConverts(fsid)
    out_data.to_csv(r'R:\JoePriceResearch\RA_work_folders\Ben_Branchflower\{}_converts.csv'.format(fsid),
                        index=False)


def remove_non_ascii_1(text):
    """
    Any usage of this function would preferrably call the remove_non_ascii 
    method of the FamilySearch class so we don't need this function 
    """
    return ''.join(i for i in text if ord(i)<128)

def ScrapeOrdinance(driver,index,fsid,outfile,first):
    """
    This function will soon be deprecated in favor of the faster ones that
    do not depend on the format of the website so heavily
    """
    
    failed = False
    
    #Get the website.
    site = 'https://www.familysearch.org/tree/person/ordinances/%s' %(fsid)
    driver.get(site)
    
  
    counter = 0
    check = False
    while True:
        # Get the text.
        text = ''
        text = driver.find_element_by_css_selector('html').text
        
        # Get the deleted page.
        if re.search('PERSON DELETED', text):
            # Click on the new link.
            try:
                driver.find_element_by_class_name('affected-person-link').click()
            except KeyboardInterrupt:
                sys.exit(1)
            except:
                pass
        
        # See if the person currently exists.
        if re.search('View My Relationship', text):
            # Make sure we actually are catching something correct.
            if check == False:
                check = True
                sleep(.1)
                continue
                
            # Get the pid.
            fsid = driver.current_url[-8:]
            
            # Break.
            check = False
            break
        
        # Skip if restricted or removed.
        if re.search('This person does not exist, has been removed', text):
            # Break.
            check = False
            break
        
        # Sleep and increment the counter.
        sleep(.1)
        counter += 1
        
        # If counter is too high, refresh the page and retry.
        if counter > 300:
            driver.get('https://www.familysearch.org/tree/person/ordinances/{}'.format(fsid))
            counter = 0

    #Get the website.
    site = 'https://www.familysearch.org/tree/person/ordinances/%s' %(fsid)
    driver.get(site)        
        
    #Scrape the ordinance page and clean the data.
    try:
        WebDriverWait(driver,30).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'#personOrdinancesContainer > div.personOrdinances')))
    except KeyboardInterrupt:
        sys.exit(1)
    except:
        failed = True         
        return failed
                
                
   
    info = remove_non_ascii_1(driver.find_element_by_css_selector('#personOrdinancesContainer > div.personOrdinances').text)
    
    info = info.split('\nB\n')
    info = info[1].split('\nC\n')
    
    baptism = info[0]
    
    info = info[1].split('\nI\n')
    
    confirmation = info[0]
    
    info = info[1].split('\nE\n')
    
    initiatory = info[0]
    
    info = info[1].split('\nSP\n')
    
    endowment = info[0]
    sealing_parents = []
    if len(info) > 2:
        for x in range(1,len(info)-1):
            sealing_parents.append(info[x])
    
    info = info[len(info)-1].split('\nSS\n')
    
    sealing_parents.append(info[0])
    
    sealing_spouse = []
    for x in range(1,len(info)):
        sealing_spouse.append(info[x])
        
    #Write to an outfile.
    j = open(outfile,'a')
    j.write(index + ',' + fsid + ',' + re.sub(r'\n',r';',baptism) + ',' + \
        re.sub(r'\n',r';',confirmation) + ',' + re.sub(r'\n',r';',initiatory) \
        + ',' + re.sub(r'\n',r';',endowment))
    for x in range(0,len(sealing_parents)):
        j.write(',' + re.sub(r'\n',r';',sealing_parents[x]))
    for x in range(0,len(sealing_spouse)):
        j.write(',' + re.sub(r'\n',r';',sealing_spouse[x]))
    j.write('\n')
    j.close()
    
    
    
        
    
    
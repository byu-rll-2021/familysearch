# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 14:24:50 2018

@author: cookchr2
"""

import os
from selenium import webdriver
from bs4 import BeautifulSoup
import re
import pandas as pd

def _get_two(self):
    
    # Read the file.
    data = pd.read_stata(self.infile)

    #login to family search
    #Call chromedriver
    chromedriver = 'R:\\JoePriceResearch\\Python\\chromedriver.exe'
    os.environ['webdriver.chrome.driver'] = chromedriver
    driver = webdriver.Chrome(chromedriver)
    
    #Open Family Search and login
    driver.implicitly_wait(10)
    driver.get('https://familysearch.org/tree/#view=tree&section=pedigree')
    driver.find_element_by_name('userName').send_keys(self.username)
    driver.find_element_by_name('password').send_keys(self.password)
    driver.find_element_by_id('login').click()
    
    for x in range(data.shape[0]):
        
        url = data['fs_image_pal'][x]
        
        driver.get(url)
        
        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        people = soup.findAll('td', {'class': 'ng-scope ng-binding'})
        record = soup.findAll('a', {'class': 'full-details-link'})
        
        name = data['pr_name'][x]
        age = str(data['pr_age'][x])
        match_name = False
        match_age = False
        count = 0
        for person in people:
            
            #match on name
            if name in str(person):
                match_name = True
                
            #match on age
            if age in str(person):
                match_age = True
            
            #people come in batches of 10; grab ark for the person
            if count % 10 == 9:
                if match_name and match_age:
                    match_ind = int((count + 1)/10) - 1
                    ark = re.search(r'[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9]',str(record[match_ind])).group()
                    print(ark)
                match_name = False
                match_age = False
            
            #keep track of where we are
            count = count + 1
            
    driver.quit()
        
        


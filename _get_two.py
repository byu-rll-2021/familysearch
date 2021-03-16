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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep, time



def _get_two(self):
    try:
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
        
        final_vars = {}
        for x in range(data.shape[0] + 1):
            
            url = data['fs_image_pal'][x]
            print(url)
            try:
                driver.get(url)
                WebDriverWait(driver,30).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'#image-index > div:nth-child(3) > div.scrollable.record-table-wrapper > table > tbody > tr:nth-child(1) > td:nth-child(2)')))
            except:
                for var in range(1,200):
                    try:
                        driver.get(url)
                        WebDriverWait(driver,30).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'#image-index > div:nth-child(3) > div.scrollable.record-table-wrapper > table > tbody > tr:nth-child(1) > td:nth-child(2)')))
                        break
                    except:
                        pass
                    if var == 199:
                        print('Something is super wrong')
                        raise
            sleep(4)
            for y in range(0,100000):
                soup = BeautifulSoup(driver.page_source, 'lxml')
                
                people = soup.findAll('td', {'class': 'ng-scope ng-binding'})
                record = soup.findAll('a', {'class': 'full-details-link'})
                if len(record) > 0 and len(people) > 0:
                    print(len(record))
                    print(len(people))
                    break
                if y == 99999:
                    print('Something is very very wrong')
                    raise
            
            name = data['pr_name_gn'][x] + ' ' + data['pr_name_surn'][x]
            age = str(data['pr_age'][x])
            print(name)
            print(age)
            match_name = False
            match_age = False
            count = 0
            for person in people:
                
                #match on name
                if name in str(person):
                    #print('match_name on ' + str(count))
                    match_name = True
                    
                #match on age
                if age in str(person):
                    #print('match_age on ' + str(count))
                    match_age = True
                
                #people come in batches of 10; grab ark for the person
                if count % 10 == 9:
                    if match_name and match_age:
                        match_ind = int((count + 1)/10) - 1
                        ark = re.search(r'[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9]',str(record[match_ind])).group()
                        print(ark)
                        final_vars[str(data['fs_unique_id'][x])] = ark
                    match_name = False
                    match_age = False
                
                #keep track of where we are
                count = count + 1
        
        df = pd.DataFrame.from_dict(final_vars,orient='index')
        df.to_stata(self.outfile,write_index=True)
            
        driver.quit()
    except:
        print(final_vars)
        df = pd.DataFrame.from_dict(final_vars,orient='index')
        df.to_stata(self.outfile,write_index=True)
        


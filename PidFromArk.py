# -*- coding: utf-8 -*-
"""
Created on Thu May 10 09:55:36 2018

@author: tannerse
"""
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep
import pandas as pd
import sys
import numpy as np


def expand_shadow_element(driver, element):
    '''
    This gets past the shadow root elements on census pages.
    
    Parameters
    ----------
    driver     - A selenium webdriver instance.
    element    - The selenium web element where the shadow root is.
    
    Returns
    -------
    The expanded shadow root.
    '''
    shadow_root = driver.execute_script('return arguments[0].shadowRoot', element)
    return shadow_root


def get_pid(driver, ark):
    '''
    Gets the pid of any attached person. If nobody is attached, returns an empty string.
    
    Parameters
    ----------
    driver     - A selenium webdriver instance.
    ark        - The FamilySearch record ark id.
    
    Returns
    -------
    The FamilySearch pid if someone is attached, an empty string otherwise.
    '''
    # Get the main record page.
    driver.get('https://www.familysearch.org/ark:/61903/1:1:%s'%ark)
    
    # Expand the first shadow root.
    root1 = driver.find_element_by_tag_name('record-details')
    shadow_root1 = expand_shadow_element(driver, root1)
    
    # Expand the second shadow root.
    #root2 = shadow_root1.find_element_by_css_selector('section.right > record-details-tools')
    #shadow_root2 = expand_shadow_element(driver, root2)
    
    
    try:
        # Ensure the page is loaded with the wait.
        sleep(1)
        
        # Expand the last shadow root.
        #root3 = shadow_root2.find_element_by_css_selector('fs-tree-person-renderer')
        root3 = shadow_root1.find_element_by_css_selector('record-details-attach')
        shadow_root3 = expand_shadow_element(driver, root3)
        
        # Get the element for the pid.
        pid = shadow_root3.find_element_by_css_selector('fs-person-eol')
        
        # Assign an empty string for the pid and loop until we get the actual pid.
        pid1 = ''
        while pid1 == '':
            try:
                # Get the pid.
                pid1 = pid.get_attribute('data-test-tree-person')
                print(pid1)
            except KeyboardInterrupt:
                sys.exit(1)
            except:
                pass
            
        # Return the pid.
        return pid1
    except:
        try:
            # Check for the attached button and return an empty string.
            shadow_root1.find_element_by_class_name('attach-button')
            return ''
        except:
            # Otherwise return 'error'.
            print('error')
            return 'error'
        

def GetPid(self):
    '''
    Gets all FamilySearch pids attached to a list of ark ids.
    
    The infile should be two columns, a list of unique indices and one of
    the FamilySearch arkids, in that order with headers. The names don't matter.
    It can be a csv, a dta, or an xlsx file.
    
    This will take an infile and rewrite it (as long as you have a csv).
    Otherwise it will write to a csv with the same name as the infile.
    '''
    # Assign the infile appropriately.
    ark_pid = self.infile

    # Check to see what type of file the input is and read it.
    if ark_pid[-3:] == 'csv':
        ark_df = pd.read_csv(ark_pid)
    elif ark_pid[-3:] == 'dta':
        ark_df = pd.read_stata(ark_pid)
    elif ark_pid[-3:] == 'lsx':
        ark_df = pd.read_excel(ark_pid)
        
    # Define which column is where the ark ids are located.
    ark_col = ark_df.columns[1]
    
    # Initialize the selenium webdriver instance.
    driver = self._login()
    driver.implicitly_wait(.1)
    
    # Iterate over rows in the ark data. 
    error_count = 0
    total_fails = 0
    i = 0
    
    # Define the pid column if it does not exist.
    if 'pid' not in ark_df.columns:
        ark_df['pid'] = ''

    # Ensure it works by adding a fail safe.
    try:
        # We will loop backwards to find the last pid we worked on to start there.
        for i in range(len(ark_df)-1,0,-1):
            # If the column is neither nan or '', start on the next ark.
            if not pd.isnull(ark_df.loc[i,'pid']) and not ark_df.loc[i,'pid'] == '':
                i += 1
                
                # Define the row count.
                row_count = len(ark_df)-i
                break
        
        if i == 1:
            row_count = len(ark_df)
            i = 0
    
        # Continue until we have gotten all of the arks.
        while i < ark_df.shape[0]:
            # Turn on the timer.
            self._timer('on')   
            
            # Assign the current ark.
            ark = ark_df.loc[i,ark_col]
            
            # If it is missing, increment the counter and pass.
            if ark == '':
                i += 1
                
            # If we have failed 10+ times, reboot.
            elif error_count >= 10:
                # If we failed completely 10 + times, break.
                if total_fails >= 10:
                    raise Exception('familysearch is either blocking this account or the servers are down. Aborting...')
    
                # Write 'error' to the file.
                ark_df.loc[i,'pid'] = 'error'
                ark_df.to_csv(ark_pid[:-4] + '.csv', index=False)
                
                # Quit and reboot the driver/FamilySearch.
                driver.quit()
                driver = self._login()
                driver.implicitly_wait(.1)
                
                # Reset the error count and increment the total fails/counter.
                error_count = 0
                total_fails += 1
                i += 1
                
            # This is where we hope the loop goes.
            else:
                try:
                    # Run the function to get the pid.
                    ark_df.loc[i,'pid'] = get_pid(driver, ark)
                    
                    # Write back to the file.
                    ark_df.to_csv(ark_pid[:-4] + '.csv', index=False)
    
                    # Reset the error count and increment the counter.
                    error_count = 0
                    i += 1
                except KeyboardInterrupt:
                    sys.exit(1)
                except:
                    # Increment the error count.
                    error_count += 1
                    print('error')
            
            # Turn the timer off.
            self._timer('off', row_count=row_count)
    except KeyboardInterrupt:
        sys.exit(1)
    except:
        # Write back to the file.
        ark_df.to_csv(ark_pid[:-4] + '.csv', index=False)
        
    # Quit the webdriver.
    driver.quit()
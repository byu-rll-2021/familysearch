# -*- coding: utf-8 -*-
"""
Created on Thu May  3 15:12:17 2018

@author: tannerse
"""
import os
import sys
sys.path.append(r'R:\JoePriceResearch\Python\Anaconda3\Lib\site-packages')
import requests
import pandas as pd
import re
from time import sleep


def expand_shadow_element(driver,element):
    shadow_root = driver.execute_script('return arguments[0].shadowRoot', element)
    return shadow_root

def AttachedCensus(self, year=None, get_census_data=True):
    '''
    Scrapes all censuses (or the specified year) attached to an individual.
    This will only handle direct links to the FamilySearch censuses.
    
    The infile should be two columns, a list of unique indices and one of
    the FamilySearch pids, in that order with no header.
    
    Parameters
    ----------
    year - Which year to scrape. None means scrape all attached censuses.
    get_census_data - a boolean for whether to get the info from the
                    corresponding arks or just to get the list of ids   
    '''
    # Check the output file.
    try:
        output = pd.read_csv(self.outfile, header=None, usecols=[0])
        lastid = output[0].iloc[-1]
    except:
        lastid = None
    
    # Read in the input file.
    df = pd.read_csv(self.infile, names=['uid', 'pid'],
                     usecols=[0,1], header=None)
    
    # Drop any missing ids and make sure everything is clean and valid.
    df['pid'] = df['pid'].str.extract('([0-9A-Z]{4}-[0-9A-Z]{3})', expand=False)
    df = df.loc[df.pid.notnull()]
    
    # Get the row count.
    row_count = len(df.pid)
    
    # Define the ark data frame.
    out = pd.DataFrame(columns=['uid','ark'])
    
    # First, log in to FamilySearch.
    #driver = self._login()
    
    # Make a cache for failed ids.
    #failed = []
    
    # Loop over observations.
    check = False
    print('Gathering arks...')
    for ind, pid in enumerate(df.pid):        
        # Check where we left off.
        if check == False:
            # If it is the last one, switch on check.
            if pid == lastid or lastid == None:
                check = True
                
            # Reduce row count.
            row_count -= 1
            continue
        
        # Turn on the timer.
        self._timer('on')
        
        # Define an empty array to hold the arks.
        data = []
        
        # initialize a variable to skip deleted IDs
        inaccessible = False
        
        for i in range(10):
            # Query the API.
            try:
                pull = requests.get('http://api.familysearch.org/platform/tree/persons/{}/sources'.format(pid), 
                                     headers={'Authorization': 'Bearer %s' %(self.token), 'Accept':'application/json'})
            except:
                print('Struggling to access R-Drive...')
                sleep(10)

            # Continue until we get a valid response in case we are throttled.
            if pull.status_code != 200 and pull.status_code != 401 and pull.status_code != 204 and pull.status_code != 403 and pull.status_code != 404: 
                print(pull.status_code)
                if pull.status_code == 429:
                    print('Throttled...')
                elif pull.status_code == 410:
                    print(f'\n\nfound a deleted ID, {pid}, skipping them\n\n')
                    inaccessible = True
                    break
                elif pull.status_code != 403 or pull.status_code != 404:
                    print(f'\n\ncould not access data on, {pid}, skipping them\n\n')
                    inaccessible = True
                    break
                else:
                    print('There is a potential issue, status code:',
                          pull.status_code)
                    print(f'The pull broke on the pid : {pid}')
                sleep(10)
            elif pull.status_code == 401:
                self.token = self.Authenticate()
            else:
                break
            if i == 9:
                print(f'There was an issue with {pid}, moving on')
                print('the status code on the pull was' + str(pull.status_code))
                
        # continue if pid info not accessible
        if inaccessible:
            with open(self.outfile + '_bad_pids.csv', 'a') as bad_pids:
                bad_pids.write(pid)
            continue
        
        # Continue if no sources.
        if pull.status_code == 204 or pull.status_code == 403 or pull.status_code == 404:
            continue
            
        # Get the text
        text = ''
        text = pull.json()
        
        # Define the regular expression to find.
        if year is None:
            match = 'United States Census'
        elif type(year) == int:
            match = 'United States Census, {}'.format(year)
        elif year.isdigit():
            match = 'United States Census, {}'.format(year)
        elif re.search('[Dd]eath', year):
            match = '[Dd]eath|[Oo]bit|[Dd]ied|[Gg]rave'
        

        # Loop to get all of the arks, verifying that there are sources.
        if 'sourceDescriptions' in text.keys():
            for y in range(len(text['sourceDescriptions'])):
                if re.search(match, text['sourceDescriptions'][y]['titles'][0]['value']):
                    try:
                        data.append(self._remove_non_ascii(text['sourceDescriptions'][y]['about']))
                    except:
                        pass
        
        # Once we have all of the arks, we will hit the census pages to scrape what we need.    
        # Loop over all of the sources.
        for y in data:
            try:
                ark = re.search('[A-Z0-9]{4}-[A-Z0-9]{3}[A-Z0-9]?', y).group()
            except:
                ark = ''
            if re.search('[0-9]{4}-[0-9]{4}', ark):
                ark = ''
            
            if ark != '':
                ap = pd.DataFrame([[df['uid'].iloc[ind], ark]], columns=['uid', 'ark'])
                out = out.append(ap, ignore_index=True)
                
        # Turn the timer off.
        self._timer('off', row_count=row_count)
    
    # Write a temporary file for the scrape record code.
    if year is None:
        self.infile = '_temp_in_census.csv'
    else:
        self.infile = '_temp_in_census{}.csv'.format(year)
    
    out.to_csv(self.infile, header=False, index=False)
    
    if get_census_data:
        # Scrape the records.
        print('Scraping the records...')
        self.iter = 0
        self.time_total = 0.
        self.ScrapeRecord()
        
        # Delete the temporary infile.
        os.remove(self.infile)


    '''
            # Get the webpage.
            if re.search('[Aa]ncestry', y):
                continue
            driver.get(y)
            
            # Reset the variables.
            text, info, info1, source1, total = ['']*5
    
            try:
                # Make sure the page is loaded.
                text = ''
                while text == '':
                    text = driver.find_element_by_css_selector('html').text
                
                # Get through the first shadow root.
                root1 = driver.find_element_by_tag_name('record-details')
                shadow_root1 = expand_shadow_element(driver, root1)
                
                # Get through the second shadow root.
                root2 = shadow_root1.find_element_by_css_selector('record-details-extra-fields')
                shadow_root2 = expand_shadow_element(driver, root2)
                
                # Click to expand the extra information tab.
                shadow_root2.find_element_by_class_name('expander').click()
        
                # Grab the text again.
                text = driver.find_element_by_css_selector('html').text
        
                # Separate out the main person information.
                info = re.search('(Name:[\s\S]+?)Household Role Sex Age Birthplace',text).group(1)
            except KeyboardInterrupt:
                sys.exit(1)
            except:
                print('Failed Full Info {}...'.format(pid))
                failed.append((pid, y))
                continue
            
            try:
                # Separate the main family information.
                info1 =  re.search('(Household Role Sex Age Birthplace[\s\S]+?)Tools\n',text).group(1)
            except KeyboardInterrupt:
                sys.exit(1)
            except:
                print('Failed Family Info {}...'.format(pid))
                failed.append((pid, y))
                continue
        
            try:
                # Separate out the main source information.
                source1 = re.search('(Document Information:\n)([\s\S]+?)Citing this Record\n',text).group(2)
            except KeyboardInterrupt:
                sys.exit(1)
            except:
                print('Failed Source Info {}...'.format(pid))
                failed.append((pid, y))
                continue
                
            # Parse the main person information.
            total = info
            total = total.split('\n')
            del total[-1]
            
            # Parse the main family information.
            info1 = re.sub(r'Household ',r'',info1)
            info1 = re.sub(r'Role ',r'',info1)
            info1 = re.sub(r'Sex ',r'',info1)
            info1 = re.sub(r'Age ',r'',info1)
            info1 = re.sub(r'Birthplace\n',r'',info1)
            info1 = info1.split('\n')
            del info1[-1]
            
            # Parse the source information.
            source1 = source1.split('\n')
            del source1[-1]
            
            # Prepare the info to write to a csv.
            write = [re.sub(r'\,',r';', x) for x in total] + [re.sub(r'\,',r';', x) for x in info1] + [re.sub(r'\,',r';', x) for x in source1]
        
            # Write to a csv.
            while True:
                try:
                    self._write_csv(pid + ',' + ','.join(write) + '\n')
                    break
                except:
                    sleep(10)
                    pass    
                
            # Close any superfulous windows.
            while len(driver.window_handles) > 1:
                driver.switch_to_window(driver.window_handles[-1])
                driver.close()
                
            # Switch back to the main window.
            driver.switch_to_window(driver.window_handles[-1])
            
        # Turn the timer off.
        self._timer('off', row_count=row_count)
    
    # Retry the failed ids.
    for pid, y in failed:            
        # Get the webpage.
        if re.search('[Aa]ncestry', y):
            continue
        driver.get(y)
        
        # Reset the variables.
        text, info, info1, source1, total = ['']*5

        try:
            # Make sure the page is loaded.
            text = ''
            while text == '':
                text = driver.find_element_by_css_selector('html').text
            
            # Get through the first shadow root.
            root1 = driver.find_element_by_tag_name('record-details')
            shadow_root1 = expand_shadow_element(driver, root1)
            
            # Get through the second shadow root.
            root2 = shadow_root1.find_element_by_css_selector('record-details-extra-fields')
            shadow_root2 = expand_shadow_element(driver, root2)
            
            # Click to expand the extra information tab.
            shadow_root2.find_element_by_class_name('expander').click()
    
            # Grab the text again.
            text = driver.find_element_by_css_selector('html').text
    
            # Separate out the main person information.
            info = re.search('(Name:[\s\S]+?)Household Role Sex Age Birthplace',text).group(1)
        except KeyboardInterrupt:
            sys.exit(1)
        except:
            print('Failed Full Info {}...'.format(pid))
            failed.append((pid, y))
            continue
        
        try:
            # Separate the main family information.
            info1 =  re.search('(Household Role Sex Age Birthplace[\s\S]+?)Tools\n',text).group(1)
        except KeyboardInterrupt:
            sys.exit(1)
        except:
            print('Failed Family Info {}...'.format(pid))
            failed.append((pid, y))
            continue
    
        try:
            # Separate out the main source information.
            source1 = re.search('(Document Information:\n)([\s\S]+?)Citing this Record\n',text).group(2)
        except KeyboardInterrupt:
            sys.exit(1)
        except:
            print('Failed Source Info {}...'.format(pid))
            failed.append((pid, y))
            continue
            
        # Parse the main person information.
        total = info
        total = total.split('\n')
        del total[-1]
        
        # Parse the main family information.
        info1 = re.sub(r'Household ',r'',info1)
        info1 = re.sub(r'Role ',r'',info1)
        info1 = re.sub(r'Sex ',r'',info1)
        info1 = re.sub(r'Age ',r'',info1)
        info1 = re.sub(r'Birthplace\n',r'',info1)
        info1 = info1.split('\n')
        del info1[-1]
        
        # Parse the source information.
        source1 = source1.split('\n')
        del source1[-1]
        
        # Prepare the info to write to a csv.
        write = [re.sub(r'\,',r';', x) for x in total] + [re.sub(r'\,',r';', x) for x in info1] + [re.sub(r'\,',r';', x) for x in source1]
    
        # Write to a csv.
        while True:
            try:
                self._write_csv(pid + ',' + ','.join(write) + '\n')
                break
            except:
                sleep(10)
                pass    
            
        # Close any superfulous windows.
        while len(driver.window_handles) > 1:
            driver.switch_to_window(driver.window_handles[-1])
            driver.close()
            
        # Switch back to the main window.
        driver.switch_to_window(driver.window_handles[-1])
    
    # Quit the driver.
    driver.quit()
    '''
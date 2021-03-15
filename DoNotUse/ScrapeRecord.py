# -*- coding: utf-8 -*-
"""
Created on Fri Jun  1 12:51:52 2018

@author: tanne
"""

import sys, os
sys.path.append(r'R:\JoePriceResearch\Python\Anaconda3\Lib\site-packages')
import pandas as pd
import requests
import re
from time import sleep

def ScrapeRecord(self, arks=True, report=False):
    '''
    This scrapes all of the information from a set of arks (or description ids
    if specified). It will save an individual output file for each record
    collection, i.e. if you fed in both 1900 and 1910 census arks, you would
    get two outfiles.
    
    The infile should be one column of ids, and one column of arks, in that
    order, with no headers.
    
    Parameters
    ----------
    arks       - True if your ids are arks, false if they are description ids.
    report     - Print any error messages.
    '''
    # Specify the needed parameter.
    if arks == True:
        par = 'personas'
    else:
        par = 'records'
        
    # Read the file and remove any missing fsids.
    try:
        # Read the outfile.
        max1 = len(pd.read_csv(self.outfile[:-4] + '.csv', header=None))
        
        # Read the infile.
        if self.infile[:-3] == 'dta':
            df = pd.read_stata(self.infile, header=None)[[0,1]]
        else:
            df = pd.read_csv(self.infile, header=None)[[0,1]]
        
        # Fix the data to start where we left off.
        df = df.iloc[max1:]
        
    except FileNotFoundError:
        # Read the infile if the outfile does not exist yet.
        df = pd.read_csv(self.infile, header=None)[[0,1]].dropna()
        
    except pd.errors.EmptyDataError:
        print(sys.exc_info()[0])
        # Read the infile if the outfile exists but is empty.
        df = pd.read_csv(self.infile, header=None)[[0,1]].dropna()
        
    except:
        raise
        
    # Initialize a dictionary with lists of columns.
    cols = {}
    
    # Loop over the arks.
    for num, x in enumerate(df[1]):
        
        # initializing a variable to skip problematic ids
        skip = False
        
        # Start the timer.
        self._timer('on')
        
        # Make the request.
        for i in range(10):
            # Query the API.
            try:
                pull = requests.get('https://api.familysearch.org/platform/records/{0}/{1}'.format(par, x), 
                             headers={'Authorization': 'Bearer %s' %(self.token), 'Accept':'application/json'})
            except:
                print('Struggling to access R-Drive...')
                sleep(10)
                
            if report:
                print(pull.status_code)

            # Continue until we get a valid response in case we are throttled.
            if pull.status_code != 200 and pull.status_code != 204 and pull.status_code != 401:
                if pull.status_code == 429 and report:
                    print('Throttled!')
                else:
                    print('There is a potential issue, status code: ' + str(pull.status_code))
                    print(f'The pull broke on the arkid : {x}') #Yes the f is supposed to be there!
                sleep(10)
            elif pull.status_code == 401:
                self.token = self.Authenticate()
            else:
                break
            if i == 9:
                skip = True
                print('The problem listed above occured 10 times in a row, moving on...')
        
        # Ensure we got a 200.
        if pull.status_code == 204 or skip:
            continue
        
        # Get the values back from the dictionary.
        mydict = {}
        mydict, count = Iterate(pull.json(), mydict)
        
        # Keep only info for our main person.
        for token, value in mydict.items():
            if token != 'sort_token':
                try:
                    mydict[token] = value.split(';')[count]
                except:
                    mydict[token] = ''
        
        # Get the source name.
        record = re.sub(' |, ', '_', pull.json()['sourceDescriptions'][0]['titles'][0]['value']) + '.csv'
        
        # Coerce the dictionary to a data frame.
        info = pd.DataFrame(mydict, index=[0])
        
        # Make sure the ark is a column.
        info['ark'] = x
        info['uid'] = df[0].iloc[num]
        
        # Get the length of the original columns.
        try:
            length = len(cols[record])
        except:
            length = 0
        
        # Check the column dictionary, and append at the end if necessary.
        if record in cols.keys():
            # Make sure all of the necessary columns exist.
            for col in cols[record]:
                # Make the column if it doesn't exist.
                if col not in info.columns:
                    info[col] = ''
            
            # Get the right column ordering.
            for col in info.columns:
                # Append to the end if it is not in the list.
                if col not in cols[record]:
                    cols[record].append(col)
            
            # Order the columns correctly.
            info = info[cols[record]]
        else:
            # Initialize the columns to keep track of the order.
            cols.update({record : info.columns.tolist()})
        
        # Append to that source file.
        if os.path.isfile(record):
            # If the new data frame has more columns, rewrite entirely.
            if len(cols[record]) > length:
                try:
                    # Read the old file.
                    temp = pd.read_csv(record)
                except UnicodeDecodeError:
                    temp = pd.read_csv(record, encoding='latin')
                
                # Append and write.
                temp = temp.append(info) # , sort=False)
                temp.to_csv(record, index=False)
                
                # Update the column tracker and delete temp.
                cols[record] = temp.columns.tolist()
                del temp
                
            else:
                info.to_csv(record, index=False, header=False, mode='a')
        else:
            info.to_csv(record, index=False)
            
        # Write the outfile to keep track of where we are and delete info.
        self._write_csv(str(df[0].iloc[num]) + ',' + str(x) + '\n')
        del info
        
        # Turn the timer off. For now we will sleep for half a second so as to not be blocked.
        sleep(.5)
        self._timer('off', row_count=len(df))
        
    print('Congratulations! You sucessfully scraped some records! Each different kind of source has save a new file in your directory.')

            

def Iterate(dictionary, mydict):
    '''
    Iterate recursively through the full json and find the actual information.
    
    Parameters
    ----------
    dictionary - The actual json from the API.
    mydict     - An empty dictionary.
    
    Returns
    -------
    A dictionary with the variable names and values.
    '''
    # Figure out which person we are interested in.
    try:
        keep = dictionary['description'][4:]
        for count in range(len(dictionary['persons'])):
            if keep == dictionary['persons'][count]['id']:
                break
    except:
        count = 0
        pass
    
    # Initiate label and check.
    lab = ''
    check = False
    
    # Loop over each token and value from the json.
    for token, value in dictionary.items():
        # If the value is a dictionary, call the function again and continue.
        if isinstance(value, dict):
            Iterate(value, mydict)
            continue
        
        # If the value is a list, call the function again for each nested dictionary.
        elif isinstance(value, list):
            for x in value:
                if isinstance(x, dict):
                    Iterate(x, mydict)
                    continue
            continue
        
        # Get the variable name if the label is correct and mark check as true.
        if token == 'labelId':
            lab = value
            check = True
        
        # Get the variable value and update the dictionary if we don't already have that variable.
        if check == True and token == 'text':
            if lab.lower() not in mydict.keys():
                # Initialize the key if it doesn't exist yet.
                mydict.update({lab.lower() : re.sub(';',':',value)})
            else:
                # Append all of the data together.
                mydict[lab.lower()] = mydict[lab.lower()] + ';' + re.sub(';',':',value)
            # Reset check.
            check = False
      
    # Return the dictionary.
    return mydict, count
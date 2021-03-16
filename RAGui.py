# -*- coding: utf-8 -*-
"""
Created on Thu May 31 08:20:48 2018

@author: tannerse
"""

import sys

sys.path.append(r'R:\JoePriceResearch\Python\Anaconda3\Lib\site-packages')

import pandas as pd
import re

from selenium.common.exceptions import WebDriverException

def RAGui(self, sheet, last_col):
    '''
    Defines a simple RA gui to interact with whatever Google Sheet they are 
    working on. It allows them to specify input columns and will sequentially
    ask for input after displaying the information for the current person they
    are working on and pulling up the FamilySearch page.
    
    Fail safe measures include making you verify the input columns if not empty
    not overwriting someone else's name, and breaking if you put a batch of 0.
    
    Parameters
    ----------
    sheet      - The url for the Google Sheet they are working on.
    last_col   - The last column where data is housed in the Sheet.
    '''
    # Get the important part of the url.
    sheet = re.search(r"(?<=spreadsheets/d/)(.+)(?=/edit)", sheet)[1]

    # Read the whole sheet into a data frame.
    df = pd.DataFrame(self._google_read(sheet,'Sheet1!A:{}'.format(last_col))).fillna(value='')

    # Get the correct columns.
    df.columns = df.iloc[0]
    df = df.reindex(df.index.drop(0))
    
    # Get the input for which column to write a name and what the name is.
    print('\n\nSelect the number of the column where you fill in your name:\n')
    for num, x in enumerate(df.columns):
        print('\t{0} - {1}'.format(num, x))
    choice = int(input())
    col = df.columns[choice]
    
    # Figure out the fsid column.
    print('\n\nSelect which column is the fsid column:\n')
    for num, x in enumerate(df.columns):
        print('\t{0} - {1}'.format(num, x))
    fsid_col = df.columns[int(input())]
    
    # Figure out the input columns.
    print('\n\nSelect which columns are input columns separated by spaces:\n')
    for num, x in enumerate(df.columns):
        print('\t{0} - {1}'.format(num, x))
    input_cols = str(input()).split(' ')
    
    # Figure out the display columns.
    print('\n\nSelect which columns you want displayed separated by spaces:\n')
    for num, x in enumerate(df.columns):
        print('\t{0} - {1}'.format(num, x))
    display_cols = str(input()).split(' ')
    display_cols = [df.columns[int(y)] for y in display_cols]
    
        
    # Get the column letter.
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    col_let = letters[choice]
    
    # Get the name.
    name = str(input('Input your name: '))
    
    # Login to FamilySearch.
    driver = self._login()
    
    # Loop until finished.
    while True:
        if int(input('Enter 1 for another batch: ')) == 1:
            pass
        else:
            break
        
        # Get the batch size.
        batch = int(input('Input how many rows do you want to take: '))
        
        # Ensure we don't overwrite someone else's name.
        last_index = df.loc[df['{}'.format(col)] == ''].index.values.astype(int)[0]

        test = list(self._google_read(sheet,'Sheet1!{0}{1}:{0}{2}'.format(col_let, last_index+1, last_index+1+batch)))

        if test != [[]]*batch and test != []:
            counter = 0
            for y in test:
                if y == []:
                    counter += 1
            print('We are going to limit you batch to {} to not overwrite someone\'s work.'.format(counter))
            batch = counter
            
        # Ensure our input columns are empty.
        for z, y in enumerate(input_cols):
            # Read the sheet.
            test = list(self._google_read(sheet,'Sheet1!{0}{1}:{0}{2}'.format(letters[int(y)], last_index+1, last_index+1+batch)))
        
            # Make sure it is empty.
            if test != [[]]*batch and test != []:
                print('\n\nInput column "{}" not empty, please check.'.format(df.columns[int(y)]))
                print('Reenter the number of the correct input column, or "d" to delete the entry:\n')
                for num, x in enumerate(df.columns):
                    print('\t{0} - {1}'.format(num, x))
                check = str(input())
                if check == 'd':
                    del input_cols[z]
                else:
                    input_cols[z] = check
        
        # Write the name to the Google sheet.
        self._google_write(sheet,'Sheet1!{0}{1}:{0}{2}'.format(col_let, last_index+1, last_index+1+batch), text=[name]*batch)
        
        # Quit if batch of 0 specified.
        if batch == 0:
            break
        
        # Loop over ids.
        for num, x in enumerate(df['{}'.format(fsid_col)].iloc[last_index-1:last_index+batch-1]):
            # Get the page of the first person and display the information.
            driver.get('https://www.familysearch.org/tree/person/details/{}'.format(x))
            
            # Print the information.
            print('\n')
            for y in display_cols:
                print(y + ': ' + df[y].iloc[last_index-1+num])
            print('\n')
        
            # Input the information for the columns.
            ans = ''
            for y in input_cols:
                # Get the information
                ans = str(input('Input "{}", or "q" to quit: '.format(df.columns[int(y)])))
                
                # Quit if specified.
                if ans == 'q':
                    break
                
                # Write to the Google sheet.
                self._google_write(sheet,'Sheet1!{0}{1}:{0}{2}'.format(letters[int(y)], last_index+1+num, last_index+1+num), text=[ans])
            
            # Quit if specified.
            if ans == 'q':
                # Erase the names from the Google sheet.
                self._google_write(sheet,'Sheet1!{0}{1}:{0}{2}'.format(col_let, last_index+1+num, last_index+1+batch), text=['']*(batch-num))
                break
            
            # Make sure we use an active window.
            try:
                driver.switch_to_window(driver.window_handles[0])
            except WebDriverException:
                driver.quit()
                driver = self._login()
        
        # Quit if specified.
        if ans == 'q':
            break
            
        # Reread the whole sheet into a data frame.
        df = pd.DataFrame(self._google_read(sheet,'Sheet1!A:{}'.format(last_col))).fillna(value='')
        
        # Get the correct columns.
        df.columns = df.iloc[0]
        df = df.reindex(df.index.drop(0))      
    
    # Quit the driver.
    print('\nGood Work!')
    driver.quit()
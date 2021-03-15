# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 11:42:59 2018

@author: bbranchf

This function takes a file of arks and writes a file with the pids that are 
attached to those arks, if any. The outfile only writes anything if there is
a pid attached so it will in nearly every case have fewer rows than the infile.

The average time per arkid is around 0.007-0.008s on a sample of records that
had a rather low proportion of records attached so this may be an underestimate
of the average of an arbitrary set of arkids. #estimated with 7aug2018 version
Taking the time of 0.008s per record that means we should get 100,000 arks done
in about 13.3 minutes. For a larger scale reference, that would mean 
getting every pid attached to the 1920 United States census in a little under
10 days of the program running constantly

This is what the repsonse for a pid should look like
[{'parentChildRelationships': [{'contributorId': 'M1L3-X9J',
    'entityId': '998D-5KV',
    'modified': 1510682364037,
    'tfEntityRefId': 'e1c85c94-5dee-4b89-ae37-a740414e53dc'}],
  'sourceId': '9P4D-NZ2'},
 {'persons': [{'contributorId': 'M1L3-X9J',
    'entityId': 'LYZZ-73Y',
    'modified': 1510682371328,
    'tags': ['Death', 'Gender', 'Birth', 'Name'],
    'tfEntityRefId': 'f297e6d0-10a9-42f2-a042-6b8f3c0f637d'}],
  'sourceId': '9P4D-N67'}]

I don't know what the parentChildRelationships does as the entityIds don't seem
to be pids or arks. A person may come up in the person/details/{FSID} page but
it will be used as an inner id which is a weird thing that comes up when you
try to use ark ids as pids.
"""

import re
import time

import json
import requests
import pandas as pd


def GetPidFromArk(self, ark_col=1, header=0, max_records=75, token=None):
    """
    This function takes a list of arks and makes a crosswalk of arks-pids as output.
    This will run faster and more consistently than its predecessor, PidFromArk.
    
    Note: I used the timer method for the class but the time remaining that is	
    		reported seems to be the total time estimate and not time remaining
    	
    Parameters
    ---------
    ark_col (int): the column that the arks are located in
    header (int): which column has headers, as used in pd.read_{filetype}
    max_records (int): the most records we can get from the call at a time. This was 75
    					at the time it was written but is not necessarily the case if the
    					website changed how it does things. It can be reduced and still 
    					work but will run slower for no benefit, this is not recommended.
    token (str): In the case that you would like to submit your own API token rather than
    			using the class default you can put it in here
    
    Returns
    -------
    A pandas dataframe version of the file that the function writes while running
    """
    
    # Assign the infile appropriately.
    ark_pid = self.infile
    
    # Check to see what type of file the input is and read it.
    if ark_pid[-3:] == 'csv':
        ark_df = pd.read_csv(ark_pid)
    elif ark_pid[-3:] == 'dta':
        ark_df = pd.read_stata(ark_pid)
    elif ark_pid[-3:] == 'lsx':
        ark_df = pd.read_excel(ark_pid)
        
    # get the class token if none was passed manually
    if token is None:
        token = self.Authenticate()
    
    # opening a file and a requests session to be used throughout the process
    with open(self.outfile, 'w') as outfile, requests.Session() as session:

        # these will be passed in with each request in the session
        session.headers.update({'Authorization':f'Bearer {token}',
                                'Accept':'application/json',
                                'Content-type': 'application/json'})

        row_count = ark_df.shape[0]
        
        # writing headers
        outfile.write('ark,pid\n')
        
        # establishing the node to access
        url = 'https://www.familysearch.org/service/tree/links/sources/attachments'
        
        URIs = []
        for index, ark in enumerate(ark_df.iloc[:,ark_col]):

            # setting the timer
            self._timer('on')
            
            URIs.append(f'https://familysearch.org/ark:/61903/1:1:{ark}')
            if len(URIs) == max_records or index == row_count - 1:
                try:
                    for i in range(5):
                        response = session.post(url, data=json.dumps({'uris':URIs}))
                        
                        #print(response.status_code)
                        # good response
                            
                        if response.status_code == 200:
                            # grabbing the attached person if there is one
                            if response.json() != {}:
                                info = response.json()['attachedSourcesMap']
                                # ! BOTTLENECK ! : Looping through all of the pids,
                                # how can we prevent this?
                                # if not prevent, minimize the cost of it
                                for full_ark in info.keys():
                                    for attachment in info[full_ark]:
                                        if 'persons' in attachment.keys():
                                            cached_ark = re.search(r"(?<=1:1:)([A-Z0-9]{4}-[A-Z0-9]{3,4})",full_ark).group(1)
                                            outfile.write(f"{cached_ark},{attachment['persons'][0]['entityId']}\n")
                            URIs = []
                            break
                            
                        # throttled, I don't think this will actually happen on
                        # this code as it isn't really an API call
                        elif response.status_code == 429:
                            wait = (int(response.headers['Retry-After'])*1.1)
                            print('Throttled, waiting {0: .1f} seconds!'.format(wait))
                            time.sleep(wait)
                            
                        # not authorized, get a new API token
                        elif response.status_code == 401:
                            token = self.Authenticate()
                            
                        # bad request
                        elif response.status_code == 400:
                            print('Bad Request')
                            URIs = []
                            continue
                            
                        # some other status code
                        else:
                            print('\nPotential Error, Status code:',
                                  response.status_code, '\n')
                            if i == 4:
                                print(f'Could not get values around line {index}, moving on')
                                URIs = []
                                
                except Exception as e:
                    print(e)
                    URIs = []
                    

            
                # report on the progress and time
                if index % 1800 == 1799:
                    print(index + 1, f'of {row_count}')
                    self._timer('off', row_count=row_count, numobs=max_records,
                                ndigits=4)
        
    print('\nPIDs Collected')
    # I figured that this functionality may be desired sometime
    return pd.read_csv(self.outfile,header=0)


# some tests to get the function working
if __name__ == '__main__':
    # testing 
    url = 'https://www.familysearch.org/service/tree/links/sources/attachments'
    token = '48f2ca75-2c56-4413-93f4-69a0b084be27-aws-prod' # 6 AUG 2018 4:30 PM
    arks = ['M355-KFL','M355-4BF','M35P-57P','2SZ5-1G5']
    URIs = []
    ark_cache= []
    for ark in arks:
        URIs.append(f'https://familysearch.org/ark:/61903/1:1:{ark}')
        ark_cache.append(ark)
    file = r'R:\JoePriceResearch\RA_work_folders\Ben_Branchflower\thisisatest.csv'
    with requests.Session() as session, open(file, 'w') as outfile:
        session.headers.update({'Authorization':f'Bearer {token}',
                        'Accept':'application/json',
                        'Content-type': 'application/json'})
        response = session.post(url, data=json.dumps({'uris':URIs}))
        response = response.json()['attachedSourcesMap']
        for ark in ark_cache:
            if f'https://familysearch.org/ark:/61903/1:1:{ark}' in response.keys():
                for attachment in response[f'https://familysearch.org/ark:/61903/1:1:{ark}']:
                    outfile.write(f"{ark},{attachment['persons'][0]['entityId']}\n")

           
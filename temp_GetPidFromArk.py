# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 11:42:59 2018

@author: bbranchf
"""

import requests
import pandas as pd
import time
import json



def GetPidFromArk(self, header=None, max_records=75, token=None):
    
    # Assign the infile appropriately.
    ark_pid = self.infile
    
    # Check to see what type of file the input is and read it.
    if ark_pid[-3:] == 'csv':
        ark_df = pd.read_csv(ark_pid, header=header)
    elif ark_pid[-3:] == 'dta':
        ark_df = pd.read_stata(ark_pid, header=header)
    elif ark_pid[-3:] == 'lsx':
        ark_df = pd.read_excel(ark_pid, header=header)
        
    # get the class token if none was passed manually
    if token is None:
        token = self.Authenticate()
    
    # opening a file and a requests session to be used throughout the process
    with open(self.outfile, 'w') as outfile, requests.Session() as session:
        # these will be passed in with each request in the session
        session.headers.update({'Authorization':f'Bearer {token}',
                                'Accept':'application/json',
                                'Content-type': 'application/json'})

        # this list will be stuck onto the dataframe and returned
        arks = ark_df.iloc[:,1]
        row_count = len(arks)
        
        # setting the timer
        self._timer('on')
        
        # writing headers
        outfile.write('uid,ark,pid')
        
        URIs = []
        arks = []
        for index, ark in enumerate(arks):
            URIs.append('https://familysearch.org/ark:/61903/1:1:{ark}')
            arks.append(ark)
            url = f'https://www.familysearch.org/service/tree/links/sources/attachments'
            if len(URIs) == max_records:
                response = session.post(url, data=json.dumps({'uris':URIs}))
                # good response
                if response.status_code == 200:
                    # grabbing the attached person if there is one
                    info = response.json()['attachedSourcesMap']
                    for attachment_list in info.values():
                        for attachment in attachment_list:
                            outfile.write(f"{ark_df.iloc[index,0]},{ark},{attachment['persons'][0]['entityId']}\n")
                    URIs = []
                    arks = []
                # throttled, I don't think this will actually happen on
                # this code as it isn't really an API call
                elif response.status_code == 429:
                    wait = (int(response.headers['Retry-After'])*1.1)
                    print('Throttled, waiting {0: .1f} seconds!'.format(wait))
                    time.sleep(wait)
                # some other error
                else:
                    print('\nPotential Error, Status code:',
                          response.status_code, '\n')
                # report on the time 
                if index % 100 == 0:
                    print(index, f'of {len(arks)}')
                    self._timer('off', row_count)
                
    return pd.read_csv(self.outfile,header=0)

if __name__ == '__main__':
    # testing 
    url = 'https://www.familysearch.org/service/tree/links/sources/attachments'
    token = '10b7ef2d-c629-4113-a374-08b76c4c0311-aws-prod' # 3 AUG 2018 4:10 PM
    URIs = []
    arks= []
    ark = 'M355-KFL'
    URIs.append(f'https://familysearch.org/ark:/61903/1:1:{ark}')
    arks.append(ark)
    ark = 'M355-4BF'
    URIs.append(f'https://familysearch.org/ark:/61903/1:1:{ark}')
    arks.append(ark)
    ark= 'M35P-57P'
    URIs.append(f'https://familysearch.org/ark:/61903/1:1:{ark}')
    arks.append(ark)
    ark = '2SZ5-1G5'
    URIs.append(f'https://familysearch.org/ark:/61903/1:1:{ark}')
    arks.append(ark)
    file = r'R:\JoePriceResearch\RA_work_folders\Ben_Branchflower\thisisatest.csv'
    with requests.Session() as session, open(file, 'a') as outfile:
        session.headers.update({'Authorization':f'Bearer {token}',
                        'Accept':'application/json',
                        'Content-type': 'application/json'})
        response = session.post(url, data=json.dumps({'uris':URIs}))
        response = response.json()['attachedSourcesMap']
        for ark in arks:
            if f'https://familysearch.org/ark:/61903/1:1:{ark}' in response.keys():
                for attachment in response[f'https://familysearch.org/ark:/61903/1:1:{ark}']:
                    outfile.write(f"{ark},{attachment['persons'][0]['entityId']}\n")

@jit                  
def write_output(index,info,ark_df):
    for attachment_list in info.values():
        for attachment in attachment_list:
            outfile.write(f"{ark_df.iloc[index,0]},{ark},{attachment['persons'][0]['entityId']}\n")

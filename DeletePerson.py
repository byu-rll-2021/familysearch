# -*- coding: utf-8 -*-
"""
Deletes pid from family tree. Can be used in conjunction with AddPerson to delete 
faulty added pids. Pid can only be deleted if the Family Search account logged into is the sole 
contributor to the person.

created by Ben Busath 9/3/2019
"""
import pandas as pd 
import requests
import time

def DeletePerson(self,token=None,pid_col=0):
    if token == None:
        token=self.Authenticate()
    
    df = pd.read_csv(self.infile)
    
    row_count=len(df)
    # opening a file and a requests session to be used throughout the process
    with requests.Session() as session:
        
    # these will be passed in with each request in the session
        session.headers.update({'Authorization' : f'Bearer {token}', 
                                'Content-type':'application/x-gedcomx-v1+json'})
    
        for index, pid in enumerate(df.iloc[:,pid_col]):
            self._timer('on')
            response=session.delete('https://api.familysearch.org/platform/tree/persons/{}'.format(pid))
            if response.status_code==204:
                #successful delete
                pass
            elif response.status_code==403:
                print('cannot delete {}, person contributed to by other users'.format(pid))
                
            elif response.status_code == 429:
                wait = (int(response.headers['Retry-After'])*1.1)
                print('Throttled, waiting {0: .1f} seconds!'.format(wait))
                time.sleep(wait)
            
            elif response.status_code==404:
                print('cannot delete {}, requested person not found'.format(pid))
                
            elif response.status_code==410:
                print('cannot delete {}, requested person already deleted or merged'.format(pid))
                
            if index % 500 == 499:
                print(index + 1, f'of {row_count}')
                self._timer('off', row_count=row_count, numobs=1,
                            ndigits=4)


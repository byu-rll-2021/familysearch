# -*- coding: utf-8 -*-
"""
Created on Fri Jan 19 14:50:42 2018

@author: cookchr2
"""
import pandas as pd
import requests

def check_if_deleted(self):
    data = pd.read_csv(self.infile, header=None)
    token = '4bc485db-889f-4a9b-8b82-5508d01ecbba-production '
    ids = 'LVBM-5WS'
    info = requests.get('http://www.familysearch.org/platform/tree/persons?pids=%s' %(ids), 
                   headers={'Authorization': 'Bearer %s' %(token), 'Accept':'application/json'})
    jay = info.json

print()


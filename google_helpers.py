# -*- coding: utf-8 -*-
"""
Created on Fri Apr 27 14:28:47 2018

@author: bbranchf

This is a file of helper functions for the FamilySearch class.
The functions are all related to using the google API.

"""

import sys

sys.path.append(r'R:\JoePriceResearch\Python\Anaconda3\Lib\site-packages')

import os
import httplib2

from googleapiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

flags = None
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = "Joe's RA's"


def _get_credentials(self):
    '''
    Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    '''
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        # if flags:
        credentials = tools.run_flow(flow, store, flags)
        # else: # Needed only for compatibility with Python 2.6
        #    credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials
        

def _google_read(self, spreadsheet,_range):
    '''
    This runs the Google API to read in the spreadsheet.
    
    spreadsheet - The Google Spreadsheet id.
    
    _range - The range of cells in the spreadsheet.
    '''
    credentials = self._get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    spreadsheetId = spreadsheet
    rangeName = _range
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])

    if not values:
        return values
    else:
        return values
    
    
def _google_write(self, spreadsheet,_range,text=None,value_range_body=None):
    '''
    This writes to the spreadsheets through the Google API.
    
    spreadsheet - The Google Spreadsheet id.
    
    _range - The range of cells in the spreadsheet.
    
    text - Text to write to a single cell.
    
    value_range_body - Spreadsheet dictionary to describe text to be written.
    '''
    credentials = self._get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
        'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
        discoveryServiceUrl=discoveryUrl)

    spreadsheetId = spreadsheet
    rangeName = _range
    value_input_option = 'RAW'
    if value_range_body == None:
        value_range_body = {
            'range' : rangeName,
            'majorDimension' : 'COLUMNS',
            'values' : [
                text,
            ],
        }

    request = service.spreadsheets().values().update(spreadsheetId=spreadsheetId, range=rangeName, valueInputOption=value_input_option, body=value_range_body)
    request.execute()
# -*- coding: utf-8 -*-
"""
This has the authenticate method for the FamilySearch class and a function that
does the same thing as the authenticat emethod but as a stand-alone function
that can be used independently of the class.

Created on Tue Oct 24 17:17:41 2017
Updated on 9 July 2019 by Ben Branchflower

@author: tannerse
"""

def Authenticate(self):
    '''
    Grabs a new access token
    
    Returns
    -------
    token    - API access token
    '''
    
    # formatting request headers
    self.session.headers.update({'accept':'application/json',
                            'content-type':'application/x-www-form-urlencoded'})
    
    # authentication resource
    url = 'http://www.familysearch.org/cis-web/oauth2/v3/token'
    
    # we authenticate as a desktop ap, the `password` grant_type
    data =  {'grant_type':'password',
             'client_id':self.CLIENT_ID,
             'username':self.username,
             'password':self.password}
    
    response = self.session.post(url, data)
    
    return response.json()['access_token']


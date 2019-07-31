# -*- coding: utf-8 -*-
"""
This file is for interacting with the search places node of the familysearch 
API.

The documentation can be found at the link below.
https://www.familysearch.org/developers/docs/api/places/Places_Search_resource

This function is intended to be used primarily to check the quality of the 
results returned and provide feedbackon the for familysearch, at least for now.

Author: Ben Branchflower
Created: 29 April 2019
"""

import re
import time

import requests
import pandas as pd


def SearchPlaces(inlist=None, infile=None, outfile=None, token=None,
                 centroid_lat=None, centroid_lon=None, distance=None,
                 parent_place='United States', verbosity=0,
                 columns=[0,1], header=0, write_out=True):
    '''
    Uses a compiled list of places names to receive results from familysearch.
    The function will grab possible place matches, their latitude and longitude
    and some other identifying information about the place.
    
    parameters
    ---------
    inlist - a python object with strings of places to be search that is 
                coercible to a pandas DataFrame type, only one of inlist or
                infile should be used
    infile - a string containing the file with the data
    outfile - a string declaring where the results should be written
    token - a string containing the familysearch api token
    centroid_lat - the latitude of the place to search around
    centroid_lon - the longitude of the place to search around
    distance - the maximum allowable distance from the centroid, in miles
    parent_id - the jurisdiction to search in such as "The United States"
                which will only return places in that are under that umbrella
    verbosity - a declaration o fhow much should be printed, 1 will give
                placenames as they are used and 2 or greater will give results
                as well. Anything else will have 
    columns - if the infile has the dataa to be used in a format other than 
                2 columns with an index and then the places
    columns - an indexed object with the 0th element being index column and the 
                1st index the places column
    header - the header parameter to be given to the pandas read_filetype
                function. A header is always used for dta filetypes
    '''
    # check for the input to be clear
    if infile is not None and inlist is not None:
        to_use = input('''Both a python object and a file were declared as
                       inputs. Please type list or file and then press enter''')
        if re.search('^l.*', to_use):
            infile = None
        else:
            inlist = None
        SearchPlaces(inlist=inlist, infile=infile, outfile=outfile, token=token,
                     columns=columns, header=header, write_out=write_out,
                     centroid_lat=centroid_lat, centroid_lon=centroid_lon,
                     distance=distance, parent_place=parent_place,
                     verbosity=verbosity)
    
    # getting consistent object type to work with
    if infile is not None:
        in_places = _read_data(infile=infile, columns=columns, header=header)
    if inlist is not None:
        in_places = pd.DataFrame(inlist)
    
    # getting a valid token
    if token is None:
        try:
            token = Authenticate('benbranchflower','chimps58') # I assumed this would be implemented with the
        except NameError:
            print('The Authenticate function that was called has not been declared,',
                  'please pass in an api token you get from http://www.familysearch.org/platform')
            return 0
    
    # establishing a connection
    session = requests.Session()
    
    # filling in appropriate headers
    session.headers.update({'Authorization':f'Bearer {token}',
                            'accept': 'application/json',
                            'content-type':'json'})
    
    # making basic search dictionary
    try:
        search_dict = _make_search_fields(parent_place, centroid_lat,
                                          centroid_lon, distance)
    except KeyError:
        parent_place = input('the parent_place field may have been typed incorrectly, please type the desired place and press enter')
        SearchPlaces(inlist=inlist, infile=infile, outfile=outfile, token=token,
                     columns=columns, header=header, write_out=write_out,
                     centroid_lat=centroid_lat, centroid_lon=centroid_lon,
                     distance=distance, parent_place=parent_place,
                     verbosity=verbosity)

    results = []
    
    # making headers
    with open(outfile, 'w') as write_out:
        write_out.write('Search String, Result String, FS Score\n')
    
    with open(outfile, 'a') as write_out:
        # looping over places input
        for place_name in in_places.iloc[:,0]:
            try:
                if verbosity > 0:
                    print(f'Search String: {place_name}')
            except UnicodeDecodeError:
                continue
            try:
                # getting a json of search results
                search_dict.update({'name':place_name})
                #response = session.post(url='http://api.familysearch.org/platform/places/search',
                #                        data=search_dict)
                
                response = session.get(f'http://api.familysearch.org/platform/places/search?q=name:"{place_name}"+%2bparentId:1~')
                print(response)
                if response.status_code == 200:
                    # matches ranked in order of quality, just use the best
                    best = response.json()['entries'][0]
                    result_name = best['content']['gedcomx']['places'][0]['display']['fullName']
                    if verbosity > 1:
                        print(f"Result String: {result_name}",
                              f"Result Score: {best['score']}\n", sep='\n')
                    results.append([place_name, result_name, best['score']])
                    write_out.write(f"{place_name}, {result_name}, {best['score']}\n")
                else:
                    # report no result
                    if verbosity > 1:
                        print(f"Result String: No result")
                        print(f"Result Score: No result\n")
                    results.append([place_name, 'no result', 'no result'])
                    write_out.write(f"{place_name}, no result, no result\n")
            # vvv This is something that could probably be improved upon though
            # I am unawarae of how to deal with different encodings
            except UnicodeEncodeError:
                if verbosity > 1:
                    print(f"Result String: Bad encoding")
                    print(f"Result Score: Bad encoding\n")
                results.append([place_name, 'Bad encoding', 'Bad encoding'])
    
    # return the data for convenience
    out = pd.DataFrame(results)
    out.columns = ['Search String','Result String', 'Score']
    return out

        
def _read_data(infile, columns=[0,1], header=0):
    '''
    A helper function for SearchPlaces
    This function gets that data and returns a dataframe with the data that
    will be used.
    '''
    if infile is None:
        return None
    
    if infile[-3:] == 'csv':
        df = pd.read_csv(infile, index_col=columns[0], usecols=columns[1],
                         header=header)
    elif infile[-3:] == 'dta':
        df = pd.read_stata(infile)
    elif infile[-3:] == 'lsx':
        df = pd.read_excel(infile, index_col=columns[0], usecols=columns[1],
                           header=header)
    return df
    

def _make_search_fields(parent_place, latitude, longitude, distance):
    '''
    a helper function for SearchPlaces
    This considers the inputs of the function and makes an appropriate string 
    to be used in the requests.
    '''
    place_id_dict = {'United States':'1'}
    
    search_dict = {'name':None}
    if parent_place is not None:
        search_dict.update({'parentId':place_id_dict[parent_place]})
    if latitude is not None:
        search_dict.update({'latitude':latitude,
                            'longitude':longitude,
                            'distance':distance})
    return search_dict


if __name__ == '__main__':
    token = '5fda9ae8-f32e-4d52-a4af-28d88ec6df11-prod ' # obtained 29 April 2019 10:30 AM
    out = SearchPlaces(infile=r'R:\JoePriceResearch\record_linking\projects\birthplaces\bplace_1900_1930.dta',
                       outfile=r'R:\JoePriceResearch\record_linking\projects\birthplaces\bplace_fs_results_w_us.csv',
                       token=token, verbosity=2)
    

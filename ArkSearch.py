# -*- coding: utf-8 -*-
"""
This function searches the records on the census for specific counties in order
to get arks for the individuals in the area. The practice case is on a list of 
counties for the college openings project in the 1880 census.
I do not know if the functionality will be expanded beyond that though the
primary difference should be in the _format_search_string function as that 
prepares the query. The other part are mainly just reading data and looping 
over results.

This could be used to get part or all of the arks of any collection of records
for which we have things to search with. The places is a convenient way of 
limiting the results to less than 5000 in many cases but it could be names,
birth years, parents names or basically anything you can search for in the
FamilySearch record search all of the arks could be obtained with relative ease
using this function with the caveat that only searching on place is currently
supported. (11 May 2019)

If you are trying to obtain the arks from a large collection then it may be 
best to request them from familysearch. We have done this in the past and it 
can often take a long time but it was for things like a census where the time
necessary makes this method unrealistic. 

NOTE:
    I tried to use the response['next'] that the api return for the next page
    of search results and I got a different number of results. I don't 
    understand why this would be the case but apparently we should do the
    string ourselves even though familysearch says they give it to us. It is
    only different in the offset parameter so it isn't incredibly difficult
    and that is what makes the different results even more bizarre
    
    I was originally able to get 500 results at once but now it is capping me
    at 100

Author: Ben Branchflower
Created: 2 May 2019
"""

import os
import re
import string
import time

import pandas as pd
import requests

example_url = "https://www.familysearch.org/service/search/hr/personas?count=75&query=%2Bsurname%3Am*~%20%2Bresidence_place%3A%22Autauga%2C%20Alabama%2C%20United%20States%22~%20%2Bfilm_number%3A1254001&collection_id=1417683&collectionNameFilter=true"



def ArkSearch(file, token, delim=',', collection_id=1417683, count=100, header=0,
              birth_range=None, sleep_time=5, use_place=True):
    '''
    The main function. Reads in data formats a string for the query and then 
    loops over results for it to be compiled
    
    parameters
    ----------
    file - the file with the places to be searched
    delim - the delimiter for the above file default is csv
    count -  an integer saying how many results to get at once. I don't see why
                you would ever want to get less than the maximum,which is the
                default value, but you could if you wanted this function to do
                exactly the same thing slower than it can.
    use_place - a boolean to indicate if you are using residence place
                    some records, such as draft cards, do not use this and you
                    will not find the people you are looking for if you use 
                    event place as residence place
    '''
    # this is the collection id for the 1880 census, change it for other records
    
    # read in search parameters
    search_input = _read_data(file, delim, header)
    
    session = requests.Session()
    
    session.headers.update({'Authorization':f'Bearer {token}'})
    
    full_ark_list = set()
    places_with_missings = []
    places_checked = set()
    
    for i in search_input.index:
        if use_place:
            residence_place = search_input.iloc[i,0]
        else:
            residence_place='no place'
        film_number = search_input.iloc[i,1]
        
        residence_place = re.sub('&','and',residence_place)
        
        if (residence_place, film_number) in places_checked:
            continue
        places_checked.add((residence_place, film_number))
        
        stub = f"https://www.familysearch.org/service/search/hr/personas?count={count}&query="
        if use_place:
            stub = stub + f"%20%2Bresidence_place%3A%22{re.sub(' ', '%20', re.sub(',','%2C', residence_place))}%22"
        if birth_range is not None:
            stub = stub + f"%2Bbirth_year%3A{birth_range}"
        url =  stub + f"%20%2Bfilm_number%3A{film_number}&collection_id={collection_id}"
        
        response = _get_results(url, session, sleep_time)
        try:
            num_results = response['totalHits']
        except TypeError:
            print(residence_place)
            print(film_number)
            print(url)
            print(response.text)
        
        print(residence_place, ':', film_number)
        print('Total hits for place:', num_results)
        
        place_arks = set()
    
        if num_results <= 5000: # 5000 is the maximum depth, need to search by first letter to refine results if there are more
            result_arks = {result['personHit']['person']['url'] for result in response['searchHits']}
            for offset in range(count, num_results, count):
                response = _get_results(url + f'&offset={offset}', session, sleep_time)
                result_arks = result_arks.union({result['personHit']['person']['url'] for result in response['searchHits']})

        else:
            print('more than 5000...')
            for letter in string.ascii_lowercase:
                print(letter)
                stub = f"https://www.familysearch.org/service/search/hr/personas?count={count}&query="
                stub = stub + f'%2Bgivenname%3A{letter}*~'
                if use_place:
                    stub = stub + f"%20%2Bresidence_place%3A%22{re.sub(' ', '%20', re.sub(',','%2C', residence_place))}%22"
                if birth_range is not None:
                    stub = stub + f"%2Bbirth_year%3A{birth_range}"
                url =  stub + f"%20%2Bfilm_number%3A{film_number}&collection_id={collection_id}"
                
                response = _get_results(url, session, sleep_time)
                if response == 'too many':
                    print(f'too many results: {residence_place}')
                    break
                
                try:
                    print(response['totalHits'])
                except TypeError:
                    print('too many results:', residence_place)
                    places_with_missings.append(residence_place)
                    break 
                result_arks = {result['personHit']['person']['url'] for result in response['searchHits']}

                for offset in range(count, response['totalHits'], count):
                    response = _get_results(url + f'&offset={offset}', session,
                                            sleep_time)
                    result_arks = result_arks.union({result['personHit']['person']['url'] for result in response['searchHits']})

                place_arks = place_arks.union(result_arks)
        place_arks = place_arks.union(result_arks)
        
        if len(place_arks) != num_results or num_results == 0:
            places_with_missings.append((residence_place,film_number,len(place_arks)- num_results))
                
        print('Total results found for place:', len(place_arks), '\n')
        
        full_ark_list = full_ark_list.union(place_arks)
    
    return full_ark_list, places_with_missings


def _get_results(url, session, sleep_time):
    """
    a helper function to deal with the different responses
    """
    for i in range(5):
        response = session.get(url)
        if response.status_code == 200:
            break
        elif response.status_code == 400:
            return response
        elif response.status_code == 429:
            time.sleep(sleep_time)
        else:
            print('Error:', response.status_code)
    
    return response.json()

    
def _read_data(infile, delim=',', header=0):
    '''
    A helper function for SearchPlaces
    This function gets that data and returns a dataframe with the data that
    will be used.
    '''
    if infile is None:
        return None
    
    if infile[-3:] in ('csv', 'txt'):
        df = pd.read_csv(infile, header=header, sep=delim)
    elif infile[-3:] == 'dta':
        df = pd.read_stata(infile)
    elif infile[-3:] == 'lsx':
        df = pd.read_excel(infile, header=header)
    return df


if __name__ == '__main__':
    
    os.chdir(r'R:\JoePriceResearch\record_linking\projects\college_openings\data')
    
    token = 'ad6b821c-de99-4354-801e-877051d15591-prod' # 22 May
    resp, prob_places = ArkSearch('county_list.csv',
                                  token=token , delim='$', collection_id=1325221)
    with open('ark_list.csv', 'w') as outfile:
        outfile.write('\n'.join(list(resp)))
    
    os.chdir(r'R:\JoePriceResearch\record_linking\projects\college_openings\data')
    prob_places.to_csv('problem_places.csv', sep='$', index=False)
    
    resp2, prob_places2 = ArkSearch(r'R:\JoePriceResearch\record_linking\projects\college_openings\data\problem_places.csv',
              token=token , delim='$', birth_range='1840-1880')
    with open(r'R:\JoePriceResearch\record_linking\projects\college_openings\data\county_arks.csv', 'a') as outfile:
        outfile.write('\n'.join(list(resp)))
    
    probs = pd.DataFrame(prob_places2)
    os.chdir(r'R:\JoePriceResearch\record_linking\projects\college_openings\data')
    probs.to_csv('problem_places.csv', sep='$', index=False)
    
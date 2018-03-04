
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import pandas as pd
#import numpy as np
import re



def is_good_response(resp):
    """
    Ensures that the response is a html.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 and 
            content_type is not None 
            and content_type.find('html') > -1)

def get_html_content(url):
    """
    Retrieve the contents of the url.
    """
    # Get the html from the url
    try:
        with closing(get(url, stream=True)) as resp:
            content_type = resp.headers['Content-Type'].lower()
            if is_good_response(resp):
                return resp.content
            else:
                # Unable to get the url responce
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))

def get_number_of_pages(url):
    """
    Get the total number of pages to cycle through in the resort page list.
    """
    
    content = get_html_content(url)

    # Get a list of all ski resorts (go through each page)
    html = BeautifulSoup(content, 'html.parser')
    
    pageLinks = html.find("ul", {"id": "pagebrowser1"})
    # Extract the total number of pages
    lastPageNumber = int(re.findall('[0-9][0-9]' ,pageLinks.contents[-2].find('a')['href'])[0])

    # should check for valid 
    return lastPageNumber

def get_basic_resort_statistics(resortUrl):
    """
    Print the basic statistics for the ski resort.
    """

    # Get the contents of the ski resort page.
    resortContent = get_html_content(resortUrl)

    # Extract the HTML
    resortHtml = BeautifulSoup(resortContent, 'html.parser')

    # Get altitude info
    altitudeDescipriton = resortHtml.find("div", {"id": "selAlti"}).contents
    # Account for tooltips in the altitude description.
    if len(altitudeDescipriton) > 2:
        altitude = float(altitudeDescipriton[2].split(" - ")[1].split("m")[0])
    else:        
        altitude = float(altitudeDescipriton[0].split(" - ")[1].split("m")[0])
   
    print("Altitude: " + str(altitude))

    # Add the altitude to the dictionary
    stat = {"Altitude":altitude}

    # Get Slope statistics
    slopeTable = resortHtml.find("table", {"class": "run-table"})
    slopeSatistics = {}
    print("Slope Statistics:")
    for row in slopeTable.findAll("tr"):
        key = row.contents[1].contents[1]
        value = float(row.contents[3].contents[0].split("km")[0])
                
        slopeSatistics[key] = value
        print(key,": ",value)
        stat[key] = value
            
    # Extract the Lift details.
    liftStatistics = {}
    print("Lift numbers:")
    for lift in resortHtml.findAll("div", {"class": "lift-count"}):
        key = lift['title']
        value = int(lift.get_text())
        liftStatistics[key] = value

        print(key,": ",value)
        stat[key] = value
                
    # Extract the ticket prices
    if not resortHtml.findAll("td", {"id": "selTicketA"}):
        adultPrices = 0
    else:
        adultPrices = resortHtml.findAll("td", {"id": "selTicketA"})[0].contents[0]

    if not resortHtml.findAll("td", {"id": "selTicketY"}):
        youthPrices = 0
    else:
        youthPrices = resortHtml.findAll("td", {"id": "selTicketY"})[0].contents[0]

    if not resortHtml.findAll("td", {"id": "selTicketC"}):
        childPrices = 0
    else:
        childPrices = resortHtml.findAll("td", {"id": "selTicketC"})[0].contents[0]

    print("Prices:")
    print("Adult: ",adultPrices,"\nYouth: ",youthPrices,"\nChild: ", childPrices)
    stat["Adult"] = adultPrices
    stat["Youth"] = youthPrices 
    stat["Child"] = childPrices

    return stat


def get_report_scores(resortUrl):
    """
    Print the resort report scores
    """

    # Construct the url for the report.
    reportUrl = resortUrl + "test-result/"

	# Get the content of the report for the resort
    reportContent = get_html_content(reportUrl)

	# Get a list of all ski resorts on the current page
    reportHtml = BeautifulSoup(reportContent, 'html.parser')
    report = reportHtml.findAll("div", {"class": "stars-link-element"})
    
    # rating dictionary
    rating = {}

    # Extract each score for each report attribute.
    for item in report:
        end = item['title'].find("out")
        score = float(item['title'][0:end])
        attribute = item.contents[5].text

        print(attribute,": ",score)
        rating[attribute] = score

    return rating


if __name__ == '__main__':
    '''
    Extraxt data for each ski resort and sort into relevant features.
    '''

    # loop through each page
    # http://www.skiresort.info/ski-resorts/page/<index>/
    
    # Sk resort website url
    url = 'http://www.skiresort.info/ski-resorts/'
    
    #totalPages = get_number_of_pages(url)
    totalPages = 1 # restict to first page while testing.

    resortData = dict()
    index = 0

    for page in range(totalPages):        

        # Consruct the next page with the list of ski resorts.
        if page > 0:
            url = url+"page/"+str(page+1)
        # else: url is unchanged.
        
        # Get the current page contents
        content = get_html_content(url)

        # Get a list of all ski resorts on the current page
        html = BeautifulSoup(content, 'html.parser')
        resorts = html.find("div", {"id": "resortList"})

        # Cycle through each resort
        for resort in resorts:
            if resort != ' ' :
                
                print (index)

                # Identify the country and locations of the resort.
                location = resort.find("div", {"class": "sub-breadcrumb"})
                continent = location.contents[1].contents[0].text
                country = location.contents[1].contents[2].text
                province_state = location.contents[1].contents[4].text
                
                # Get the URL for each resort
                resortUrl = resort.find("a", {"class": "pull-right btn btn-default btn-sm"})['href']
                resortName = resortUrl.split('/')[-2]
                print ("Resort: ",resortUrl)
                
                # Get the contents of the ski resort page.
                stat = get_basic_resort_statistics(resortUrl)

                # Get the report scores
                scores = get_report_scores(resortUrl)

                # Add all the data to the dataframe
                resortData[resortName] = { "URL" : resortUrl, 
                        "Continent" : continent, "Country" : country, "State/Province" : province_state,
                        **stat,
                        **scores}

                index = index + 1

    df = pd.DataFrame.from_dict(resortData, orient='columns')
    
                







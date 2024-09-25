from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup, Tag
import pandas as pd
#import numpy as np
import re
import time


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
    # Be a responisble scraper.
    time.sleep(2)

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
        print('Error during requests to {0} : {1}'.format(url, str(e)))
#        ConnectionError(ProtocolError('Connection aborted.', RemoteDisconnected('Remote end closed connection',)),)

def currencyExtraction(priceString):
    """
    Extract the currency symbol and convert to a description of the currency.
    """
    currencyDict = {'£':'UK Pound','¥':'Japanese Yen','€':'European Euro','AED':'United Arab Emerites',
                    'AMD':'Armenian Dram','ARS':'Argentine Peso','AU$':'Australian dollar',
                    'AZN':'Azerbaijani manat','BAM':'Bosnia convertible mark','BGN':'Bulgarian Lev',
                    'C$':'Canadian Dollar','CLP':'Chiliean Peso','CZK':'Czech koruna',
                    'DKK':'Danish Krone','GEL':'Georgian Lari','HRK':'Croatian Kuna',
                    'HUF':'Hungarian forint','ILS':'Israeli new shekel','IRR':'Iranian rial',
                    'ISK':'Icelandic krona','KGS':'Kyrgyzstani som','KRW':'South Korean won',
                    'KZT':'Kazakhstani tenge','LBP':'Lebanese pound','MKD':'Macedonian denar',
                    'MNT':'Mongolian togrog','NOK':'Norwegian krone','NZ$':'New Zealand Dollar',
                    'PLN':'Polish zloty','RON':'Romanian leu','Rs':'Indian rupee','RSD':'Serbian dinar',
                    'RUB':'Russian ruble','SFr.':'Swiss Franc','Skr':'Swedish krona','TRY':'Turkish lira',
                    'UAH':'Ukrainian hryvnia','US$':'US Dollar','ZAR':'South African rand','Ұ':'Chinese Yuan'}

    [currency, price] = priceString.split()
    if (',' in price):
        [price, extra] = price.split(',')
        

    if (currency in currencyDict):
        return [currencyDict[currency], price]
    else:
        return ['unknown', price]



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

def get_interactive_trail_map(resortName):
    """
    Get the interactive trail map link for the resort.
    """
    # Construct the URL for the trail map
    trail_map_url = f"https://www.skiresort.info/ski-resort/{resortName}/trail-map/"
    
    # Get the contents of the trail map page
    trail_map_content = get_html_content(trail_map_url)
    trail_map_html = BeautifulSoup(trail_map_content, 'html.parser')

    # Initialize the trail map link
    trail_map_link = None

    # Find the interactive trail map section
    trail_map_section = trail_map_html.find("div", {"class": "panel panel-default"})
    if trail_map_section:
        # Look for the list of links
        list_group = trail_map_section.find("ul", {"class": "list-group"})
        if list_group:
            # Extract the first link (or modify to extract specific links as needed)
            first_link = list_group.find("a", {"class": "more-infos"})
            if first_link and 'href' in first_link.attrs:
                trail_map_link = first_link['href']

    return trail_map_link

def get_basic_resort_statistics(resortUrl):
    """
    Print the basic statistics for the ski resort.
    """
    # Get the contents of the ski resort page.
    resortContent = get_html_content(resortUrl)

    # Extract the HTML
    resortHtml = BeautifulSoup(resortContent, 'html.parser')

    # Initialize logo_url, resort_website, and trail_map_link
    logo_url = None
    resort_website = None
    trail_map_link = None

    # Extract the logo URL and resort website
    logo_element = resortHtml.find("div", {"class": "resort-logo"})
    if logo_element:
        img_tag = logo_element.find("img")
        if img_tag and 'src' in img_tag.attrs:
            logo_url = img_tag['src']
            if logo_url.startswith('/'):
                logo_url = f"https://www.skiresort.info{logo_url}"
        
        a_tag = logo_element.find("a")
        if a_tag and 'href' in a_tag.attrs:
            resort_website = a_tag['href']

    # Get the resort name for the trail map link
    resortName = resortUrl.split('/')[-2]

    # Get the interactive trail map link
    trail_map_link = get_interactive_trail_map(resortName)

    # Get altitude info
    if (resortHtml.find("div", {"id": "selAlti"}) != None):
        altitudeDescipriton = resortHtml.find("div", {"id": "selAlti"}).contents
        # Account for tooltips in the altitude description.
        if len(altitudeDescipriton) > 2:
            altitude = float(altitudeDescipriton[2].split(" - ")[1].split("m")[0])
        else:        
            altitude = float(altitudeDescipriton[0].split(" - ")[1].split("m")[0])
    else:
        altitude = 0

    print("Altitude: " + str(altitude))

    # Add the altitude to the dictionary
    stat = {"Altitude": altitude, "Trail Map": trail_map_link}  # Add trail map link

    # Get slope statistics
    slopeTable = resortHtml.find("table", {"class": "run-table"})
    slopeSatistics = {}
    print("Slope Statistics:")
    if (slopeTable is not None):
        for row in slopeTable.findAll("tr"):
            print(row)  # Debugging output to see the row structure
            if len(row.contents) >= 3:  # Ensure there are at least 3 contents
                key = row.contents[0].text.strip()  # Get the description
                distance_text = row.find("td", {"class": "distance"}).text.strip()  # Get the distance text
                
                print("distance_text:", distance_text)  # Debugging output
                # Check if distance_text is not empty and contains "km"
                if distance_text and "km" in distance_text:
                    value = float(distance_text.split("km")[0].strip())  # Get the distance value
                    slopeSatistics[key] = value
                    stat[key] = value
                else:
                    print(f"Distance value is missing or not in expected format: {distance_text}")
            else:
                print("Unexpected structure in row:", row)
                
    # Extract lift numbers
    liftStatistics = {}
    print("Lift numbers:")
    liftGroups = resortHtml.findAll("div", {"class": "lift-info-group"})  # Find all lift info groups

    if liftGroups:
        for lift in liftGroups:
            # Find all lift counts within the lift group
            lift_counts = lift.findAll("div", {"class": "lift-count"})
            
            for lift_count in lift_counts:
                lift_type = lift_count.get("title")  # Get the lift type from the title attribute
                lift_amount = lift_count.find("span", {"class": "lift-amount"})  # Find the amount
                
                if lift_amount:
                    count = lift_amount.text.strip()  # Get the lift count
                    print(f"{lift_type}: {count}")  # Debugging output
                    liftStatistics[lift_type] = int(count) if count.isdigit() else 0  # Store lift count in liftStatistics
                else:
                    print("Lift amount not found in lift count:", lift_count)
    else:
        print("Lift table not found or has unexpected structure.")

    # Extract the ticket prices
    currency = None
    if not resortHtml.findAll("td", {"id": "selTicketA"}):
        adultPrices = 0
    else:
        adultPrices = resortHtml.findAll("td", {"id": "selTicketA"})[0].contents[0]
        [currency, adultPrices] = currencyExtraction(adultPrices)

    if not resortHtml.findAll("td", {"id": "selTicketY"}):
        youthPrices = 0
    else:
        youthPrices = resortHtml.findAll("td", {"id": "selTicketY"})[0].contents[0]
        [currency, youthPrices] = currencyExtraction(youthPrices)

    if not resortHtml.findAll("td", {"id": "selTicketC"}):
        childPrices = 0
    else:
        childPrices = resortHtml.findAll("td", {"id": "selTicketC"})[0].contents[0]
        [currency, childPrices] = currencyExtraction(childPrices)
   
    if currency is None:
        currency = '-'

    print("Prices:")
    print("Adult: ",adultPrices,"\nYouth: ",youthPrices,"\nChild: ", childPrices)
    stat["Adult"] = adultPrices
    stat["Youth"] = youthPrices 
    stat["Child"] = childPrices
    stat["Currency"] = currency
    stat["Logo URL"] = logo_url
    stat["Website"] = resort_website

    return stat, liftStatistics


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
    url = 'https://www.skiresort.info/ski-resorts/europe/'
    
    # totalPages = get_number_of_pages(url)
    totalPages = 2 # restict to first page while testing.
    totalResorts = 4

    resortData = dict()
    index = 0

    # Initialize a list to hold all resort data
    resort_data_list = []

    for page in range(totalPages):        

        # Consruct the next page with the list of ski resorts.
        if page == 1:
            url = url+"page/"+str(page+1)
        elif page > 1 and page < 10:
            url = url[:-1]+str(page+1)
        elif page >= 10:
            url = url[:-2]+str(page+1)
        # else: url is unchanged.
        
        # Get the current page contents
        content = get_html_content(url)

        # Get a list of all ski resorts on the current page
        html = BeautifulSoup(content, 'html.parser')
        resorts = html.find("div", {"id": "resortList"})

        # Cycle through each resort
        for index, resort in enumerate(resorts):
            if index >= totalResorts:  # Stop after the first 3 resorts
                break

            if resort != ' ':
                print(str(page + 1) + ": " + str(index))

                # Identify the country and locations of the resort.
                location = resort.find("div", {"class": "sub-breadcrumb"})
                
                # Initialize province_state
                province_state = "Unknown"  # Default value

                # Check if location is found
                if location:
                    continent = location.contents[0].text.strip() if len(location.contents) > 0 else "Unknown"
                    country = location.contents[1].text.strip() if len(location.contents) > 1 else "Unknown"
                    
                    # Assuming the province/state is in the next element or can be derived
                    if len(location.contents) > 2:
                        province_state = location.contents[2].text.strip()  # Adjust based on actual structure

                # Get slope statistics
                slopeTable = resort.find("table", {"class": "run-table"})
                if slopeTable:
                    for row in slopeTable.findAll("tr"):
                        print(row)  # Debugging output to see the row structure
                        if len(row.contents) >= 3:  # Ensure there are at least 3 contents
                            key = row.contents[0].text.strip()  # Get the description
                            distance_text = row.find("td", {"class": "distance"}).text.strip()  # Get the distance text
                            
                            print("distance_text:", distance_text)  # Debugging output
                            # Check if distance_text is not empty and contains "km"
                            if distance_text and "km" in distance_text:
                                value = float(distance_text.split("km")[0].strip())  # Get the distance value
                                slopeSatistics[key] = value
                                stat[key] = value
                            else:
                                print(f"Distance value is missing or not in expected format: {distance_text}")
                        else:
                            print("Unexpected structure in row:", row)

                # Extract lift numbers
                liftStatistics = {}
                print("Lift numbers:")
                liftTable = resort.find("table", {"class": "lift-table"})  # Adjust the class name based on actual HTML
                if liftTable:
                    for row in liftTable.findAll("tr"):
                        if len(row.contents) >= 2:  # Ensure there are at least 2 contents
                            lift_type = row.contents[0].text.strip()  # Get the lift type
                            lift_count = row.contents[1].text.strip()  # Get the lift count
                            
                            print(f"{lift_type}: {lift_count}")  # Debugging output
                            liftStatistics[lift_type] = int(lift_count) if lift_count.isdigit() else 0  # Store lift count in liftStatistics
                else:
                    print("Lift table not found or has unexpected structure.")

                # Get the URL for each resort
                resortUrl = resort.find("a", {"class": "pull-right btn btn-default btn-sm"})['href']
                resortName = resortUrl.split('/')[-2]
                print("Looking at Resort: ", resortUrl)
                
                # Get the contents of the ski resort page.
                stat, liftStatistics = get_basic_resort_statistics(resortUrl)

                # Get the report scores
                scores = get_report_scores(resortUrl)

                altitude = stat["Altitude"]
                logo_url = stat["Logo URL"]
                resort_website = stat["Website"]
                trail_map_link = stat["Trail Map"]

                newResort = {
                    "Resort Name": resortName,
                    "Continent": continent,
                    "Country": country,
                    "State/Province": province_state,  
                    "URL": resortUrl,
                    "Altitude": altitude,
                    "Logo URL": logo_url,  
                    "Website": resort_website, 
                    "Trail Map": trail_map_link,  
                    **stat,  # Include slope statistics
                    **scores,  # Include report scores
                }

                # Add lift statistics to the newResort dictionary
                for lift_type, count in liftStatistics.items():
                    newResort[lift_type] = count  # Add each lift type and its count

                print("Resort data: ", newResort)

                # Add the resort data to the list
                resort_data_list.append(newResort)

    # After the loop, create a DataFrame and save to Excel
    df = pd.DataFrame(resort_data_list)
    df.to_excel('skiResort.xlsx', sheet_name='sheet1', index=False)
    
    # Extract the dollar symbol from the price







from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup, Tag
import pandas as pd
#import numpy as np
import re
import time
from colorama import Fore, Style, init
import signal
import sys

init(autoreset=True)  # Initialize Colorama

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

def get_interactive_trail_map(id):
    """
    Get the interactive trail map link for the resort.
    """
    # Construct the URL for the trail map
    trail_map_url = f"https://www.skiresort.info/ski-resort/{id}/trail-map/"
    
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
    resortContent = get_html_content(resortUrl)
    print(f"{Fore.CYAN}🌐 Scraped resort content from: {resortUrl}")  # Log the scraping action

    resortHtml = BeautifulSoup(resortContent, 'html.parser')

    # Initialize variables
    logo_url = None
    resort_website = None
    trail_map_link = None
    description = None
    altitude = 0
    slopeSatistics = {}
    liftStatistics = {}

    # Extract the resort name
    resort_name_element = resortHtml.find("h1").find("span", {"class": "fn"})
    resort_name = resort_name_element.get_text(strip=True) if resort_name_element else "Unknown"

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

    # Get the resort id for the trail map link
    id = resortUrl.split('/')[-2]

    # Get the interactive trail map link
    trail_map_link = get_interactive_trail_map(id)

    # Extract the description
    description_element = resortHtml.find("p", {"class": "p_before_list"})
    if description_element:
        js_more_text = description_element.find("span", {"class": "js-more-text"})
        if js_more_text:
            description = js_more_text.get_text(strip=True)

    # Get altitude info
    if (resortHtml.find("div", {"id": "selAlti"}) != None):
        altitudeDescipriton = resortHtml.find("div", {"id": "selAlti"}).contents
        if len(altitudeDescipriton) > 2:
            altitude = float(altitudeDescipriton[2].split(" - ")[1].split("m")[0])
        else:        
            altitude = float(altitudeDescipriton[0].split(" - ")[1].split("m")[0])

    print(f"{Fore.GREEN}🏔️ Resort Name: {resort_name}")  # Log resort name
    print(f"{Fore.YELLOW}🖼️ Logo URL: {logo_url}")  # Log logo URL
    print(f"{Fore.YELLOW}🔗 Website: {resort_website}")  # Log website
    print(f"{Fore.YELLOW}🗺️ Trail Map Link: {trail_map_link}")  # Log trail map link
    print(f"{Fore.YELLOW}📝 Description: {description}")  # Log description
    print(f"{Fore.YELLOW}📏 Altitude: {altitude} meters")  # Log altitude

    # Get slope statistics
    slopeTable = resortHtml.find("table", {"class": "run-table"})
    print(f"{Fore.BLUE}📊 Slope Statistics:")
    if slopeTable is not None:
        for row in slopeTable.findAll("tr"):
            if len(row.contents) >= 3:
                key = row.contents[0].text.strip()
                distance_text = row.find("td", {"class": "distance"}).text.strip()
                if distance_text and "km" in distance_text:
                    value = float(distance_text.split("km")[0].strip())
                    slopeSatistics[key] = value
                    print(f"{Fore.GREEN}  {key}: {value} km")  # Log slope statistics
    else:
        print(f"{Fore.RED}❌ No slope statistics found.")

    # Extract lift numbers
    liftTable = resortHtml.find("table", {"class": "lift-table"})
    print(f"{Fore.BLUE}🚡 Lift Statistics:")
    if liftTable:
        for row in liftTable.findAll("tr"):
            if len(row.contents) >= 2:
                lift_type = row.contents[0].text.strip()
                lift_count = row.contents[1].text.strip()
                liftStatistics[lift_type] = int(lift_count) if lift_count.isdigit() else 0
                print(f"{Fore.GREEN}  {lift_type}: {liftStatistics[lift_type]}")  # Log lift statistics
    else:
        print(f"{Fore.RED}❌ Lift table not found or has unexpected structure.")

    # Extract the ticket prices
    currency = None
    adultPrices = resortHtml.find("td", {"id": "selTicketA"}).contents[0] if resortHtml.find("td", {"id": "selTicketA"}) else 0
    youthPrices = resortHtml.find("td", {"id": "selTicketY"}).contents[0] if resortHtml.find("td", {"id": "selTicketY"}) else 0
    childPrices = resortHtml.find("td", {"id": "selTicketC"}).contents[0] if resortHtml.find("td", {"id": "selTicketC"}) else 0

    [currency, adultPrices] = currencyExtraction(adultPrices) if adultPrices else ['-', 0]
    [currency, youthPrices] = currencyExtraction(youthPrices) if youthPrices else ['-', 0]
    [currency, childPrices] = currencyExtraction(childPrices) if childPrices else ['-', 0]

    print(f"{Fore.BLUE}💰 Ticket Prices:")
    print(f"{Fore.GREEN}  Adult: {adultPrices} {currency}")  # Log adult prices
    print(f"{Fore.GREEN}  Youth: {youthPrices} {currency}")  # Log youth prices
    print(f"{Fore.GREEN}  Child: {childPrices} {currency}")  # Log child prices

    # Compile all statistics into a dictionary
    stat = {
        "Altitude": altitude,
        "Description": description,
        "Trail Map": trail_map_link,
        "ID": id,
        "Resort Name": resort_name,
        "Adult": adultPrices,
        "Youth": youthPrices,
        "Child": childPrices,
        "Currency": currency,
        "Logo URL": logo_url,
        "Website": resort_website,
        **slopeSatistics,
        **liftStatistics
    }

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


# Initialize a list to hold all resort data
resort_data_list = []

def signal_handler(sig, frame):
    print(f"{Fore.RED}🚨 Script interrupted! Saving data to 'skiResort.xlsx'...")  # Log interruption
    df = pd.DataFrame(resort_data_list)
    df.to_excel('skiResort.xlsx', sheet_name='sheet1', index=False)
    print(f"{Fore.GREEN}💾 Data saved  to 'skiResort.xlsx'. Total resorts scraped: {resort_count}. Exiting...")  # Log data saving completion
    sys.exit(0)

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    print(f"{Fore.CYAN}🚀 Starting the ski resort data scraping process...")

    url = 'https://www.skiresort.info/ski-resorts/europe/'
    totalPages = 3  # europe
    totalResorts = 99

    resort_count = 0  # Initialize a counter for processed resorts

    for page in range(totalPages):        
        print(f"{Fore.CYAN}📄 Scraping page {page + 1} of {totalPages}...")

        # Construct the next page URL
        if page == 0:
            page_url = url
        elif page == 1:
            page_url = url + "page/" + str(page + 1)
        else:
            page_url = url + "page/" + str(page + 1)

        content = get_html_content(page_url)
        html = BeautifulSoup(content, 'html.parser')
        resorts = html.find("div", {"id": "resortList"}).find_all("div", class_="resort-list-item")

        for resort in resorts:
            if resort_count >= totalResorts:
                break

            resort_link = resort.find("a", {"class": "pull-right btn btn-default btn-sm"})
            if resort_link and 'href' in resort_link.attrs:
                resort_count += 1
                resortUrl = resort_link['href']
                print(f"{Fore.CYAN}🔍 Processing resort {resort_count} on page {page + 1}...")
                print("Looking at Resort: ", resortUrl)
                
                stat = get_basic_resort_statistics(resortUrl)
                resort_data_list.append(stat)

        if resort_count >= totalResorts:
            break

    print(f"{Fore.CYAN}✅ Data scraping completed. Total resorts scraped: {resort_count}. Saving to Excel...")
    df = pd.DataFrame(resort_data_list)
    df.to_excel('skiResort.xlsx', sheet_name='sheet1', index=False)
    print(f"{Fore.CYAN}💾 Data saved to 'skiResort.xlsx'.")
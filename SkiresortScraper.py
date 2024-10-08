from requests import Session
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import pandas as pd
import time
from colorama import Fore, init
import signal
import sys

# Initialize colorama for colored terminal output
init(autoreset=True)

def is_good_response(resp):
    """
    Check if the HTTP response is valid and contains HTML content.

    Args:
        resp: The HTTP response object.

    Returns:
        bool: True if the response is valid HTML, False otherwise.
    """
    content_type = resp.headers.get('Content-Type', '').lower()
    return resp.status_code == 200 and 'html' in content_type

def get_html_content(url: str) -> bytes:
    """
    Fetch the HTML content from a given URL.

    Args:
        url (str): The URL to scrape.

    Returns:
        bytes: The HTML content of the page, or None if the response is not valid.
    """
    time.sleep(1)  # Respectful scraping: wait before making a request
    with Session() as session:
        try:
            resp = session.get(url, stream=True)
            return resp.content if is_good_response(resp) else None
        except RequestException as e:
            print(f'Error during requests to {url}: {e}')

def currency_extraction(price_string):
    """
    Extract the currency symbol and price from a price string.

    Args:
        price_string (str): The price string containing currency and amount.

    Returns:
        list: A list containing the currency description and the price amount.
    """
    currency_dict = {
        '£': 'UK Pound', '¥': 'Japanese Yen', '€': 'European Euro', 'AED': 'United Arab Emirates',
        'AMD': 'Armenian Dram', 'ARS': 'Argentine Peso', 'AU$': 'Australian Dollar',
        'AZN': 'Azerbaijani Manat', 'BAM': 'Bosnia Convertible Mark', 'BGN': 'Bulgarian Lev',
        'C$': 'Canadian Dollar', 'CLP': 'Chilean Peso', 'CZK': 'Czech Koruna',
        'DKK': 'Danish Krone', 'GEL': 'Georgian Lari', 'HRK': 'Croatian Kuna',
        'HUF': 'Hungarian Forint', 'ILS': 'Israeli New Shekel', 'IRR': 'Iranian Rial',
        'ISK': 'Icelandic Krona', 'KGS': 'Kyrgyzstani Som', 'KRW': 'South Korean Won',
        'KZT': 'Kazakhstani Tenge', 'LBP': 'Lebanese Pound', 'MKD': 'Macedonian Denar',
        'MNT': 'Mongolian Togrog', 'NOK': 'Norwegian Krone', 'NZ$': 'New Zealand Dollar',
        'PLN': 'Polish Zloty', 'RON': 'Romanian Leu', 'Rs': 'Indian Rupee', 'RSD': 'Serbian Dinar',
        'RUB': 'Russian Ruble', 'SFr.': 'Swiss Franc', 'Skr': 'Swedish Krona', 'TRY': 'Turkish Lira',
        'UAH': 'Ukrainian Hryvnia', 'US$': 'US Dollar', 'ZAR': 'South African Rand', 'Ұ': 'Chinese Yuan'
    }

    currency, price = price_string.split()
    price = price.split(',')[0] if ',' in price else price  # Remove any commas from the price
    return [currency_dict.get(currency, 'unknown'), price]

def get_interactive_trail_map(id):
    """
    Retrieve the interactive trail map link for a specific ski resort.

    Args:
        id (str): The unique identifier for the ski resort.

    Returns:
        str: The URL of the interactive trail map, or None if not found.
    """
    trail_map_url = f"https://www.skiresort.info/ski-resort/{id}/trail-map/"
    trail_map_content = get_html_content(trail_map_url)
    trail_map_html = BeautifulSoup(trail_map_content, 'html.parser')
    first_link = trail_map_html.find("div", {"class": "panel panel-default"}).find("ul", {"class": "list-group"}).find("a", {"class": "more-infos"})
    return first_link['href'] if first_link and 'href' in first_link.attrs else None

def get_basic_resort_statistics(resort_url):
    """
    Scrape and print basic statistics for a ski resort.

    Args:
        resort_url (str): The URL of the ski resort page.

    Returns:
        dict: A dictionary containing various statistics about the resort.
    """
    resort_content = get_html_content(resort_url)
    print(f"{Fore.CYAN}🌐 Scraped resort content from: {resort_url}")

    resort_html = BeautifulSoup(resort_content, 'html.parser')
    resort_name = resort_html.find("h1").find("span", {"class": "fn"}).get_text(strip=True) if resort_html.find("h1") else "Unknown"
    logo_url = resort_html.find("div", {"class": "resort-logo"}).find("img")['src'] if resort_html.find("div", {"class": "resort-logo"}) else None
    logo_url = f"https://www.skiresort.info{logo_url}" if logo_url and logo_url.startswith('/') else logo_url
    resort_website = resort_html.find("div", {"class": "resort-logo"}).find("a")['href'] if resort_html.find("div", {"class": "resort-logo"}) else None
    id = resort_url.split('/')[-2]  # Extract the resort ID from the URL
    trail_map_link = get_interactive_trail_map(id)
    description = resort_html.find("p", {"class": "p_before_list"}).find("span", {"class": "js-more-text"}).get_text(strip=True) if resort_html.find("p", {"class": "p_before_list"}) else None
    altitude = float(resort_html.find("div", {"id": "selAlti"}).contents[2].split(" - ")[1].split("m")[0]) if resort_html.find("div", {"id": "selAlti"}) and len(resort_html.find("div", {"id": "selAlti"}).contents) > 2 else 0

    # Print resort details
    print(f"{Fore.GREEN}🏔️ Resort Name: {resort_name}")
    print(f"{Fore.YELLOW}🖼️ Logo URL: {logo_url}")
    print(f"{Fore.YELLOW}🔗 Website: {resort_website}")
    print(f"{Fore.YELLOW}🗺️ Trail Map Link: {trail_map_link}")
    print(f"{Fore.YELLOW}📝 Description: {description}")
    print(f"{Fore.YELLOW}📏 Altitude: {altitude} meters")

    # Scrape slope statistics
    slope_statistics = {}
    slope_table = resort_html.find("table", {"class": "run-table"})
    if slope_table:
        for row in slope_table.findAll("tr"):
            if len(row.contents) >= 3:
                key = row.contents[0].text.strip()
                distance_text = row.find("td", {"class": "distance"}).text.strip()
                if distance_text and "km" in distance_text:
                    value = float(distance_text.split("km")[0].strip())
                    slope_statistics[key] = value
                    print(f"{Fore.GREEN}  {key}: {value} km")
    else:
        print(f"{Fore.RED}❌ No slope statistics found.")

    # Scrape lift statistics
    lift_statistics = {}
    lift_table = resort_html.find("table", {"class": "lift-table"})
    if lift_table:
        for row in lift_table.findAll("tr"):
            if len(row.contents) >= 2:
                lift_type = row.contents[0].text.strip()
                lift_count = row.contents[1].text.strip()
                lift_statistics[lift_type] = int(lift_count) if lift_count.isdigit() else 0
                print(f"{Fore.GREEN}  {lift_type}: {lift_statistics[lift_type]}")
    else:
        print(f"{Fore.RED}❌ Lift table not found or has unexpected structure.")

    # Scrape ticket prices
    adult_prices = resort_html.find("td", {"id": "selTicketA"}).contents[0] if resort_html.find("td", {"id": "selTicketA"}) else 0
    youth_prices = resort_html.find("td", {"id": "selTicketY"}).contents[0] if resort_html.find("td", {"id": "selTicketY"}) else 0
    child_prices = resort_html.find("td", {"id": "selTicketC"}).contents[0] if resort_html.find("td", {"id": "selTicketC"}) else 0

    # Extract currency and prices
    currency, adult_prices = currency_extraction(adult_prices) if adult_prices else ['-', 0]
    currency, youth_prices = currency_extraction(youth_prices) if youth_prices else ['-', 0]
    currency, child_prices = currency_extraction(child_prices) if child_prices else ['-', 0]

    # Print ticket prices
    print(f"{Fore.BLUE}💰 Ticket Prices:")
    print(f"{Fore.GREEN}  Adult: {adult_prices} {currency}")
    print(f"{Fore.GREEN}  Youth: {youth_prices} {currency}")
    print(f"{Fore.GREEN}  Child: {child_prices} {currency}")

    # Compile all statistics into a dictionary
    stat = {
        "Altitude": altitude,
        "Description": description,
        "Trail Map": trail_map_link,
        "ID": id,
        "Resort Name": resort_name,
        "Adult": adult_prices,
        "Youth": youth_prices,
        "Child": child_prices,
        "Currency": currency,
        "Logo URL": logo_url,
        "Website": resort_website,
        **slope_statistics,
        **lift_statistics
    }

    return stat

# Initialize a list to hold all resort data
resort_data_list = []

def signal_handler(sig, frame):
    """
    Handle script interruption and save data to an Excel file.

    Args:
        sig: The signal number.
        frame: The current stack frame.
    """
    print(f"{Fore.RED}🚨 Script interrupted! Saving data to 'skiResort.xlsx'...")
    df = pd.DataFrame(resort_data_list)
    df.to_excel('skiResort.xlsx', sheet_name='sheet1', index=False)
    print(f"{Fore.GREEN}💾 Data saved to 'skiResort.xlsx'. Total resorts scraped: {len(resort_data_list)}. Exiting...")
    sys.exit(0)

# Register the signal handler for graceful exit
signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    print(f"{Fore.CYAN}🚀 Starting the ski resort data scraping process...")

    # Base URL for scraping ski resorts
    url = 'https://www.skiresort.info/ski-resorts/'
    # Base URL for scraping ski resorts in Europe
    # url = 'https://www.skiresort.info/ski-resorts/europe'

    total_pages = 21  # Total number of pages to scrape
    total_resorts = 21 * 50  # Total number of resorts to scrape (50 resorts per page)

    resort_count = 0  # Initialize a counter for processed resorts

    # Loop through each page to scrape resort data
    for page in range(total_pages):        
        print(f"{Fore.CYAN}📄 Scraping page {page + 1} of {total_pages}...")
        page_url = f"{url}page/{page + 1}" if page > 0 else url

        content = get_html_content(page_url)
        html = BeautifulSoup(content, 'html.parser')
        resorts = html.find("div", {"id": "resortList"}).find_all("div", class_="resort-list-item")

        # Loop through each resort on the page
        for resort in resorts:
            if resort_count >= total_resorts:
                break

            resort_link = resort.find("a", {"class": "pull-right btn btn-default btn-sm"})
            if resort_link and 'href' in resort_link.attrs:
                resort_count += 1
                resort_url = resort_link['href']
                print(f"{Fore.CYAN}🔍 Processing resort {resort_count} on page {page + 1}...")
                print("Looking at Resort: ", resort_url)
                
                # Get statistics for the current resort
                stat = get_basic_resort_statistics(resort_url)
                resort_data_list.append(stat)

        if resort_count >= total_resorts:
            break

    # Save all scraped data to an Excel file
    print(f"{Fore.CYAN}✅ Data scraping completed. Total resorts scraped: {resort_count}. Saving to Excel...")
    df = pd.DataFrame(resort_data_list)
    df.to_excel('skiResort.xlsx', sheet_name='sheet1', index=False)
    print(f"{Fore.CYAN}💾 Data saved to 'skiResort.xlsx'.")
#!/usr/bin/env python
# coding: utf-8

import os
from pathlib import Path, PurePath
import requests
#import pandas as pd
from bs4 import BeautifulSoup

SALES_URL = "https://www.nyc.gov/site/finance/property/property-annualized-sales-update.page" 

def get_sales_links(url, skip_table):
    """
    Get links to excel spreadsheets by year (from 2003 to 2023) and 
    borough from NYC Department of Finance website.
    """
    try:
        website_text = requests.get(url).text
        soup = BeautifulSoup(website_text, "html5lib")
        tables = soup.find_all('table')
        
        links = [each_link['href']
                for each_table in tables[skip_table:]
                for each_link in each_table.select("a[href*='.xls']")]

        list_of_urls = ["https://www1.nyc.gov" + each for each in links]

    except requests.RequestException as exception:
        return exception

    return list_of_urls

def check_for_directory(dirname):
    """
    Check the data directory for the existance 
    of a specific directory and creats
    if it doesn't exist.
    """
    parent_dir = Path(os.getenv("PARENT_DIR"))
    data_dir = parent_dir.joinpath('data')
    target_dir = data_dir.joinpath(dirname)
    if not Path.is_dir(target_dir):
        Path.mkdir(target_dir)
    
    return target_dir


def extract(url_links):
    """
    Downloads Excel spreadsheets from table on NYC Dept. 
    of Finance website and stores them in data directory.
    Checks to see if raw directory is created in data directory
    and creates one if doesn't exist.
    """
    raw_path = check_for_directory("raw")
    #ADD LOGGING CODE HERE
    for each_link in url_links:
        response = requests.get(each_link)
        filename = PurePath(each_link).name
        filepath = raw_path.joinpath(filename)
        with open(filepath, mode='wb') as f:
            f.write(response.content)


def main():
    url_links = get_sales_links(SALES_URL, 1)
    extract(url_links)

if __name__ == "__main__":
    main()

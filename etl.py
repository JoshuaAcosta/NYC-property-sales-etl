#!/usr/bin/env python
# coding: utf-8

import os
from pathlib import Path, PurePath
import requests
import pandas as pd
from bs4 import BeautifulSoup

def get_sales_links(url, skip_table=1):
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


def extract(url):
    """
    Downloads Excel spreadsheets from table on NYC Dept. 
    of Finance website and stores them in data directory.
    Checks to see if raw directory is created in data directory
    and creates one if doesn't exist.
    """
    raw_path = check_for_directory("raw")
    url_links = get_sales_links(url)
    
    for each_link in url_links:
        response = requests.get(each_link)
        filename = PurePath(each_link).name
        filepath = raw_path.joinpath(filename)
        with open(filepath, mode='wb') as f:
            f.write(response.content)

    return raw_path

def locate_header_row(file_path):
    
    df = pd.read_excel(file_path, header=None)
       
    # Check each row to find where the header starts
    for i, row in df.iterrows():
        if "BOROUGH" in row.iloc[0].strip():
            # Set this row as the header and drop rows above it
            #df.columns = df.iloc[i]
            #df = df[i + 1:].reset_index(drop=True)
            return i  # Return cleaned DataFrame and 1-based header row index
    
    return None  # Return None if no matching row is found

def read_csv_data(list_of_filenames):
    """ 
    Creates a list of dataframes, one df per spreadsheet, and then concats them into
    one combined dataframe. For each spreadsheet, columns desired are specified.
    Tax related columns and those with mostly null values are not added.
    Numeber of rows to skip for each df is specific due to change made by NY DOF 
    after 2010.
    """
    use_col_names = ["BOROUGH", "NEIGHBORHOOD","BUILDING CLASS CATEGORY", 
                     "TAX CLASS AS OF FINAL ROLL", "BLOCK", "LOT", "EASEMENT",
                     "BUILDING CLASS AS OF FINAL ROLL", "ADDRESS", "APARTMENT NUMBER", 
                     "ZIP CODE","RESIDENTIAL UNITS", "COMMERCIAL UNITS", "TOTAL UNITS",
                     "LAND SQUARE FEET", "GROSS SQUARE FEET", "YEAR BUILT",
                     "TAX CLASS AT TIME OF SALE",
                     "BUILDING CLASS AT TIME OF SALE",
                     "SALE PRICE", "SALE DATE"]
    
    list_of_dfs = []

    for each_link in  list_of_filenames:
        stage_path = check_for_directory("stage")
        filepath = stage_path.joinpath(each_link)
        list_of_dfs.append(pd.read_csv(filepath, header=0, dtype=str, names=use_col_names))

    dataframe = pd.concat(list_of_dfs, ignore_index=True, sort=False)

    return dataframe


def excel_to_csv(excel_file_list):
    # Directory paths
    stage_path = check_for_directory("stage")
    raw_path = check_for_directory("raw")
    
    # Process each file
    for each_link in excel_file_list:
        filepath = raw_path.joinpath(each_link)
        
        # Check the file extension and choose the correct engine
        if filepath.suffix == '.xls':
            engine = 'xlrd'
        elif filepath.suffix == '.xlsx':
            engine = 'openpyxl'
        else:
            print(f"Skipping unsupported file format: {filepath}")
            continue
        
        # Read the Excel file
        header_row = locate_header_row(filepath)
        print(f'filename: {each_link}, engine: {engine} and header row {header_row}')
        df = pd.read_excel(filepath, engine=engine, header=header_row)
        
        # Save the DataFrame as a CSV file
        csv_filename = stage_path.joinpath(filepath.stem + '.csv')

        df.to_csv(csv_filename, index=False)
    
    return stage_path

def transform_data(dir):

    #convert various Excel type files into csv
    staged_csv = excel_to_csv(dir)

    df = read_csv_data(os.listdir(staged_csv))
    df.drop_duplicates()
    df.dropna(how='all', inplace=True)

    #Updates columns names by stripping white spaces, makes all characters
    #lower case and replacing and spaces with an underscore.
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

    #Drop Easement column, completely empty
    df.drop(['easement'], axis=1, inplace=True)

    #Updating a neighborhood name that had incorrect values
    neighbohood_val = {'3004':'GRAVESEND',
                       '3019':'PROSPECT HEIGHTS',
                       '1026':'MIDTOWN EAST',
                       '1021':'SOHO'}
    df["neighborhood"].replace(neighbohood_val, inplace=True)

    #update year built of property address for accuracy
    df.loc[df.address == "762 MARCY AVENUE, 1B", 'year_built'] = 2017.0
    df.loc[df.address == "762 MARCY AVENUE, 4", 'year_built'] = 2017.0
    df.loc[df.address == "9 BARTLETT AVENUE, 0", 'year_built'] = 2019.0


    #Update zip code on property for accuracy 
    df.loc[df.address == "762 MARCY AVENUE, 1B", 'zip_code'] = 11216.0
    df.loc[df.address == "762 MARCY AVENUE, 4", 'zip_code'] = 11216.0

    #Split apartment number contained inside the address column
    #and update the apartment_number column.

    #Slice original dataframe to a another dataframe if the address
    #value for a row contains a comma. Splits address value into two
    #values if initial cell contained the column: one containing the
    #roperty address and another containing apartment number.
    #Apartment value then added to apartment_number column for row.
    
    df2 = df[df['address'].str.contains(",",na=False)]
    for index_label, row_series in df2.iterrows():
        new_address, apt_num = row_series['address'].split(',', 1)
        df2.at[index_label, 'address'] = new_address
        df2.at[index_label, 'apartment_number'] = apt_num
    df.update(df2)

    #removes all commas from cells in the apartment_number column
    df["apartment_number"] = df["apartment_number"].str.replace(',', '')

    prod_path = check_for_directory("prod")
    cleaned_file = 'cleaned_csv_sales.csv'
    cleaned_filepath = prod_path.joinpath(cleaned_file)
    df.to_csv(cleaned_filepath, index=False)

    return df.shape


def main():

    SALES_URL = "https://www.nyc.gov/site/finance/property/property-annualized-sales-update.page" 

    raw_data = extract(SALES_URL)

    clean_data = transform_data(os.listdir(raw_data))

    print(clean_data)


if __name__ == "__main__":
    import time
    start_time = time.time()
    main()
    end_time = time.time()  # Record the end time

    elapsed_time = end_time - start_time  # Calculate the elapsed time in seconds
    minutes, seconds = divmod(elapsed_time, 60)  # Convert elapsed time to minutes and seconds

    print(f"Execution time: {elapsed_time:.4f} seconds")
    print(f"Execution time: {int(minutes)} minutes and {seconds:.4f} seconds")

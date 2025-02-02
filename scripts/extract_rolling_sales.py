import logging
logger = logging.getLogger(__name__)
import os
from pathlib import Path, PurePath
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler() 
    ]
)

def extract_rolling_sales_links(url:str) -> list[str]:
    """
    Extracts links to excel spreadsheets containing propery sales 
    in 2024 for each borough. 
    
    Note: The Department of Finance rolling 
    sales files lists tax class 1, 2, and 4 properties that have sold in 
    the last 12-month period. This script extracts sales for the date range
    of January-December 2024. Script will need to be updated if you want
    to it every month to extract new sales from previous month.
    """
    try:
        website_text = requests.get(url).text
        soup = BeautifulSoup(website_text, "html5lib")
        table = soup.find('table')
        
        links = ["https://www.nyc.gov" + each_link['href'] for 
                 each_link in table.select("a[href*='.xlsx']")]

    except requests.RequestException as exception:
        logger.error(f"Failed to fetch URL {url}: {str(exception)}")
        raise exception

    return links

def check_for_directory(dirname:str) -> Path:
    """
    Check the data directory for the existance 
    of a specific directory and creates
    if it doesn't exist.
    """
    parent_dir = Path(os.getenv("PARENT_DIR"))
    data_dir = parent_dir.joinpath('data')
    target_dir = data_dir.joinpath(dirname)
    if not Path.is_dir(target_dir):
        Path.mkdir(target_dir)
    
    return target_dir


def download_files(url_links:list[str], raw_path:Path) -> None:
    """
    Downloads Excel spreadsheets from table on NYC Dept. 
    of Finance website and stores them in data directory.
    Checks to see if raw directory is created in data directory
    and creates one if doesn't exist.
    """
    
    for each_link in url_links:
        try:
            response = requests.get(each_link)

        except requests.RequestException as exception:
            logger.error(f"Failed to fetch URL {each_link}: {str(exception)}")
            raise exception

        if response.status_code == 200:
            filename = PurePath(each_link).name
            filepath = raw_path.joinpath(filename)
            with open(filepath, mode='wb') as f:
                f.write(response.content)


if __name__ == "__main__":

    rolling_sales_url = os.getenv("ROLLING_SALES_URL")
    excel_links = extract_rolling_sales_links(rolling_sales_url)
    raw_path = check_for_directory("raw/rolling_sales")
    download_files(excel_links, raw_path)
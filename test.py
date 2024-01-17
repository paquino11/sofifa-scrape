import requests
from bs4 import BeautifulSoup
import csv
import logging
import time
import os
import random
import yaml
from pathlib import Path
from typing import Optional, Dict, List
import csv



def load_config(filename: str) -> Dict:
    """
    Load configuration from a YAML file.

    Args:
        filename (str): The path to the YAML file.

    Returns:
        dict: The configuration dictionary.
    """
    try:
        with open(filename, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError as e:
        logging.error(f"Config file not found: {e}")
        raise

def choose_user_agent(user_agents: List[str]) -> str:
    """
    Randomly choose a user agent from a list.

    Args:
        user_agents (List[str]): A list of user agents.

    Returns:
        str: A randomly chosen user agent.
    """
    return random.choice(user_agents)

def get_html(url: str, session: requests.Session) -> Optional[str]:
    """
    Retrieve HTML content from a URL using a given requests session.

    Args:
        url (str): The URL to fetch.
        session (requests.Session): The requests session.

    Returns:
        Optional[str]: The HTML content if successful, None otherwise.
    """
    try:
        response = session.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Failed to retrieve the webpage: {e}")
        return None

def save_table_to_csv(table: BeautifulSoup, filename: str, include_headers: bool) -> None:
    """
    Save a BeautifulSoup table to a CSV file with custom data extraction for specific columns.
    """
    try:
        rows = table.find_all('tr')
        with open(filename, 'a' if not include_headers else 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if include_headers:
                headers = [header.get_text(strip=True) for header in rows[0].find_all(['th'])]
                writer.writerow(headers)
                rows = rows[1:]  # Skip the header row for data rows

            for row in rows:
                csv_row = []
                for index, cell in enumerate(row.find_all(['td', 'th'])):
                    if index == 1:  # Special handling for the second column
                        player_name = cell.find('a').get_text(strip=True) if cell.find('a') else ''
                        csv_row.append(player_name)
                    elif index == 5:  # Special handling for the sixth column
                        team_name = cell.find('a').get_text(strip=True) if cell.find('a') else ''
                        csv_row.append(team_name)
                    else:
                        cell_text = cell.get_text(strip=True).replace('\n', ' ').replace('\r', '').strip()
                        csv_row.append(cell_text)

                writer.writerow(csv_row)
        logging.info(f"Data appended to {filename}")
    except IOError as e:
        logging.error(f"Error saving table to {filename}: {e}")

def fetch_and_save_first_table(url: str, offset: int, session: requests.Session, filename: str, include_headers: bool) -> None:
    """
    Fetch the first table from the given URL and save it as a CSV file.
    """
    logging.info(f"Fetching data from URL: {offset}")
    html = get_html(url, session)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        first_table = soup.find('table')
        if first_table:
            save_table_to_csv(first_table, filename, include_headers)
        else:
            logging.info("No table found in the HTML.")
        time.sleep(3)

def remove_rows_with_non_integer_potential(input_file, output_file, potential_column_index):
    """
    Remove rows from the CSV where the 'Potential' column does not contain an integer, except for the header row.

    Args:
        input_file (str): The path to the input CSV file.
        output_file (str): The path to the output CSV file.
        potential_column_index (int): The index of the 'Potential' column in the CSV.
    """
    with open(input_file, 'r', newline='', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        # Write the header row
        header_row = next(reader)
        writer.writerow(header_row)

        for row in reader:
            # Check if the row has enough columns
            if len(row) > potential_column_index:
                try:
                    # Check if the 'Potential' value is an integer
                    int(row[potential_column_index])
                    # Write the row to the output file
                    writer.writerow(row)
                except ValueError:
                    # Skip rows where 'Potential' is not an integer
                    continue

def clean_csv(input_file, output_file):
    """
    Clean each row in the CSV by removing the first and last commas.

    Args:
        input_file (str): The path to the input CSV file.
        output_file (str): The path to the output CSV file.
    """
    with open(input_file, 'r', newline='', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        for row in reader:
            if row:
                # Remove the first element if it's empty
                if row[0] == '':
                    row = row[1:]
                # Remove the last element if it's empty
                if row[-1] == '':
                    row = row[:-1]

                writer.writerow(row)

def modify_column(input_file, output_file, height_column_index):
    """
    Modify the column in the CSV to only include the height in centimeters.

    Args:
        input_file (str): The path to the input CSV file.
        output_file (str): The path to the output CSV file.
        height_column_index (int): The index of the 'Height' column in the CSV.
    """
    with open(input_file, 'r', newline='', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        for row in reader:
            if len(row) > height_column_index:
                # Extract only the 'xxxcm' part for height
                height_data = row[height_column_index].split(' ')[0]  # Assumes format 'xxxcm / y'y"'
                height_data = height_data[:-2]
                row[height_column_index] = height_data

            writer.writerow(row)

def remove_files(*file_paths):
    """
    Remove the specified files.

    Args:
        file_paths: A list of file paths to be removed.
    """
    for file_path in file_paths:
        try:
            os.remove(file_path)
            print(f"File '{file_path}' successfully removed.")
        except FileNotFoundError:
            print(f"File '{file_path}' not found. Cannot be removed.")
        except Exception as e:
            print(f"Error occurred while removing file '{file_path}': {e}")

def data_cleaning(filename):
    input_csv_file = filename
    remove_headers = "remove_headers.csv"
    remove_commas = "remove_commas.csv"
    fix_height = "fix_height.csv"
    sofifa_players = "sofifa_players.csv"
    potential_col_index = 2  # Update this to the correct index of the 'Potential' column in your CSV
    remove_rows_with_non_integer_potential(input_csv_file, remove_headers, potential_col_index)
    clean_csv(remove_headers, remove_commas)
    modify_column(remove_commas, fix_height, 5)
    modify_column(fix_height, sofifa_players, 6)
    remove_files("remove_headers.csv", "remove_commas.csv", "fix_height.csv", "raw_players.csv")



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    config = load_config('config.yaml')
    session = requests.Session()
    session.headers.update({'User-Agent': choose_user_agent(config['user_agents'])})

    base_url = "https://sofifa.com/players?col=oa&sort=desc&showCol%5B0%5D=ae&showCol%5B1%5D=hi&showCol%5B2%5D=wi&showCol%5B3%5D=pf&showCol%5B4%5D=oa&showCol%5B5%5D=pt&showCol%5B6%5D=bo&showCol%5B7%5D=bp&showCol%5B8%5D=gu&showCol%5B9%5D=jt&showCol%5B10%5D=le&showCol%5B11%5D=vl&showCol%5B12%5D=wg&showCol%5B13%5D=rc&showCol%5B14%5D=ta&showCol%5B15%5D=cr&showCol%5B16%5D=fi&showCol%5B17%5D=he&showCol%5B18%5D=sh&showCol%5B19%5D=vo&showCol%5B20%5D=ts&showCol%5B21%5D=dr&showCol%5B22%5D=cu&showCol%5B23%5D=fr&showCol%5B24%5D=lo&showCol%5B25%5D=bl&showCol%5B26%5D=to&showCol%5B27%5D=ac&showCol%5B28%5D=sp&showCol%5B29%5D=ag&showCol%5B30%5D=re&showCol%5B31%5D=ba&showCol%5B32%5D=tp&showCol%5B33%5D=so&showCol%5B34%5D=ju&showCol%5B35%5D=st&showCol%5B36%5D=sr&showCol%5B37%5D=ln&showCol%5B38%5D=te&showCol%5B39%5D=ar&showCol%5B40%5D=in&showCol%5B41%5D=po&showCol%5B42%5D=vi&showCol%5B43%5D=pe&showCol%5B44%5D=cm&showCol%5B45%5D=td&showCol%5B46%5D=ma&showCol%5B47%5D=sa&showCol%5B48%5D=sl&showCol%5B49%5D=tg&showCol%5B50%5D=gd&showCol%5B51%5D=gh&showCol%5B52%5D=gc&showCol%5B53%5D=gp&showCol%5B54%5D=gr&showCol%5B55%5D=tt&showCol%5B56%5D=bs&showCol%5B57%5D=aw&showCol%5B58%5D=dw&showCol%5B59%5D=pac&showCol%5B60%5D=sho&showCol%5B61%5D=pas&showCol%5B62%5D=dri&showCol%5B63%5D=def&showCol%5B64%5D=phy&offset="
    offset_step = 60
    max_offset = 18600

    filename = "raw_players.csv"
    for offset in range(0, max_offset, offset_step):
        current_url = f"{base_url}{offset}"
        fetch_and_save_first_table(current_url, offset, session, filename, include_headers=(offset == 0))
        time.sleep(3)

    data_cleaning(filename)




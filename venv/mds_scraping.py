import requests
from bs4 import BeautifulSoup
import pandas as pd
import warnings
import json
from multiprocessing import Pool
import os
import time

# Ignore all warnings
warnings.filterwarnings("ignore")

def _combinations():
    combinations = []
    # get a list from 000.0 to 999.9
    for i in range(10):
        for j in range(10):
            for k in range(10):
                for decimal in range(10):
                    combination = f"{i:0>1}{j:0>1}{k:0>1}.{decimal:0>1}"
                    combinations.append(combination)   
    return combinations

def scrap_mds(df: pd.DataFrame) -> pd.DataFrame:
    # log start time
    start_time = time.perf_counter()

    # get CPU Processor Count
    processes_count = os.cpu_count()

    # get list of all combinations
    combinations = _combinations()

    # Multiprocess Scraping Data
    processes_pool = Pool(processes_count)
    async_results = [processes_pool.apply_async(_scrap, args=(combo, df)) for combo in combinations]
    results = [ar.get() for ar in async_results]
    result_df = pd.concat(results, ignore_index=True)

    # log finish time
    finish_time = time.perf_counter()
    print("Program finished in {} seconds - using multiprocessing".format(finish_time - start_time))

    return result_df

def _scrap(extension, df):

    url = "https://www.librarything.com/mds/" + extension
    
    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, 'html.parser')
    
        # Find the table with class "ddc"
        table = soup.find('table', {'class': 'ddc'})
    
        # Extract data from the table
        for row in table.find_all('tr'):
            # Extract data from each cell in the row
            cells = []
            for cell in row.find_all(['td', 'th']):
                # Extract data from the div elements within the cell
                ddcnum_div = cell.find('div', {'class': 'ddcnum'})
                word_div = cell.find('div', {'class': 'word'})
                
                ddcnum = ddcnum_div.text.strip() if ddcnum_div else ''
                word = word_div.text.strip() if word_div else ''
                
                cells.append({'ddcnum': ddcnum, 'word': word})
                
            df = df.append(cells).reset_index(drop=True)
            
        return df
    else:
        print(f"Failed to retrieve the webpage: {url}. Status code: {response.status_code}")
        return df

def data_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    # Keep only the first occurrence of each unique value in 'ddcnum'
    df = df[~df['ddcnum'].duplicated(keep='first')]

    # Drop rows where 'word' is blank or missing or bad records
    df = df.dropna(subset=['word'], how='all')
    df = df[df['word'] != '']
    df = df[~df['word'].str.startswith('--')]

    # Drop Periods From DDCNUM
    # used to build tree structure
    df['ddccum_stripped'] = df['ddcnum'].str.replace(r'\D', '', regex=True)

    return df

def build_tree(df, root_node_key):
    tree = {root_node_key: {'ddcnum': '', 'word': 'Root', 'children': {}}}
    
    for index, row in df.iterrows():
        current_node = tree[root_node_key]['children']
        ddcnum_parts = row['ddccum_stripped']
        
        for part in ddcnum_parts:
            if part not in current_node:
                current_node[part] = {'ddcnum': row['ddcnum'], 'word': row['word'], 'children': {}}
            current_node = current_node[part]['children']
    
    return tree

def data_backup(df, tree):
    # save data
    df.to_csv("../data/scrapdata.csv")
    df.to_pickle("../data/scrapData.pkl")
    
    # Specify the file path where you want to save the JSON
    file_path = "../data/data.json"
    
    # Save the dictionary to a JSON file
    with open(file_path, 'w') as json_file:
        json.dump(tree, json_file, indent=0)
    return

def main():
    # Run Scraping routine and save as a dataframe
    df = scrap_mds(pd.DataFrame())
    # Clean Data
    df_clean = data_cleaning(df)
    # build tree
    tree = build_tree(df_clean, 'root')
    # save data
    data_backup(df_clean, tree)

if __name__ == '__main__':
    main()


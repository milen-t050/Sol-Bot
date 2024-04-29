import pandas as pd
import datetime
import personal as p
import requests
import time
import json
import re
import pprint
import pytz

############################################################################################################

#PARAMETERS
MC_HIGH = 20000
MC_LOW = 0
MIN_LIQ = 2000
MIN_24HR_VOL = 2000
NUM_TOKENS_TO_SEARCH = 15000

MAX_SELL_PERCENTAGE = 70
MIN_TRADES_LAST_HOUR = 10
MIN_UNIQUE_WALLETS_2HR = 0
MIN_VIEW24H = 100

# THIS ONLY RUNS FOR NEW DATA IF THE BELOW IS TRUE 
new_data = True

############################################################################################################

def birdEye_bot():
    url = "https://public-api.birdeye.so/defi/tokenlist"
    headers = {"x-chain": "solana", "X-APi-KEY": p.birdEye_apiKey}

    tokens = []
    offset = 0
    limit = 50
    total_tokens = 0
    while total_tokens < NUM_TOKENS_TO_SEARCH:
        print("Scaned Tokens %d" % total_tokens)
        params = {"sort_by": "v24hUSD", "sort_type": "desc", "offset": offset, "limit": limit}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            response_data = response.json()
            new_tokens = response_data.get('data', {}).get('tokens', [])
            tokens.extend(new_tokens)
            total_tokens += len(new_tokens)
            offset += limit
        else:
            print("Failed to retrieve data:", response.status_code)
            break

    # Create a DataFrame from the tokens
    df = pd.DataFrame(tokens)

    # Initial DataFrame length before filtering
    initial_length = len(df)
    print("Initial number of entries before filtering: %d" % initial_length)

    # Apply filters for minimum liquidity and 24-hour volume
    df = df.dropna(subset=['liquidity', 'v24hUSD'])
    df = df[(df['liquidity'] > MIN_LIQ) & (df['v24hUSD'] > MIN_24HR_VOL)]

    # Apply filters for mc
    df = df[(df['mc'] >= MC_LOW) & (df['mc'] <= MC_HIGH)]

    # Drop specified columns
    drop_columns = ['logoURI']
    df = df.drop(columns=drop_columns)

    # Convert lastTradeUnix time to EST and create a new column
    # Note: We create the 'lastTradeTime_EST' column without altering the 'lastTradeUnixTime' column
    df['lastTradeTime_EST'] = pd.to_datetime(df['lastTradeUnixTime'], unit='s').dt.tz_localize('UTC').dt.tz_convert('America/New_York')

    # Set the new time column as the index, keeping it in the DF
    df.set_index('lastTradeTime_EST', inplace=True)

    # Filter out rows with trades happening more than 1 hour ago
    current_time = datetime.datetime.now(pytz.timezone('UTC'))
    one_hour_ago = current_time - datetime.timedelta(hours=1)
    df = df[df.index >= one_hour_ago]

    # Reset index as the index was previously set to 'lastTradeTime_EST'
    df.reset_index(inplace=True)

    # Reorder columns to ensure 'address' is the first column
    address_column = df['address']
    df.drop(labels=['address'], axis=1, inplace=True)
    df.insert(0, 'address', address_column)

    # Add the token link column in the specified format
    df['token_link'] = "https://birdeye.so/token/" + df['address'].astype(str)

    # Ensure the 'address' column is first after resetting the index
    reordered_columns = ['address'] + [col for col in df.columns if col != 'address' and col != 'token_link']
    df = df[reordered_columns + ['token_link']]  # This will add 'token_link' as the last column

     # Final DataFrame length after filtering
    final_length = len(df)
    print("Final number of entries after filtering: %d" % final_length)

    # Save the dataframe to a local CSV file
    df.to_csv("filtered_pricechange.csv", index=False)

    # Pretty print the modified DataFrame
    pd.set_option('display.max_columns', None)  # Show all columns

    return df

if new_data == True:
    # run bird eye bot in order to get the meme token data
    data = birdEye_bot()
else:
    # load the data from the csv
    data = pd.read_csv('filtered_pricechange.csv')

#in the df if the v24hUSD colum has a number in it, drop it from the data and make a new 
def new_launches(data):
    #create a new DF with rows where 'v24hChange' is NaN (empty)
    new_launches = data[data['v24hChangePercent'].isna()]

    # Generate a timestamp for the current date and time
    timestamp =datetime.datetime.now().strftime("%m-%d-%H")

    # Contruct the CSV file name with the timestamp
    csv_filename = 'new_launches.csv'

    # Save the new launches DF as  CSV file with the gernerated filenmae
    new_launches.to_csv(csv_filename, index=False)

    #print(new_launches)
    return new_launches

pp = pprint.PrettyPrinter(indent=4)
BASE_URL = "https://public-api.birdeye.so/defi/"

def pretty_print_json(data):
    """Utility function to print JSON data in a formatted manner."""
    pp.pprint(data)

def find_urls(text):
    """Extracts URLs from a given string using a simplified regex pattern."""
    regex_pattern = r'https?://[^\s]+'
    return re.findall(regex_pattern, text)

def token_overview(address):
    """Fetches and processes token overview data from an API for a given token address."""
    url = f"{BASE_URL}token_overview?address={address}"
    headers = {"x-chain": "solana", "X-API-KEY": p.birdEye_apiKey}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return parse_overview_data(response.json()['data'], address)
        else:
            print(f"Failed to retrieve token overview: {response.status_code}")
            return {}
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return {}

def parse_overview_data(data, address):
    """Parses the relevant token data from the API response."""
    result = {
        'url': f"https://dexscreener.com/solana/{address}",  # Link to token on Dexscreener
        'trade1h': data.get('buy1h', 0) + data.get('sell1h', 0),  # Total trading volume in the last hour
        'buy1h': data.get('buy1h', 0),  # Buy volume in the last hour
        'sell1h': data.get('sell1h', 0),  # Sell volume in the last hour
    }
    result.update(calculate_percentages(result))
    result.update(extract_price_changes(data))
    result.update({
        'uniqueWallet2hr': data.get('uniqueWallet2hr', 0),  # Number of unique wallets trading the token in the last 2 hours
        'v24USD': data.get('v24hUSD', 0),  # 24-hour trading volume in USD
        'watch': data.get('watch', 0),  # Watch count on Dexscreener
        'view24h': data.get('view24h', 0),  # Views in the last 24 hours
        'liquidity': data.get('liquidity', 0),  # Current liquidity of the token
        })
        # Safely extracting the description, considering 'extensions' might be None
    extensions = data.get('extensions', {})
    if extensions is not None:
        result.update({'links': extract_links(extensions.get('description', ''))})
    return result

def calculate_percentages(result):
    """Calculates buy and sell percentages and evaluates trade conditions."""
    total_trades = result['trade1h']
    if total_trades > 0:
        buy_percentage = (result['buy1h'] / total_trades) * 100
        sell_percentage = (result['sell1h'] / total_trades) * 100
    else:
        buy_percentage = sell_percentage = 0
    return {
        'buyPercentage': buy_percentage,
        'sellPercentage': sell_percentage,
    }

def extract_price_changes(data):
    """Extracts and returns price changes data from token details."""
    return {'priceChangeXhrs': {k: v for k, v in data.items() if 'priceChange' in k}}

def extract_links(description):
    """Extracts and categorizes links from the token description based on their domain."""
    urls = find_urls(description)
    links = []
    for url in urls:
        if 't.me' in url:
            links.append({'telegram': url})  # Telegram links
        elif 'twitter.com' in url:
            links.append({'twitter': url})  # Twitter links
        else:
            links.append({'website': url})  # Assume any other URL is the token's website
    return links


new_launches = new_launches(data)

# Create an empty DF for the results
results_df = pd.DataFrame()

# Iterate over each row in the DF
for index, row in new_launches.iterrows():
    #Use the 'token_overview' func from 'nice_funs' for each address
    address = row['address']
    print(f"Fetching token data for: {address}")
    token_data = token_overview(address) # update this function so we can pass in max sell percentage and min trades last hour, mIn unique wallets2hr, min view 24hr, min liquidy

    # If token_data is not None, append the data to the reuslts DF
    if token_data:
            if (token_data.get('sellPercentage', 101) < MAX_SELL_PERCENTAGE and 
            token_data.get('trade1h', 0) >= MIN_TRADES_LAST_HOUR and 
            token_data.get('uniqueWallet2hr', 0) >= MIN_UNIQUE_WALLETS_2HR and 
            token_data.get('view24h', 0) >= MIN_VIEW24H and 
            not token_data.get('rug_pull', False)):
                if isinstance(token_data, dict):  # Ensuring token_data is in DataFrame format
                    token_data = pd.DataFrame([token_data])
                token_data['address'] = address  # Add address to the data
                temp_data = token_data.copy()

                # Before attempting to pop 'priceChangeXhrs', check if the column exists in the DataFrame
                if 'priceChangeXhrs' in temp_data.columns:
                    temp_data.pop('priceChangeXhrs')

                # Using pd.concat instead of .append()
                results_df = pd.concat([results_df, temp_data], ignore_index=True)
    
# Save the results to CSV
results_df.to_csv('hyper-sorted-sol.csv', index=False)
import requests
import json
import personal as p
import pandas as pd
import datetime
import pytz
import time

def birdEye_bot():
    url = "https://public-api.birdeye.so/defi/tokenlist"
    headers = {"x-chain": "solana", "X-APi-KEY": p.birdEye_apiKey}

    tokens = []
    offset = 0
    limit = 50
    total_tokens = 0
    token_limit = 15000
    mc_high = 20000
    mc_low = 0
    min_liq = 2000
    min_24hr_vol = 2000
    n = 1
    delayT = 1
    # delay with 1.5 worked, 1.4 worked, 1.375 worked, 1.37 worked, 1 didn't work, 1.25 didn't work, 1.3 didnt work, 1.35 didn't work, 1.355 didn't work, 1.36 didnt work, 1.365 didnt work
    while total_tokens < token_limit:
        print("Scaned Tokens %d" % total_tokens)
        n += 1
        params = {"sort_by": "v24hUSD", "sort_type": "desc", "offset": offset, "limit": limit}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            response_data = response.json()
            new_tokens = response_data.get('data', {}).get('tokens', [])
            tokens.extend(new_tokens)
            total_tokens += len(new_tokens)
            offset += limit
            #time.sleep(delayT)
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
    df = df[(df['liquidity'] >= min_liq) & (df['v24hUSD'] >= min_24hr_vol)]

    # Apply filters for mc
    df = df[(df['mc'] >= mc_low) & (df['mc'] <= mc_high)]

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
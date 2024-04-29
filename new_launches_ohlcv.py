#checking OHLCV data for new launches

import pandas as pd
import requests
import time
import personal as p
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import pandas_ta as ta
from time import sleep
import os.path

# GETTING NEW TOKENS FIRST
#import get_new_launches2

timeframe = '3m' # 1m, 3,. 5m, 15m, 1h, 4h, 1d

#function to caluclate timestamps for now and 10 days from now
def get_time_range():
    now = datetime.now()
    ten_days_earlier = now - timedelta(days=10)
    time_to = int(now.timestamp())
    time_from = int(ten_days_earlier.timestamp())
    print(time_from, time_to)

    return time_from, time_to

def get_data(address, timeframe, time_from, time_to):
    url = f"https://public-api.birdeye.so/defi/ohlcv?address={address}&type={timeframe}&time_from={time_from}&time_to={time_to}"
    headers = {"x-chain": "solana", "X-API-KEY": p.birdEye_apiKey}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        json_response = response.json() #get the JSON response
        items = json_response.get('data', {}).get('items', []) #get the items from the JSON response

        processed_data = [{
            'Datetime (UTC)': datetime.fromtimestamp(item['unixTime'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'Open': item['o'],
            'High': item['h'],
            'Low': item['l'],
            'Close': item['c'],
            'Volume': item['v']
        } for item in items]

        df = pd.DataFrame(processed_data)
        
        # Check if the DF has fewer than 20 rows
        if len(df) < 40:
            # Calculate the number of rows to replicate
            rows_to_add = 40 - len(df)

            # replicate the first row
            first_row_replicated = pd.concat([df.iloc[0:1]] * rows_to_add, ignore_index=True)

            # append the replicatre rows to the original DF
            df = pd.concat([df, first_row_replicated], ignore_index=True)

        # Calculate the RSI, MA20, and MA40 with the adjusted lengths
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MA20'] = ta.sma(df['Close'], length=20)
        df['MA40'] = ta.sma(df['Close'], length=40)

        df['Price_above_MA20'] = df['Close'] > df['MA20']
        df['Price_above_MA40'] = df['Close'] > df['MA40']
        df['MA20_above_MA40'] = df['MA20'] > df['MA40']

        print(df.head())

        return df
    else:
        print(f"Failed to retrieve token OHLCV data for address {address}. Status Code: {response.status_code}")
        return pd.DataFrame


#lets do some debugging of only this function above and make sure we are getting unique data

def anaylze_ohlcv_trend(ohlcv_df):
    ohlcv_df["RSI"] = ta.rsi(ohlcv_df['Close'], length=14)
    ohlcv_df['MA20'] = ta.sma(ohlcv_df['Close'], length=20)
    ohlcv_df['MA40'] = ta.sma(ohlcv_df['Close'], length=40)
    ohlcv_df['Price_above_MA20'] = ohlcv_df['Close'] > ohlcv_df['MA20']
    ohlcv_df['Price_above_MA40'] = ohlcv_df['Close'] > ohlcv_df['MA40']
    ohlcv_df['MA20_above_MA40'] = ohlcv_df['MA20'] > ohlcv_df['MA40']

    #intiialize varibles to track the prev high and low
    prev_high = ohlcv_df['High'].iloc[0]
    prev_low = ohlcv_df['Low'].iloc[0]
    higher_highs = True
    higher_lows = True

    #Loop through the rows of the DataFrame to check for higher highs and lower lows
    for i in range (1, len(ohlcv_df)):
        current_high = ohlcv_df['High'].iloc[i]
        current_low = ohlcv_df['Low'].iloc[i]

        if current_high <= prev_high:
            higher_highs = False
        if current_low >= prev_low:
            higher_lows = False
        
        #update the previous high and low for the next iteration
        prev_high = current_high
        prev_low = current_low
    
    price_increase_from_launch = ohlcv_df['Close'].iloc[-1] > ohlcv_df['Open'].iloc[0]

    # Check the mnajority of the last 30 entries for the following conditions
    price_above_ma20_majority = ohlcv_df['Price_above_MA20'].tail(30).mean() > 0.5
    price_above_ma40_majority = ohlcv_df['Price_above_MA40'].tail(30).mean() > 0.5
    ma20_above_ma40_majority = ohlcv_df['MA20_above_MA40'].tail(30).mean() > 0.5

    # Determine if any of the conditions are met
    keep_address = any({
        higher_highs,
        higher_lows,
        price_increase_from_launch,
        price_above_ma20_majority,
        price_above_ma40_majority,
        ma20_above_ma40_majority
    })

    #Prepare the analyis result
    trend_analysis = {
        'higher_highs': higher_highs,
        'higher_lows': higher_lows,
        'price_increase_from_launch': price_increase_from_launch,
        'RSI': ohlcv_df['RSI'].iloc[-1],
        'MA20': ohlcv_df['MA20'].iloc[-1],
        'MA40': ohlcv_df['MA40'].iloc[-1],
        'Price_above_MA20': price_above_ma20_majority,
        'Price_above_MA40': price_above_ma40_majority,
        'MA20_above_MA40': ma20_above_ma40_majority
    }

    # Now check for the majority of true values in the last 30 entries
    conditions_met = any({
        trend_analysis['higher_highs'],
        trend_analysis['higher_lows'],
        trend_analysis['price_increase_from_launch'],
        trend_analysis['Price_above_MA20'],
        trend_analysis['Price_above_MA40'],
        trend_analysis['MA20_above_MA40']
    })

    return trend_analysis


def filter_and_output_addresses(ohlcv_df, current_address, original_df_path, output_df_path):
    print(f"Checking address {current_address} for conditions...")
    # Check if the majoirt oft he last 30 entries meet the conditions
    conditions_met = []
    
    if len(ohlcv_df) >= 30:
        conditions_met.append((ohlcv_df['Price_above_MA20'].tail(30).sum() / 30) > 0.5)
        conditions_met.append((ohlcv_df['Price_above_MA40'].tail(30).sum() / 30) > 0.5)
        conditions_met.append((ohlcv_df['MA20_above_MA40'].tail(30).sum() / 30) > 0.5)    
    
    # Check if 'price_increase_from_launch' is True
    price_increase_from_launch = ohlcv_df['Close'].iloc[-1] > ohlcv_df['Open'].iloc[0]
    conditions_met.append(price_increase_from_launch)

    if any(conditions_met):
        # Check if the address already exists

        # Read the original DataFrame
        original_df = pd.read_csv(original_df_path)

        # find and keep the address in the orginal DF
        filtered_df = original_df[original_df['address'] == current_address]

        #Append the filitered DF to the ouput DF
        if not filtered_df.empty:
            #Check if the output file exists to avioid overwriting the head
            if not os.path.exists(output_df_path):
                filtered_df.to_csv(output_df_path, index=False)
            else:
                filtered_df.to_csv(output_df_path, mode='a', header=False, index=False)  # Append without header
            
            print(f"Address {current_address} meets the conditions. Appended to the {output_df_path}.")

original_df_path = 'hyper-sorted-sol.csv'
output_df_path = 'final_sort.csv'

# Clear the final_sort.csv file or create a new one and write the headers
if os.path.exists(output_df_path):
    os.remove(output_df_path)  # Remove the file if it exists
# Read headers from the original file and write them to the new final sort file
header_df = pd.read_csv(original_df_path, nrows=0)
header_df.to_csv(output_df_path, index=False)

og_df = pd.read_csv(original_df_path)

time_from, time_to = get_time_range()

for index, row in og_df.iterrows():
    address = row['address']
    
    ohlcv_df = get_data(address, timeframe, time_from, time_to)

    if not ohlcv_df.empty:
        trend_analysis = anaylze_ohlcv_trend(ohlcv_df)

        # Call the filter_and_output_addresses function for each address
        filter_and_output_addresses(ohlcv_df, address, original_df_path, output_df_path)

        if any(trend_analysis.values()):
            dexscreener_url = f"https://dexscreener.com/solana/{address}"
            print(f"Anaylsis for address {address} {trend_analysis}\nDexscreener URL: {dexscreener_url}\n")
            print("=" * 50)
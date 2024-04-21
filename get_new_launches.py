import pandas as pd
import datetime
import birdeyebot as bbot
import personal as p
import requests
import time
import json
import nice_funcs as n
import tkinter as tk
from tkinter import messagebox

# CONFIG VARIABLES
MAX_SELL_PERCENTAGE = 80
MIN_TRADES_LAST_HOUR = 10

# THIS ONLY RUNS FOR NEW DATA IF THE BELOW IS TRUE 
new_data = False

if new_data == True:

    # run bird eye bot in order to get the meme token data
    data = bbot.birdEye_bot()
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

new_launches = new_launches(data)

# load the CSV w/ last filer
#df = pd.read_csv("new_launches.csv")

# Create an empty DF for the results
results_df = pd.DataFrame()

# Iterate over each row in the DF
for index, row in new_launches.iterrows():
    #Use the 'token_overview' func from 'nice_funs' for each address
    address = row['address']
    token_data = n.token_overview(address)

    # If token_data is not None, append the data to the reuslts DF
    if (token_data is not None 
        and not token_data.get('rug_pull', False)
        and token_data.get('minimum_trades_met', False)
        and token_data.get('sell_condition_over', False)
        and token_data.get('hasDescription', 'False')):
        if isinstance(token_data, dict):  # Ensuring token_data is in DataFrame format
            token_data = pd.DataFrame([token_data])
        token_data['address'] = address  # Add address to the data
        temp_data = token_data.copy()

        # Before attempting to pop 'priceChangeXhrs', check if the column exists in the DataFrame
        if 'priceChangeXhrs' in temp_data.columns:
            temp_data.pop('priceChangeXhrs')

        # Using pd.concat instead of .append()
        results_df = pd.concat([results_df, temp_data], ignore_index=True)

# After processing all rows, sort the DataFrame by 'buy_percentage'
if 'buy_percentage' in results_df.columns:
    results_df = results_df.sort_values(by='buy_percentage', ascending=False)
    
# Save the results to CSV
results_df.to_csv('hyper-sorted-sol.csv', index=False)

# Get the current date and time
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Create the message
message = f"Finished Scanning and Analyzing Solana Tokens at {current_time}"

# Create a root window, but keep it hidden
root = tk.Tk()
root.withdraw()  # Hide the main window

# Display the message box with an information icon
messagebox.showinfo("Alert", message)

# Destroy the root window after the message box is closed
root.destroy()
    




#Function to nicely print the response
def print_transaction_details(transactions):
    ''' 
    This outputs the last 250 trades from the CA
    '''

    for item in transactions:
        print(f"Transaction Hash: {item['txHash']}")
        print(f"Source: {item['source']}")
        print(f"Block Time: {item['blockUnixTime']}")
        print(f"From: {item['from']['symbol']} (Amount: {item['from']['uiAmount']})")
        print(f"To: {item['to']['symbol']} (Amount: {item['to']['uiAmount']})")
        print("-" * 30)
    print(f"Total Transactions retrieved: {len(transactions)}")



# if new_data == True:

#     not_0_v_data = data.copy()
#     new_launched = new_launches(data)
#     if (len(new_launched) == 0):
#         new_launches = not_0_v_data
#         print("Didn't get ones with 0 percent change")

#         # Contruct the CSV file name with the timestamp
#         csv_filename = 'new_launches.csv'

#         # Save the new launches DF as  CSV file with the gernerated filenmae
#         not_0_v_data.to_csv(csv_filename, index=False)
#     else:
#         # new_launches = new_launched
#         print("WE GOT ONES WITH 0 PERCENT CHANGE!")   

#     # filtered_data = new_launches.copy()

# else:
#     # Contruct the CSV file name with the timestamp
#     csv_filename = 'new_launches.csv'

#     # Save the new launches DF as  CSV file with the gernerated filenmae
#     data.to_csv(csv_filename, index=False)




# Functions to anaylyze the trades
# def analyze_trades(transactions, token_url):
#     buy_count = 0
#     sell_count = 0
#     trades_in_hour = 0
#     current_time = datetime.datetime.now(datetime.timezone.utc)

#     for item in transactions:
#         # Check if the trade is a buy or a sell using the 'side' key directly
#         if item.get('side') == 'buy':
#             buy_count += 1
#         elif item.get('side') == 'sell':
#             sell_count += 1
        
#         # Check if trade occurred in the last hour 
#         trade_time = datetime.datetime.fromtimestamp(item['blockUnixTime'], tz=datetime.timezone.utc)
#         # Calculate the difference as a timedelta object
#         time_difference = current_time - trade_time
#         # Now you can call total_seconds() on the timedelta object
#         if time_difference.total_seconds() < 3600:
#             trades_in_hour += 1

#     # Calculate percentages
#     total_trades = buy_count + sell_count
#     buy_percentage = (buy_count / total_trades * 100) if total_trades else 0
#     sell_percentage = (sell_count / total_trades * 100) if total_trades else 0

#     # If we wanna print info

#     # print(f"Analysis for token URL {token_url}")
#     # print(f"Buy Percentage: {buy_percentage:.2f}%")
#     # print(f"Sell Percentage: {sell_percentage:.2f}%")
#     # print(f"Trades in the last hour: {trades_in_hour}")

#     sell_condition = sell_percentage > MAX_SELL_PERCENTAGE
#     trade_condition = trades_in_hour < MIN_TRADES_LAST_HOUR 

#     return sell_condition, trade_condition


# Here we are filtering new tokens using analyze trades above if they have more than MAX_SELL_PERCENTAGE or less than MIN_TRADES we drop them from the data

#     # Loop through the DF
#     for index, row in new_launches.iterrows():
#         transactions = []
#         token_url = row['token_link']
#         for offset in range(0, 250, 50): # Loop to get 250 trades, grabbing the max 50 at a time

#             # Construct the URL with the address from the current row
#             url = f"https://public-api.birdeye.so/defi/txs/token?address={row['address']}&tx_type=swap&limit=50&tx_type=swap"

#             # Headers including APi Key
#             headers = {"X-API-KEY": p.birdEye_apiKey}

#             # Make the GET request 
#             response = requests.get(url, headers=headers)

#             # Check if request was successful
#             if response.status_code == 200:
#                 # print the response text
#                 response_data = json.loads(response.text)
#                 transactions.extend(response_data['data']['items']) # Extend 
#             else:
#                 print(f"Failed to retrieve data for address {row['address']} at offset {offset}: {response.status_code}")
            
#             #time.sleep(1) # Delay to avoid any hiiting rate limits

#         #print(f"Analysis for CA: {row['address']}")
#         sell_condition, trade_condition = analyze_trades(transactions, token_url)
#         #print('')
#         #print('-' * 30)
#         if sell_condition or trade_condition:
#             filtered_data.drop(index, inplace=True)

#     filtered_data.to_csv('sol_new_removed_trash.csv', index=False)

# use our nice_funcs token overview and do the final filter and output

# here we are suing nice_funcs toen overview to get the token data for each address in the csv
# goal of trying to filter down any rug pulls

# Filter BY OHLC

# look at the last 250 orders and see if it they are mostly buys or sells returns percentage buys vs sells
# look how many trades were in the last hour and return that number

# if the sell % > 70% then drop the token from the list and whole row from the list
# if there are less than 5 trades in the last hour, dropo the token and whole row from the list
# after doing the above 2 things, save new list as 'sol_new_removed_trash.csv'

# RECENT ORDERS - api call, if takes more than 3 days to get api setup --? gpt vision.
    # at least 5+ orders in the last hour

# HIGH TO LOW - if the price is down more than 90% from the high, its a rug


#TVL - thius may be in the token overview api call, if nah --> gpt vision - can we get this in the api?


#WESBITE and TWITTER - this may be in the token overview api call, if nah --? gpt vision


#TRENDING - use all the above in order to build our own trending algo


#LAUNCH DATE - not a huge priortiy, may be in the creation token info







#now we hvae the new_launches csc but there could also be some goodies up in the filtered_Data

#### RULES FOR SNIPER_BOT #####

# if v24hchangepercent is NAN == new launch

# look through api and send in the CA 1 by 1 to try to fulfill the rules below
# recent orders and how many in the last hour? launch date, if we can figure it out? we
# can we see TVL? recent orders same person? can we see trending on Birdeye?


# add GPT Vision in order too look at the chart and also look at the recent orders

# chart would look for an uptrend on the 5min, 15 min and 1 hr

# figure out launch date

# look for a website, if they have it, check to see if it's working, if not -- rug

# the recent orders would look for a lot of orders (5 or more in the past hour)
# double check to make sure that its not all the same person, look at the wallet addresses
# if the order are all red, and it's more than 60% sell we out

# look at the holders and the hcnage of holders over time and the rate of change

# gpt vision look at the rubric in the top left to see 24 hr change

# when there is no 24 hours change on the output we know its brand new

# check for the ss in the top left if its launched in the past 24 hrs and it has the yellow banner

# look at the twitter if they have one in the discrription and note their last tweet

# search the token, and make sure there aren't any other named tokens similar 

# look at PNL and at like 150%, take of 50% == guaranteed profit

# build solana new token creation bot

# look for a mininum of 1 sol size  for larger bots

# can the api look at the trending on Birdeye

# are the arb bots in yet? 
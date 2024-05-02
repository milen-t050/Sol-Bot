import requests
import pandas as pd
import time
import nice_funcs as n
import tweepy
import personal as p
import re
import json
from solana.rpc.api import Client
from solana.keypair import Keypair
from solana.transaction import Transaction


# OUR ADDRESS WE SNIPPING FROM
account_address = "5iuidX4HRaS3uhNLKLWYJdSmh7DzsGTgcJ4aC3GNAT8m"

# FOR A COUPLE FUNCS - THIS IS A TOKEN ADDRESS TO CHECK OPEN POSTION
# TOKEN MINT ADDRESS = SYMBOL
coin_address = "5SuHxgTNE8cbCoK4gfQ7LxpiKgrkENVEQmq78FoAr6La"

USDC_SIZE = 10 # AMOUNT OF USDC PER SNIPE

# Percetnage gain needed
SELL_1_MULTIPLE = 2  # 100% gain
SELL_2_MULTIPLE = 4  # 300% gain
SELL_3_MULTIPLE = 6  # 500% gain



# Percent of sizes based on the orignal amount
# if the 3 below do not = 1, we will leave a moon bag
SELL_1_SIZE = 0.5 # percent of orginal total size
SELL_2_SIZE = 0.25 # percent of orginal total size
SELL_3_SIZE = 0.1 # percent of orginal total size

BASE_URL = "https://public-api.birdeye.so/defi/"


# def pos_info(coin_address):

# def pnl_close(coin_address, tp, sl, sell_amount):
#     '''
#     this will close the position and return the pnl
#     '''

#     while 

def fetch_wallet_holdings(account_address):
    url = "https://api.mainnet-beta.solana.com"
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            account_address,
            {
                "programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
            },
            {
                "encoding": "jsonParsed",
            }
        ]
    }

    response = requests.post(url, json=payload, headers=headers)
    respone_data = response.json()

    mint_addresses = []
    amounts = []

    if 'result' in respone_data and 'value' in respone_data['result']:
        for item in respone_data['result']['value']:
            mint_address = item['account']['data']['parsed']['info']['mint']
            balance = item['account']['data']['parsed']['info']['tokenAmount']['uiAmount']
            if balance > 0:
                mint_addresses.append(mint_address)
                amounts.append(balance)
    
    # Create a DataFrame with mint addresses and amounts where the amount is greater than 0
    df = pd.DataFrame({'coin_address': mint_addresses, 'Amount': amounts})

    return df


def get_position(coin_address):
    """
    Fetches the balance of a specific token given its mint address from a dataframe

    Parameters:
    - dataframe: A pandas DataFrame containing the token balances with colums ['Mint Address', 'Amount']
    - coin_address: The mint address of the token to fetch its balance

    Returns:
    - The balance of the specified token if foundk, otherwise a message indicating the token is not in the wallet
    """

    dataframe = fetch_wallet_holdings(account_address)

    # Save the DataFrame to a CSV file
    dataframe.to_csv("token_per_address.csv", index=False)

    #Check if the token mint address is in the DataFrame
    if coin_address in dataframe['Mint Address'].values:
        # Get the balnce for the specified token
        balance = dataframe.loc[dataframe['Mint Address'] == coin_address, 'Amount'].iloc[0]
        return balance
    else:
        #if the token mint address is not found in the DataFrame, return a message indidcating so
        return 0 # return 0 if the token is not in the wallet
    
#Example usage
# balance_messgae = get_token_balance(dataframe, coin_address)
# print(f"Balance: {balance_messgae} for {coin_address}")

def token_price(coin_address):

    url = f"{BASE_URL}price?address={coin_address}"

    headers = {"x-chain": "solana", "X-APi-KEY": p.birdEye_apiKey}

    response = requests.get(url, headers=headers)

    price_data = response.json()

    if price_data['success']:
        return price_data['data']['value']
    else:
        return None

def buying_df():
    '''address, num_tokens_to_buy, price at wjich to sell_half, price at which to sell all'''

    # read in the final csv
    df = pd.read_csv("hyper-sorted-sol.csv")

    # add new colums to the df
    df['usdc_price'] = None
    df['buy_amount'] = None
    df['sell_1_price'] = None
    df['sell_1_size'] = None
    df['sell_2_price'] = None
    df['sell_2_size'] = None
    df['sell_3_price'] = None
    df['sell_3_size'] = None


    # loop through address colum and update the df
    for index, row in df.iterrows():
        token_address = row['address']
        price = token_price(token_address)

        if price is not None:
            df.at[index, 'usdc_price'] = price
            df.at[index, 'buy_amount'] = USDC_SIZE / price

            df.at[index, 'sell_1_price'] = price * SELL_1_MULTIPLE
            df.at[index, 'sell_1_size'] = df.at[index, 'buy_amount'] * SELL_1_SIZE 

            df.at[index, 'sell_2_price'] = price * SELL_2_MULTIPLE
            df.at[index, 'sell_2_size'] = df.at[index, 'buy_amount'] * SELL_2_SIZE 

            df.at[index, 'sell_3_price'] = price * SELL_3_MULTIPLE
            df.at[index, 'sell_3_size'] = df.at[index, 'buy_amount'] * SELL_3_SIZE 
    
    #save to csv
    df.to_csv("buying_df.csv", index=False)
    print(df)

#buying_df()

def open_position(coin_address):
    '''
    this will loop until the postion is full, it uses the get_token_balance function till its full
    '''
    buying_df = pd.read_csv("buying_df.csv")
    token_info = buying_df[buying_df['address'] == coin_address].to_json(orient='records')[0]

    balance = get_position(coin_address)

    token_size = token_info['buy_amount']

    token_size = float(token_size)
    balance = float(balance)

    size_needed = token_size - balance

    while balance < token_size:
        print(f"Balance is {balance} and size is {token_size} and size needed is {size_needed}")

        # Buy
        # symbol, buy (t/f)
        n.market_order(coin_address, True, size_needed)
        print(f"Just made an order {coin_address[-4:]} of size: {size_needed}")
        time.sleep(10)

        balance = get_position(coin_address)
        size_needed = token_size - balance
    
    print(f"Fully filled our posiiton...")

def kill_switch(coin_address):
    '''This function will close the position fully'''

    print("Closing the position in full...")

def pnl_close(coin_address):
    '''this will check to see if price is > sell1, sell2, sell3 and sell the accordingly'''

    print("Checking to see if we should sell 1,2,3...")

    # Grab only the row with the coin_adress in it and turn it into a json key value pair
    token_info = buying_df[buying_df['address'] == coin_address].to_json(orient='records')[0]

    # get position
    balance = get_position(coin_address)

    # get the price of the token
    price = token_price(coin_address)
    print(f"Balance is {balance} and price is {price}")

    sell_1_till

    if price > token_info['sell_1_price']:
        print(f"price is {price} and sell 1 price is {token_info['sell_1_price']} so selling {token_info['sell_1_size']}")
        n.market_order(coin_address, False, token_info['sell_1_size'])
        print(f"Just made an order {coin_address[:-4]} size {token_info['sell_1_size']}")
        balance = get_position(coin_address)

    # while loop to sell until we only half
    while balance > (half * 1.02): #100,50 .. sell 50, sell 50
        print(f"Balance is {balance} and half is {half}")

        # Sell
        n.market_order(coin_address, False, half)
        print(f"Just made an order {coin_address[-4:]} size {half}")
        time.sleep(10)

        balance = get_position(coin_address)

import requests
import pandas as pd
import time
import nice_funcs as n
import tweepy
import personal as p


# OUR ADDRESS WE SNIPPING FROM
address = "5iuidX4HRaS3uhNLKLWYJdSmh7DzsGTgcJ4aC3GNAT8m"

# FOR A COUPLE FUNCS - THIS IS A TOKEN ADDRESS TO CHECK OPEN POSTION
# TOKEN MINT ADDRESS = SYMBOL
token_mint_address = "5SuHxgTNE8cbCoK4gfQ7LxpiKgrkENVEQmq78FoAr6La"

usdc = 10 # AMOUNT OF USDC PER SNIPE
tp = 100
sl = 90

#Initialize the Twitter API
auth = tweepy.OAuthHandler(p.tweepy_api, p.tweepy_secret)
auth.set_access_token(p.twitter_access_token, p.twitter_token_secret)
twitter_api = tweepy.API(auth)

# def pos_info(token_mint_address):

# def pnl_close(token_mint_address, tp, sl, sell_amount):
#     '''
#     this will close the position and return the pnl
#     '''

#     while 


def tokens_from_usdc(token_mint_address, usdc):
    '''
    pass in the address and usdc amount and it will let you know how many tokens
    '''

    print("figurring out how many tokens to buy")

    return token_size

def open_position(token_mint_address):
    '''
    this will loop until the postion is full, it uses the get_token_balance function till its full
    '''

    balance = get_token_balance(token_mint_address)

    token_size = tokens_from_usdc()

    size_needed = token_size - balance

    while balance < token_size:
        print(f"Balance is {balance} and size is {token_size} and size needed is {size_needed}")

        # Buy
        # symbol, buy (t/f)
        n.market_order(token_mint_address, True, size_needed)
        print(f"Just made an order {token_mint_address[:-4]} size {size_needed}")
        time.sleep(10)

        balance = get_token_balance(token_mint_address)
        size_needed = token_size - balance
    
    print(f"Fully filled our posiiton...")

def kill_switch(token_mint_address):
    '''This function will close the position fully'''

    print("Closing the position in full...")

def sell_half(token_mint_address):
    print("Selling half of the position...") 

    # figure out what half is
    balance = get_token_balance(token_mint_address)
    half = balance / 2

    # while loop to sell until we only half
    while balance > half: #100,50 .. sell 50, sell 50
        print(f"Balance is {balance} and half is {half}")

        # Sell
        n.market_order(token_mint_address, False, half)
        print(f"Just made an order {token_mint_address[:-4]} size {half}")
        time.sleep(10)

        balance = get_token_balance(token_mint_address)

def fetch_wallet_holdings(address):
    url = "https://api.mainnet-beta.solana.com"
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            address,
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
    df = pd.DataFrame({'Mint Address': mint_addresses, 'Amount': amounts})

    return df


def get_token_balance(token_mint_address):
    """
    Fetches the balance of a specific token given its mint address from a dataframe

    Parameters:
    - dataframe: A pandas DataFrame containing the token balances with colums ['Mint Address', 'Amount']
    - token_mint_address: The mint address of the token to fetch its balance

    Returns:
    - The balance of the specified token if foundk, otherwise a message indicating the token is not in the wallet
    """

    dataframe = fetch_wallet_holdings(address)

    print(dataframe)

    # Save the DataFrame to a CSV file
    dataframe.to_csv("token_per_address.csv", index=False)

    #Check if the token mint address is in the DataFrame
    if token_mint_address in dataframe['Mint Address'].values:
        # Get the balnce for the specified token
        balance = dataframe.loc[dataframe['Mint Address'] == token_mint_address, 'Amount'].iloc[0]
        return balance
    else:
        #if the token mint address is not found in the DataFrame, return a message indidcating so
        return f"Token {token_mint_address} not found in the wallet."
    
#Example usage
# balance_messgae = get_token_balance(dataframe, token_mint_address)
# print(f"Balance: {balance_messgae} for {token_mint_address}")

def check_website(url):
    '''This function will check if a website is up and running. It will return a message indicating the status of the website.'''

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return True, f"Wesbite {url} is up and running!"
        else:
            return True, f"Wesbite {url} is reachable but returned a status code of {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Website {url} is unreachable. Error: {e}"

print(check_website("https://www.google.com"))

def check_twitter_account(username):
    try:
        user = twitter_api.get_user(screen_name=username)
        return f"Account @{username} is active. Profile name: {user.name}"
    except Exception as e:
        return f"Could not find account @{username}. Error: {e}"

print(check_twitter_account("elonmusk"))
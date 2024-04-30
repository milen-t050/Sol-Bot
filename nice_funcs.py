import requests
#below is personal api key
import personal as p
import pandas as pd
import pprint
import re


# Constants for minimum trades and maximum sell percentage criteria
MIN_TRADES = 10
MAX_SELL_PERCENTAGE = 70
BASE_URL = "https://public-api.birdeye.so/defi/"
#SAMPLE_ADDRESS = "BY8T5eNHVeDvZ9ueWJ2m8TjtGr4qrJWrznczq7muSd73"

# Pretty printer setup for debugging and clear output of JSON data
pp = pprint.PrettyPrinter(indent=4)

def security_check(address):

    '''
    use:
    - top10HolderPercent, top10UserPercent
    - freezeAuthority, freezeable
    '''

    url = f"{BASE_URL}token_security?address={address}"
    headers = {"x-chain": "solana", "X-API-KEY": p.bird}

    response = requests.get(url, headers=headers)

    return response if response.status_code == 200 else None

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
        'uniqueWallet1hr': data.get('uniqueWallet1hr', 0),  # Number of unique wallets trading the token in the last hour
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
        'minimum_trades_met': total_trades >= MIN_TRADES,
        'sell_condition_over': sell_percentage < MAX_SELL_PERCENTAGE
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

# MIN_TRADES = 10
# MAX_SELL_PERCENTAGE = 80

# # Function to print JSON to readable shi if needed
# def pretty_print_json(data):
#     pp = pprint.PrettyPrinter(indent=4)
#     pp.pprint(data)

# def find_urls(string):
#     # Correct and complete the regex pattern for URL detection
#     regex_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
#     return re.findall(regex_pattern, string)

# # Base URL shoulkd be midfied to fit actual endpoints
# BASE_URL = "https://public-api.birdeye.so/defi/"

# SAMPLE_ADDRES = "BY8T5eNHVeDvZ9ueWJ2m8TjtGr4qrJWrznczq7muSd73"

def token_security_info(address):

    '''

    Freeze authority is like renocuing ownership on eth

    Token Secuiry Info Sample:

    Token Security Info
{   'creationSlot': 259010788,
    'creationTime': 1712578763,
    'creationTx': '3nUxpECGxJLtBGNvkXFDPSGTiX4Afi2Gy1AgqRfjxsudgav5nqcW7QxYBkhjxC4b4kVhi3y12ao5Gxm6u37hCKgx',
    'creatorAddress': '3XMYDBYDApWVreitmcSmJLdyCTU5wHdBKB4aw8WXSRBn',
    'creatorBalance': 0,
    'creatorOwnerAddress': None,
    'creatorPercentage': 0,
    'freezeAuthority': None,
    'freezeable': None,
    'isToken2022': False,
    'isTrueToken': None,
    'lockInfo': None,
    'metaplexOwnerUpdateAuthority': None,
    'metaplexUpdateAuthority': '3XMYDBYDApWVreitmcSmJLdyCTU5wHdBKB4aw8WXSRBn',
    'metaplexUpdateAuthorityBalance': 0,
    'metaplexUpdateAuthorityPercent': 0,
    'mintSlot': 259010788,
    'mintTime': 1712578763,
    'mintTx': '3nUxpECGxJLtBGNvkXFDPSGTiX4Afi2Gy1AgqRfjxsudgav5nqcW7QxYBkhjxC4b4kVhi3y12ao5Gxm6u37hCKgx',
    'mutableMetadata': False,
    'nonTransferable': None,
    'ownerAddress': None,
    'ownerBalance': None,
    'ownerOfOwnerAddress': None,
    'ownerPercentage': None,
    'preMarketHolder': [],
    'top10HolderBalance': 61365746.90792626,
    'top10HolderPercent': 0.6204364389877346,
    'top10UserBalance': 31216759.186860345,
    'top10UserPercent': 0.31561605427362,
    'totalSupply': 98907386.88405663,
    'transferFeeData': None,
    'transferFeeEnable': None}
    '''
    
    # endpoint for secuirty
    url = f"{BASE_URL}/token_security?address={address}"
    headers = {"x-chain": "solana","X-API-KEY": p.birdEye_apiKey}

    # Sending a GET request to the API
    response = requests.get(url, headers=headers)

    # Check if the request was succesful
    if response.status_code == 200:
        security_data = response.json()['data']
        pretty_print_json(security_data)
    else:
        print("Failed to retrieve token overview: ", response.status_code)

def token_creation(address):

    '''
    Token Creation Sample Info:

    Token Creation Info
{   'decimals': 9,
    'owner': '3XMYDBYDApWVreitmcSmJLdyCTU5wHdBKB4aw8WXSRBn',
    'slot': 259010788,
    'tokenAddress': 'EjMMptfh15szffcmPBbHEQYpYck48M4SWcpDDPQxtx12',
    'txHash': '3nUxpECGxJLtBGNvkXFDPSGTiX4Afi2Gy1AgqRfjxsudgav5nqcW7QxYBkhjxC4b4kVhi3y12ao5Gxm6u37hCKgx'}
    '''

    # endpoint for token creation
    url = f"{BASE_URL}/token_creation_info?address={address}"
    headers = {"x-chain": "solana","X-API-KEY": p.birdEye_apiKey}

    # Sending a GET request to the API
    response = requests.get(url, headers=headers)

    # Check if the request was succesful
    if response.status_code == 200:
        creation_data = response.json()['data']
        pretty_print_json(creation_data)
    else:
        print("Failed to retrieve token overview: ", response.status_code)

# overview_info = token_overview(SAMPLE_ADDRES)
# pretty_print_json(overview_info)

# print("Token Security Info")
# token_security_info(SAMPLE_ADDRES)

# print("Token Creation Info")
# token_creation(SAMPLE_ADDRES)

'''

note - use my trade last hour function not thisone,
I actually presort the data anyway so its not needed

    Things we can do with the below
    - add up buy1h and sell1hr to get trade1h
    - go into extensions and get desciprion
    - if nay of the priceChangeXhrs over 80% we're gonna call it a rug
    - uniquewallet24h 
    - v24hUSD could be intresting
    - watch - can see how mant watchers there
    - view24h -can see how many views in the past 24hrs
    - TVL is liquidity


    Token overview sample:

    Token Review
{   'address': 'EjMMptfh15szffcmPBbHEQYpYck48M4SWcpDDPQxtx12',
    'buy1h': 0,
    'buy1hChangePercent': 0,
    'buy24h': 30,
    'buy24hChangePercent': -99.02755267423015,
    'buy2h': 0,
    'buy2hChangePercent': 0,
    'buy30m': 0,
    'buy30mChangePercent': 0,
    'buy4h': 0,
    'buy4hChangePercent': 0,
    'buy8h': 0,
    'buy8hChangePercent': 0,
    'buyHistory1h': 0,
    'buyHistory24h': 3085,
    'buyHistory2h': 0,
    'buyHistory30m': 0,
    'buyHistory4h': 0,
    'buyHistory8h': 0,
    'decimals': 9,
    'extensions': {   'description': 'https://axoonsol.online/\n'
                                     'https://twitter.com/axoSolana\n'
                                     'https://t.me/axo_sol'},
    'history12hPrice': 0.0003963524436726448,
    'history1hPrice': 0.00016463363411896856,
    'history24hPrice': 7.328115721239334e-05,
    'history2hPrice': 0.00017408560107755753,
    'history30mPrice': 0.00015274776465265953,
    'history4hPrice': 0.0001455180034987095,
    'history6hPrice': 0.00014708657643898077,
    'history8hPrice': 0.0001621941284411205,
    'holder': 333,
    'lastTradeHumanTime': '2024-04-10T04:21:11',
    'lastTradeUnixTime': 1712722871,
    'liquidity': 9535.559765148922,
    'logoURI': 'https://img.fotofolio.xyz/?url=https%3A%2F%2Fbafkreicc7yhfgemyw3j2pql5mhsydjixzmznq5wfc26233vepcycop6z2y.ipfs.nftstorage.link',
    'mc': 15005.66034387242,
    'name': 'axo',
    'numberMarkets': 2,
    'price': 0.00015171425326869348,
    'priceChange12hPercent': -61.722387311935634,
    'priceChange1hPercent': -7.847352042863366,
    'priceChange24hPercent': 107.03037320900211,
    'priceChange2hPercent': -12.850774372141958,
    'priceChange30mPercent': -0.6766130989322143,
    'priceChange4hPercent': 4.258064034007257,
    'priceChange6hPercent': 3.1462264890178586,
    'priceChange8hPercent': -6.461316000246835,
    'sell1h': 0,
    'sell1hChangePercent': 0,
    'sell24h': 23,
    'sell24hChangePercent': -99.09234411996843,
    'sell2h': 0,
    'sell2hChangePercent': 0,
    'sell30m': 0,
    'sell30mChangePercent': 0,
    'sell4h': 0,
    'sell4hChangePercent': 0,
    'sell8h': 0,
    'sell8hChangePercent': 0,
    'sellHistory1h': 0,
    'sellHistory24h': 2534,
    'sellHistory2h': 0,
    'sellHistory30m': 0,
    'sellHistory4h': 0,
    'sellHistory8h': 0,
    'supply': 98907386.88405663,
    'symbol': 'axo',
    'trade1h': 0,
    'trade1hChangePercent': 0,
    'trade24h': 53,
    'trade24hChangePercent': -99.0567716675565,
    'trade2h': 0,
    'trade2hChangePercent': 0,
    'trade30m': 0,
    'trade30mChangePercent': 0,
    'trade4h': 0,
    'trade4hChangePercent': 0,
    'trade8h': 0,
    'trade8hChangePercent': 0,
    'tradeHistory1h': 0,
    'tradeHistory24h': 5619,
    'tradeHistory2h': 0,
    'tradeHistory30m': 0,
    'tradeHistory4h': 0,
    'tradeHistory8h': 0,
    'uniqueView1h': 1,
    'uniqueView1hChangePercent': -50,
    'uniqueView24h': 54,
    'uniqueView24hChangePercent': -81.69491525423729,
    'uniqueView2h': 1,
    'uniqueView2hChangePercent': -50,
    'uniqueView30m': 1,
    'uniqueView30mChangePercent': None,
    'uniqueView4h': 3,
    'uniqueView4hChangePercent': -25,
    'uniqueView8h': 4,
    'uniqueView8hChangePercent': -87.5,
    'uniqueViewHistory1h': 2,
    'uniqueViewHistory24h': 295,
    'uniqueViewHistory2h': 2,
    'uniqueViewHistory30m': 0,
    'uniqueViewHistory4h': 4,
    'uniqueViewHistory8h': 32,
    'uniqueWallet1h': 6,
    'uniqueWallet1hChangePercent': -66.66666666666666,
    'uniqueWallet24h': 176,
    'uniqueWallet24hChangePercent': -88.78266411727215,
    'uniqueWallet2h': 23,
    'uniqueWallet2hChangePercent': 0,
    'uniqueWallet30m': 4,
    'uniqueWallet30mChangePercent': 33.33333333333333,
    'uniqueWallet4h': 33,
    'uniqueWallet4hChangePercent': 120,
    'uniqueWallet8h': 44,
    'uniqueWallet8hChangePercent': -61.73913043478261,
    'uniqueWalletHistory1h': 18,
    'uniqueWalletHistory24h': 1569,
    'uniqueWalletHistory2h': 23,
    'uniqueWalletHistory30m': 3,
    'uniqueWalletHistory4h': 15,
    'uniqueWalletHistory8h': 115,
    'v1h': None,
    'v1hChangePercent': None,
    'v1hUSD': None,
    'v24h': 25335392.89723617,
    'v24hChangePercent': -99.22668991128518,
    'v24hUSD': 2661.4021808428743,
    'v2h': None,
    'v2hChangePercent': None,
    'v2hUSD': None,
    'v30m': None,
    'v30mChangePercent': None,
    'v30mUSD': None,
    'v4h': None,
    'v4hChangePercent': None,
    'v4hUSD': None,
    'v8h': None,
    'v8hChangePercent': None,
    'v8hUSD': None,
    'vBuy1h': None,
    'vBuy1hChangePercent': None,
    'vBuy1hUSD': None,
    'vBuy24h': 13118077.191417327,
    'vBuy24hChangePercent': -99.211489177291,
    'vBuy24hUSD': 1376.1771867235811,
    'vBuy2h': None,
    'vBuy2hChangePercent': None,
    'vBuy2hUSD': None,
    'vBuy30m': None,
    'vBuy30mChangePercent': None,
    'vBuy30mUSD': None,
    'vBuy4h': None,
    'vBuy4hChangePercent': None,
    'vBuy4hUSD': None,
    'vBuy8h': None,
    'vBuy8hChangePercent': None,
    'vBuy8hUSD': None,
    'vBuyHistory1h': None,
    'vBuyHistory1hUSD': None,
    'vBuyHistory24h': 1663652141.9387686,
    'vBuyHistory24hUSD': 716251.8303383676,
    'vBuyHistory2h': None,
    'vBuyHistory2hUSD': None,
    'vBuyHistory30m': None,
    'vBuyHistory30mUSD': None,
    'vBuyHistory4h': None,
    'vBuyHistory4hUSD': None,
    'vBuyHistory8h': None,
    'vBuyHistory8hUSD': None,
    'vHistory1h': None,
    'vHistory1hUSD': None,
    'vHistory24h': 3276226867.7163715,
    'vHistory24hUSD': 1429985.1799156168,
    'vHistory2h': None,
    'vHistory2hUSD': None,
    'vHistory30m': None,
    'vHistory30mUSD': None,
    'vHistory4h': None,
    'vHistory4hUSD': None,
    'vHistory8h': None,
    'vHistory8hUSD': None,
    'vSell1h': None,
    'vSell1hChangePercent': None,
    'vSell1hUSD': None,
    'vSell24h': 12217315.705818843,
    'vSell24hChangePercent': -99.24237212015538,
    'vSell24hUSD': 1285.2249941192931,
    'vSell2h': None,
    'vSell2hChangePercent': None,
    'vSell2hUSD': None,
    'vSell30m': None,
    'vSell30mChangePercent': None,
    'vSell30mUSD': None,
    'vSell4h': None,
    'vSell4hChangePercent': None,
    'vSell4hUSD': None,
    'vSell8h': None,
    'vSell8hChangePercent': None,
    'vSell8hUSD': None,
    'vSellHistory1h': None,
    'vSellHistory1hUSD': None,
    'vSellHistory24h': 1612574725.7776031,
    'vSellHistory24hUSD': 713733.349577249,
    'vSellHistory2h': None,
    'vSellHistory2hUSD': None,
    'vSellHistory30m': None,
    'vSellHistory30mUSD': None,
    'vSellHistory4h': None,
    'vSellHistory4hUSD': None,
    'vSellHistory8h': None,
    'vSellHistory8hUSD': None,
    'view1h': 1,
    'view1hChangePercent': None,
    'view24h': 92,
    'view24hChangePercent': -89.30232558139535,
    'view2h': 1,
    'view2hChangePercent': -50,
    'view30m': 1,
    'view30mChangePercent': None,
    'view4h': 3,
    'view4hChangePercent': 50,
    'view8h': 5,
    'view8hChangePercent': -90.9090909090909,
    'viewHistory1h': 0,
    'viewHistory24h': 860,
    'viewHistory2h': 2,
    'viewHistory30m': 0,
    'viewHistory4h': 2,
    'viewHistory8h': 55,
    'watch': None}
'''
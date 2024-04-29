STRATEGY

STEP 1 to build sniper bot
    - get a constant stream of the new tokens launched and then we can loop through the functions below in order to filter out the trash and find the gems 

1. pull all data from bird and get the volume, tvl, 24hr trade, 24hr volume, market cap (under 500k)
    - list of fresh tokens
    - get their CA
        ==  address
    - get their MC
        == mcap
    - get their volume
        == v24hUSD 
    - get their price
    - get their 24hr trades
    - get their tvl (total value locked) == liquidity in output
        liquidity == tvl
    - check recent sells and buy to make sure there is vol
        lastTradeUnixTime == the time last trade, make sure there are trades
        v24hUSD == volume in last 24 hours
        mc == market cap
    - get the number of holders

2. analyze that data to decide which is best to buy
    - use llms
    - use gpt vision
3. buy top 5 memes of the day after data anaylysis

IDEAS
- follow traders profiles, especially other bots
- looking at 24hr vol could be good if we filter out big tokens
    (not good for sniper but may be good for later uses)
- looking at 24hr price change will give us tokens after they pump
# filter to make sure last trade was recent

# filter to make sure liquidity is over Y

- look into the token and see if liq is locked 

Premium APIs
- price of multiple tokens in one call
-get hirstroical price & OHLCV
    - build trading bots with some of our strats witht his data
    - list of trades on a token historically (hopefully we can see the traders too)
        - read the trades to see if its a good opportunity
- get tojen overreview - I wonder what that includes
- creater token info - hopefully shows launch time
*they dont give tredning, but we can build our own tredning algo because we will have recent order data

What can we do with premium and what needs to be gpt Vision
- Look through api and send in the CA 1 by 1 to try to fulfill the rules below.
- Recent order and how many in the last hour? Launch date, if nah we can figure it out? website? twitter? from the description?
- can we see TVL? recent orders same person? can we see treding on birdeye?

================= UPDATES ==========
Update
    - Next up

    TRENDING ALGO - build our own tredning list to prediict what is going to be trending on birdeye.. reverse engineer it so we can make our buys before its listed
    on top 10 trenders

    - look if all transactions are from one user or not

Update
    - We sorted tokens for brand new launch only, while keeping other df for other alpha
    - We can now get price for any token
    - crossroad: I can use gpt vision to do things now or I can wait to get the OHLCV data in the premium api...

    UP NEXT (when Premim API):

    RECENT ORDERS - api call, if takes more than 3 days to get api setup --? gpt vision.
    TVL - thius may be in the token overview api call, if nah --> gpt vision
    WESBITE and TWITTER - this may be in the token overview api call, if nah --? gpt vision
    TRENDING - use all the above in order to build our own trending algo
    LAUNCH DATE - not a huge priortiy, may be in the creation token info

    Red fags are 100% inintial allocation to the team when created, no actiivity on github, vested at the start instead of over time i.e devs are gonna dump 

API
- endpoints: https://docs.birdeye.so/docs/premium-apis-1


later build in rust to make proceess more efficent and faster
maybe use multiple threads to speed up process
    -split the new launches csv into chunks and send each chunk to its own thread and get the output
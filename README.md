Solana Trading Bot
Overview
This Solana Trading Bot is designed to scan the Solana blockchain for newly launched tokens, analyze their potential based on various parameters, and execute trades (buy/sell) efficiently. It leverages the Birdeye API to fetch token data and performs filtering based on liquidity, market cap, and other key indicators. Additionally, the bot can analyze token marketing strategies by checking for associated social media pages (like Twitter) and functional websites. This project also includes a buyer implementation that integrates Solana RPC, smart contracts, and the Solana network to automate trading.

Features
New Token Discovery: Scans the Solana blockchain for newly launched tokens.
Filtering Criteria:
Liquidity (Total Value Locked - TVL)
Market Cap (MC)
Number of holders
Recent trading volume and last trade timestamp
Freezable status and mint authority
Social presence (Twitter, website)
Buyer Implementation:
Ability to sort tokens by specific parameters and execute buy/sell trades.
Automated trading using Solana RPC and solders to manage transactions.
Smart Money Contracts: Trades are executed efficiently by integrating with smart money contracts.
Birdeye API: Used to gather token data, including OHLCV (Open, High, Low, Close, Volume), market cap, and token-specific metrics.
Installation
Prerequisites
Ensure you have the following installed:

Python 3.x
Solana CLI
solana-py library (for Solana RPC)
Birdeye API access (obtain API key from Birdeye Docs)

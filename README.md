# CryptoTwitterTradeBot
Python code to trade cryptocurrencies on Binance.us based on real-time monitoring of tweets. Want to buy DOGE or BTC as soon as Elon Musk tweets about it? Then continue reading!

This code accompanies an article I wrote called [*Trade Cryptocurrencies Based on Live Tweets*](https://www.realcryptoanalysis.com/trade-cryptocurrencies-based-on-live-tweets/), that describes how you can automate cryptocurrency trading based on tweets from influential users. I wrote this code for instructional purposes, but I have been using it to buy and sell small amounts of cryptocurrencies. If you choose to use this code, please do so with caution! Start by testing with small amounts of money!

This code is the full version that I wrote. You can find the simpler version [here](https://github.com/realcryptoanalysis/AutoTradeFromTwitter_Simple). This version includes an automated email message when you make trades and a logger to track your trades.

## Background
I recently wrote an article analyzing the influence of Elon Musk's and Mark Cuban's tweets on the prices of DOGE and BTC. While countless numbers of articles, blogs, and videos claim that Elon Musk moves prices simply by tweeting, I found that these claims were never backed by concrete data. I wanted to determine if their tweets truly influenced crytocurrency prices on a short time scale.

*[The Impact of Major Twitter Influencers on Crypto Prices: Can you really game the system? - Part I](https://www.realcryptoanalysis.com/the-impact-of-major-twitter-influencers-on-crypto-prices-can-you-really-game-the-system-part-i/)*

and 

*[The Impact of Major Twitter Influencers on Crypto Prices: Can you really game the system? - Part II](https://www.realcryptoanalysis.com/the-impact-of-major-twitter-influencers-on-crypto-prices-can-you-really-game-the-system-part-ii/)*

Because there are so many factors influencing the prices of cryptocurrency coins and tokens, I hypothesized that their tweets would not significantly impact prices over short time scales. To my surprise, I discovered that Elon Musk's tweets correlated with statistically significant increases in DOGE price.

Naturally, I decided to write the code to automate the buying and selling of cryptocurrencies based on Tweets. To be clear, I'm not suggesting that you use this information to make trading decisions. That's entirely up to you.

## Getting Twitter and Binance API Keys
To interact with the Twitter and Binance API, you will need to retrieve API keys.

To get your Twitter API keys, you can you follow the steps described [here](https://dev.to/sumedhpatkar/beginners-guide-how-to-apply-for-a-twitter-developer-account-1kh7). If you've correctly followed those instructions, Twitter should present you with a Twitter API key and a Twitter API secret key, Twitter API Access Token, and Twitter API Access Secret Token. Be sure to write both down and save them! These 4 keys are all that we need from the developer account to use the Twitter API.

To get your Binance.us API keys, you can follow the steps described [here](https://cryptopro.app/help/automatic-import/binance-api-key/). After going through steps 1 and 2 at the above link, you should have your Binance API key and API secret key. Write these 2 keys down and save them.

Remember to never share your API keys with anyone.

### Saving your API keys
Once you have your Twitter and Binance.us API keys (you should have a total of 6 keys), you need to save them in JSON files. In the folder `api_keys/`, you'll find two files, `twitter_api_keys.json` and `binance_api_keys.json` that need to be completed. Open the files in a text editor and insert the appropriate keys into each file. Save the JSON files.

## Installation
You will need to install Python3 as well as the following Python packages which can be installed with pip or Anaconda.

```
pip install argparse
pip install boto3
pip install pytz
pip install tweepy==3.10.0
pip install python-binance
```
If installing `python-binance` gave you an error, you may need to run the following command:

```
sudo apt-get install python3-dev
```
before installing `python-binance`.

## How to Run

Now that everything is set up, you can run the code using the following command:

```
python3 stream_tweets_and_trade.py <command line args>
```
where `<command line args>` must be replaced with the following command line arguments.

### Arguments
Here are the command line arguments you will need:

```
usage: stream_tweets_and_trade.py [-h] -u USERNAME -t TICKER -d
                                  AMOUNT_TO_TRADE_USD -s SELL_TIME
                                  -twitter_api TWITTER_API_KEYS_FILE
                                  -binance_api BINANCE_US_API_KEYS_FILE
                                  [-e EMAIL_ADDRESS]

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        Twitter username of person you want to track.
  -t TICKER, --ticker TICKER
                        Cryptocurrency ticker -for tracking on Binance.us.
  -d AMOUNT_TO_TRADE_USD, --amount_to_trade_usd AMOUNT_TO_TRADE_USD
                        Amount of money in USD that you want to trade.
  -s SELL_TIME, --sell_time SELL_TIME
                        Time in hours after the Tweet that you want to sell.
  -twitter_api TWITTER_API_KEYS_FILE, --twitter_api_keys_file TWITTER_API_KEYS_FILE
                        Path to file with Twitter API keys.
  -binance_api BINANCE_US_API_KEYS_FILE, --binance_us_api_keys_file BINANCE_US_API_KEYS_FILE
                        Path to file with Binance.us API keys.
  -e EMAIL_ADDRESS, --email_address EMAIL_ADDRESS
                        Input your email address to get emailed messages when
                        transactions occur and when the Twitter stream starts.
                        This is only valid if using AWS.
```
Note - make sure the ticker you choose is based on Binance.us tickers. For example, purchasing the DOGE/USD pair is DOGEUSD, and purchasing the BTC/USD pair is BTCUSD.

The following example command will monitor Elon Musk's tweets, and buy \$20 USD worth of DOGE on your Binance.us account everytime one of his tweets contains the keyword 'doge' (caps don't matter). It will then wait 6 minutes (0.1 hours) and sell the previously purchased DOGE.

```
python3 stream_tweets_and_trade.py -u elonmusk -t DOGEUSD -d 20 -s 0.1 -twitter_api api_keys/twitter_api_keys.json -binance_api api_keys/binance_api_keys.json
```

If you want to be automatically emailed every time you make a transaction and when the Twitter streaming starts, you can add the `-e <email_address>` command line argument, where `<email_address>` should be replaced with your email address. Note, this email feature will only work on Amazon AWS, and you might need to go into the file `send_email_aws.py` and change the `aws_region` on line 14. This email feature works for me, but I haven't thoroughly tested it for others.

When the application runs, it will create and update a log file and a CSV file recording the transactions in the `saved_data/` folder.




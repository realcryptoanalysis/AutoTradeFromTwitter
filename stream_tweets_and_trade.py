"""Trade crypto based on streaming Tweets in real time."""

import argparse
from datetime import datetime, timedelta
import logging
import os
import pytz
import time
import tweepy

from apis import APIClients
import send_email_aws
import trade


class TradeDataForKilledStream():
    def __init__(self):
        self.side = "buy"
        self.buy_time = None
        self.text = ""

    def save_buy_order_data(self, buy_time, text):
        self.side = "sell"
        self.buy_time = buy_time
        self.text = text


class StreamListener(tweepy.StreamListener):
    def __init__(self, twitter_api=None, binance_api=None, username=None,
                 ticker=None, amount_to_trade_usd=None,
                 trade_data_for_stream_kill=None, logger=None,
                 sell_time=None, email_address=''):
        self.api = twitter_api
        self.username = username
        self.ticker = ticker
        self.ticker_str = ticker[:-3].lower()
        self.amount_to_trade_usd = amount_to_trade_usd
        self.logger = logger
        self.insufficient_funds = False
        self.binance_trader = trade.BinanceTrading(binance_api)
        self.trade_data_for_stream_kill = trade_data_for_stream_kill
        self.sell_time = sell_time
        self.email_address = email_address
        self.executed_qty = 0

    def on_status(self, status):
        if self.trade_data_for_stream_kill.side == "buy":
            if status.user.screen_name.lower() != self.username:
                return
            if not self.from_creator(status):
                return

            if hasattr(status, "extended_tweet"):
                text = status.extended_tweet['full_text']
            else:
                text = status.text

            if not (self.ticker_str in text.lower()):
                return

            self.logger.info(f"start trade")
            print("Buy order placed")
            buy_order = self.create_order('buy')
            if self.insufficient_funds:
                self.logger.info(
                    f"Insufficient funds: {self.insufficient_funds}")
                return
            if buy_order:
                buy_time = datetime.fromtimestamp(
                    float(buy_order['transactTime']) / 1000).astimezone(
                        pytz.timezone('UTC'))
                self.log_data(status, text, buy_order, buy_time, side='buy')
                message = "Bought {} at {}\n\n{}".format(
                    self.ticker, buy_time, buy_order)
                if self.email_address:
                    self.logger.info(f"Sent email")
                    send_email_aws.send_email(self.email_address,
                                              "Trade confirmation",
                                              message)
                    self.logger.info(f"Sent email")
                self.executed_qty = float(buy_order['executedQty'])
                print("Buy order filled")
            else:
                buy_time = datetime.now(pytz.timezone('UTC'))
            self.trade_data_for_stream_kill.save_buy_order_data(buy_time, text)
            self.trade_data_for_stream_kill.side = "sell"

        if self.trade_data_for_stream_kill.side == "sell":
            while True:
                now = datetime.now(pytz.timezone('UTC'))
                if now - self.trade_data_for_stream_kill.buy_time > timedelta(
                        hours=self.sell_time):
                    self.trade_data_for_stream_kill.side = "buy"
                    print("Sell order placed")
                    sell_order = self.create_order('sell')
                    if self.insufficient_funds:
                        return
                    if sell_order:
                        sell_time = datetime.fromtimestamp(
                            float(
                                sell_order['transactTime']) / 1000).astimezone(
                            pytz.timezone('UTC'))
                        self.log_data(status,
                                      self.trade_data_for_stream_kill.text,
                                      sell_order,
                                      sell_time,
                                      side='sell')
                        message = "Sold {} at {}\n\n{}".format(
                            self.ticker, sell_time, sell_order)
                        if self.email_address:
                            send_email_aws.send_email(self.email_address,
                                                      "Trade confirmation",
                                                      message)
                            self.logger.info(f"Sent email")
                        print("Sell order filled")

                    break
                time.sleep(1)

    def on_error(self, status):
        """Tweepy error."""
        self.logger.error(status)

    def log_data(self, status, text, order, trade_time, side):
        """Save all of the data for buys and sells."""

        # write outputs to logger file
        tweet_date_time = (status.created_at).strftime("%m/%d/%Y: %H:%M:%S")
        self.logger.info(f"Screen name: {status.user.screen_name}")
        self.logger.info(f"Tweet: {text}")
        self.logger.info(f"Tweet ID: {status.id}")
        self.logger.info(f"Tweet date time: {tweet_date_time}")
        self.logger.info(f"Trade date time: {trade_time}")
        self.logger.info(f"String to parse: {ticker}")
        self.logger.info(f"{side} order: {order}")
        self.logger.info(f"End trade\n")

        # write outputs to CSV
        price = order['fills'][0]['price']
        commission = order['fills'][0]['commission']
        commissionAsset = order['fills'][0]['commissionAsset']
        qty = order['executedQty']
        usd = order['cummulativeQuoteQty']
        order_type = order['type']
        side = order['side']
        time = (datetime.fromtimestamp(
            float(order['transactTime']) / 1000)).strftime(
            "%m/%d/%Y: %H:%M:%S")

        csv_file_path = os.path.join(saved_dir, "saved_trade_data.csv")
        if not os.path.exists(csv_file_path):
            with open(csv_file_path, "a+") as f:
                f.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
                    "Ticker",
                    "Twitter screen name",
                    "Text",
                    "Status ID",
                    "Status date",
                    "Buy/sell price (USD)",
                    "Buy/sell commission",
                    "Buy/sell commission asset",
                    "Buy/sell quantity",
                    "Cost in USD",
                    "Buy/sell type",
                    "Buy/sell side",
                    "Buy/sell date time"
                ))

        remove_chars = [",", "\n"]
        for c in remove_chars:
            text.replace(c, " ")
        with open(csv_file_path, "a+") as f:
            f.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
                self.ticker,
                status.user.screen_name,
                text,
                status.id,
                tweet_date_time,
                price,
                commission,
                commissionAsset,
                qty,
                usd,
                order_type,
                side,
                time))

    def create_order(self, side):
        """Create the trade order on Binance.us."""

        prices = self.binance_trader.check_balances()
        if 'BNB' in prices.keys():
            amount_of_bnb_usd = float(prices['BNB']['USD invested'])
        else:
            amount_of_bnb_usd = 0
        amount_of_usd = float(prices['USD']['amount'])

        # create buy orders
        if side.lower() == "buy":
            trans_fee = self.amount_to_trade_usd * 0.001
            if (amount_of_usd < self.amount_to_trade_usd or
                   (amount_of_usd - self.amount_to_trade_usd < trans_fee and amount_of_bnb_usd < trans_fee)):
                msg = 'Not enough USD or BNB to buy.'
                msg += ' Balance: {} USD,'.format(prices['USD']['amount'])
                msg += ' Buy request: {} USD.'.format(self.amount_to_trade_usd)
                print(msg)
                self.logger.info(f"Not enough USD to buy."
                                 f"Balance: {prices['USD']['amount']} USD,"
                                 f"Buy request: {self.amount_to_trade_usd} USD")
                self.insufficient_funds = True
                return
            order = self.binance_trader.create_buy_order(self.ticker,
                                                         self.amount_to_trade_usd,
                                                         side='BUY',
                                                         type="MARKET")

        # create sell orders
        elif side.lower() == "sell":
            price_per_ticker_coin = float(
                prices[self.ticker[:-3]]['price per coin (USD)'])
            amount_of_ticker_coin = float(
                prices[self.ticker[:-3]]['amount'])
            amount_to_sell = price_per_ticker_coin * self.executed_qty
            trans_fee = self.amount_to_trade_usd * 0.001
            if amount_of_ticker_coin < self.executed_qty:
                msg = 'Not enough {} to sell.'.format(self.ticker)
                msg += ' Balance: {} - {},'.format(self.ticker[:-3], amount_of_ticker_coin)
                msg += ' Sell request: {} - {}.'.format(self.ticker[:-3], amount_to_sell)
                print(msg)
                self.logger.info(f"Not enough {self.ticker} to sell."
                                 f"Balance: {self.ticker[:-3]} - {amount_of_ticker_coin},"
                                 f"Sell request: {self.ticker[:-3]} - {amount_to_sell}")
                self.insufficient_funds = True
                return
            elif amount_to_sell < 10:
                msg = 'Sell size was < 10 USD. Sell size - '
                msg += ' {} USD.'.format(amount_to_sell)
                print(msg)
                self.logger.info(f"Sell size was < 10 USD."
                                 f"Sell size - {amount_to_sell} USD")
                self.insufficient_funds = True
                return
            elif amount_of_usd < trans_fee and amount_of_bnb_usd < trans_fee:
                msg = 'Not enough USD or BNB to cover transaction fee for selling.'
                msg += ' Balance: USD - {},'.format(amount_of_usd)
                msg += ' Balance: BNB {},'.format(amount_of_bnb_usd)
                msg += ' Transaction fee: USD - {}.'.format(trans_fee)
                print(msg)
                self.logger.info(f"Not enough USD or BNB to cover transaction fee for selling."
                                 f"Balance: USD - {amount_of_usd},"
                                 f"Balance: BNB {amount_of_bnb_usd},"
                                 f"Transaction fee: USD - {trans_fee}")
                self.insufficient_funds = True
                return
            order = self.binance_trader.create_sell_order(self.ticker,
                                                          self.executed_qty,
                                                          side='SELL',
                                                          type="MARKET")
        else:
            raise ValueError("Incorrect side. Must be either 'buy' or 'sell'.")

        self.insufficient_funds = False
        return order

    def from_creator(self, status):
        """Check to ensure the correct user Tweeted."""
        if hasattr(status, 'retweeted_status'):
            return False
        elif status.in_reply_to_status_id:
            return False
        elif status.in_reply_to_screen_name:
            return False
        elif status.in_reply_to_user_id:
            return False
        return True


def create_logger(saved_dir):
    """Set up the logger."""
    files = os.listdir(saved_dir)
    ids = []
    for filename in files:
        if 'logger' in filename:
            id = int(between(filename, 'logger_', '.txt'))
            ids.append(id)

    if len(ids) > 0:
        new_id = max(ids) + 1
        logger_file_path = os.path.join(
            saved_dir, 'logger_{}.txt'.format(new_id))
    else:
        logger_file_path = os.path.join(saved_dir, 'logger_0.txt')

    logging.basicConfig(filename=logger_file_path,
                        filemode='a', level=logging.INFO)
    logger = logging.getLogger()

    return logger


def between(input_str, start, end):
    """Utilities method to get string between two substrings."""
    return input_str[input_str.find(start) + len(start):input_str.rfind(end)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-u', '--username', type=str, required=True,
                        help="Twitter username of person you want to track.")
    parser.add_argument('-t', '--ticker', type=str, required=True,
                        help="Cryptocurrency ticker -for tracking on Binance.us.")
    parser.add_argument('-d', '--amount_to_trade_usd', type=float, required=True,
                        default=10, help="Amount of money in USD that you want to trade.")
    parser.add_argument('-s', '--sell_time', type=float, required=True,
                        help="Time in hours after the Tweet that you want to sell.")
    parser.add_argument('-twitter_api', '--twitter_api_keys_file', type=str,
                        required=True, help="Path to file with Twitter API keys.")
    parser.add_argument('-binance_api', '--binance_us_api_keys_file', type=str,
                        required=True, help="Path to file with Binance.us API keys.")
    email_message = "Input your email address to get emailed messages "
    email_message += "when transactions occur and when the Twitter stream starts. "
    email_message += "This is only valid if using AWS."
    parser.add_argument('-e', '--email_address', type=str, default='',
                        required=False, help=email_message)

    args = parser.parse_args()

    # set up inputs
    username = args.username
    ticker = args.ticker
    amount_to_trade_usd = args.amount_to_trade_usd
    sell_time = args.sell_time
    email_address = args.email_address

    twitter_api_keys_file = args.twitter_api_keys_file
    binance_us_api_keys_file = args.binance_us_api_keys_file

    trade_data_for_stream_kill = TradeDataForKilledStream()

    curr_dir = os.path.dirname(os.path.abspath(__file__))
    saved_dir = os.path.join(curr_dir, 'saved_data')
    if not os.path.exists(saved_dir):
        os.makedirs(saved_dir)
    logger = create_logger(saved_dir)

    while True:
        try:
            print("setting up Twitter stream...")

            if email_address:
                message = "Setting up Twitter stream at {}".format(
                    datetime.now(pytz.timezone('UTC')))
                subject = "Set up new Twitter stream"
                send_email_aws.send_email(email_address, subject, message)
                logger.info(f"Email sent")
            logger.info(f"Setting up Twitter stream...\n\n\n")

            # set up apis
            apis = APIClients()
            apis.set_up_apis(binance_us_api_keys_file=binance_us_api_keys_file,
                             twitter_api_keys_file=twitter_api_keys_file)
            api_clients = apis.clients

            binance_api = api_clients['Binance.us Client']
            twitter_api = api_clients['Twitter Client']

            user = twitter_api.get_user(username)

            # fetching the ID
            user_id = user.id_str

            # listen to tweets and make trades, filtering on usernames and keywords
            tweets_listener = StreamListener(twitter_api=twitter_api,
                                             binance_api=binance_api,
                                             username=username,
                                             ticker=ticker,
                                             amount_to_trade_usd=amount_to_trade_usd,
                                             trade_data_for_stream_kill=trade_data_for_stream_kill,
                                             logger=logger,
                                             sell_time=sell_time,
                                             email_address=email_address)
            stream = tweepy.Stream(twitter_api.auth, tweets_listener)
            stream.filter(follow=[user_id])
        except Exception as e:
            print(e)
            time.sleep(5)
            continue

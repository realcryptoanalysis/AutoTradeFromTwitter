"""Trade cryptocurrencies on Binance.us."""

from binance.exceptions import BinanceAPIException


class BinanceTrading():
    def __init__(self, client):
        self.client = client

    def check_balances(self):
        try:
            self.client.get_account()
        except BinanceAPIException as e:
            print(e)

        balances = self.client.get_account()['balances']
        prices = {}
        for i in balances:
            if float(i['free']) > 0:
                ticker = "{}USD".format(i['asset'])
                info = self.client.get_asset_balance(asset=i['asset'])
                if i['asset'] != 'USD':
                    crypto_to_usd = self.client.get_symbol_ticker(
                        symbol=ticker)['price']
                else:
                    crypto_to_usd = 1
                prices[info['asset']] = {'amount': info['free'],
                                         'USD invested': float(
                    crypto_to_usd) * float(info['free']),
                    'price per coin (USD)': crypto_to_usd}

        return prices

    def create_buy_order(self, symbol, quoteOrderQty, side='BUY',
                         type='MARKET'):
        prices = self.check_balances()
        amount_of_usd = float(prices['USD']['amount'])
        if 'BNB' in prices.keys():
            amount_of_bnb_usd = float(prices['BNB']['USD invested'])
        else:
            amount_of_bnb_usd = 0
        trans_fee = quoteOrderQty * 0.001
        if (amount_of_usd < quoteOrderQty or
                   (amount_of_usd - quoteOrderQty < trans_fee and amount_of_bnb_usd < trans_fee)):
            print('Order not created. Less USD available than order size.')
            return

        try:
            # precision = 8
            # quantity = 0.01
            # price_str = '{:0.0{}f}'.format(quantity, precision)
            buy_order = self.client.create_order(
                symbol=symbol,
                side=side,
                type=type,
                # quantity=price_str,
                quoteOrderQty=quoteOrderQty)
            # automatically send email
            return buy_order
        except BinanceAPIException as e:
            print(e)

    def create_sell_order(self, symbol, quantity, side='SELL',
                          type='MARKET'):
        prices = self.check_balances()
        price_per_ticker_coin = float(
            prices[symbol[:-3]]['price per coin (USD)'])
        if 'BNB' in prices.keys():
            amount_of_bnb_usd = float(prices['BNB']['USD invested'])
        else:
            amount_of_bnb_usd = 0
        amount_of_usd = float(prices['USD']['amount'])
        amount_to_sell = price_per_ticker_coin * quantity

        trans_fee = amount_to_sell * 0.001
        msg = 'Order not filled. '
        if float(prices[symbol[:-3]]['amount']) < quantity:
            msg += 'Less coin available than sell order size.'
            print(msg)
            return
        elif amount_to_sell < 10:
            msg += 'Sell size was less 10 USD.'
            print(msg)
            return
        if (amount_of_usd < trans_fee and amount_of_bnb_usd < trans_fee):
            msg += 'Not enough USD or BNB to cover transaction fee'
            msg += ' for selling.'
            print(msg)
            return

        try:
            # precision = 8
            # quantity = 0.01
            # price_str = '{:0.0{}f}'.format(quantity, precision)
            sell_order = self.client.create_order(
                symbol=symbol,
                side=side,
                type=type,
                # quantity=price_str,
                quantity=quantity)
            # automatically send email
            return sell_order
        except BinanceAPIException as e:
            print(e)

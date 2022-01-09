"""Read API keys for various exchanges and apps."""

import json
import tweepy

from binance.client import Client as binance_client


class APIClients():
    def __init__(self):
        self.clients = None

    def set_up_apis(self, binance_us_api_keys_file=None,
                    twitter_api_keys_file=None):
        """Set up multiple API clients.
        Args:
            binance_us_api_keys_file (string): path to JSON
                file with Binance.us key.
            twitter_api_keys_file (string): path to JSON file
                with Twitter API key.
        """

        api_clients = {}

        if twitter_api_keys_file:
            client, api_key = self.set_up_twitter_api(twitter_api_keys_file)
            api_clients['Twitter Client'] = client
            api_clients['Twitter Key'] = api_key

        if binance_us_api_keys_file:
            client, api_key, api_secret_key = self.set_up_binance_us_client(
                binance_us_api_keys_file)
            api_clients['Binance.us Client'] = client
            api_clients['Binance.us Key'] = api_key
            api_clients['Binance.us Secret Key'] = api_secret_key

        self.clients = api_clients

    def set_up_twitter_api(self, twitter_api_keys_file):
        """Set up twitter api using developer keys.

        Args:
            twitter_api_keys_file (string): full path to json
                file containing the users Twitter API keys.

        Returns:
            api (Twitter api object)
        """

        # read api keys from json file
        with open(twitter_api_keys_file) as f:
            api_keys = json.load(f)

        # Creating the authentication object
        auth = tweepy.OAuthHandler(
            api_keys['twitter_api_key'], api_keys['twitter_api_secret_key'])
        # Setting your access token and secret
        auth.set_access_token(
            api_keys['access_token'], api_keys['access_secret_token'])
        # Creating the API object while passing in auth information
        api = tweepy.API(auth)

        return api, api_keys

    def set_up_binance_us_client(self, binance_us_api_keys_file):
        """Set up Binance.US api keys.

        Args:
            binance_us_api_keys_file (string): full path to json
                file containing the users Binance.us API keys.

        Returns:
            api (Binance.us api object)
        """
        with open(binance_us_api_keys_file) as f:
            api_keys = json.load(f)

        api_key = api_keys['binance_api_key']
        secret_key = api_keys['binance_api_secret_key']

        client = binance_client(
            api_key=api_key, api_secret=secret_key, tld='us')

        return client, api_key, secret_key

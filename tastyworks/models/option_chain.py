from typing import Dict
from dataclasses import dataclass

from datetime import date, datetime
from tastyworks.models.option import Option,OptionType,OptionUnderlyingType


@dataclass
class OptionChain(object):   
    """
    Maps option symbols to Option structures
    Provides filter methods based on type, strike price, expiry, etc.

    Example usage:
        symbol = "AAPL"
        response = await client.get_option_chains(symbol)
        oc = OptionChain(OptionChain.parse(symbol, response))
        
        for strike in oc.get_all_strikes():
            print(strike)

        for expiry in oc.get_all_expirations():
            print(expiry)

        for symbol, option in oc.get(strike=300.0,option_type=OptionType.CALL,expiry=datetime.date(2018,9,21)).items():
            print(symbol, option) 
    """
    
    chain : Dict[str, Option]

    @classmethod
    def parse(cls, ticker : str, response: dict):    
        """
        Parses a response from tasty session into a dict[str, Option]

        Args:
            ticker (str): Ticker symbol of the option chain
            response (dict): Response from tasty session

        Returns:
            dict[str,Option]: dict mapping all option symbols to Option structures
        """

        chain = {}
        for expiry, strikes in response.items():
            for strike, opts in strikes.items():
                chain[opts['call']] = Option(
                    ticker=ticker,
                    expiry=datetime.date(expiry),
                    strike=strike,
                    option_type=OptionType.CALL,
                    underlying_type=OptionUnderlyingType.EQUITY, #todo pass underlying                                        
                )

                chain[opts['put']] = Option(
                    ticker=ticker,
                    expiry=datetime.date(expiry),
                    strike=strike,
                    option_type=OptionType.PUT,
                    underlying_type=OptionUnderlyingType.EQUITY, #todo pass underlying                                        
                )

        
        return chain

    

    
    def get_all_strikes(self):
        return sorted(list(set([option.strike for symbol, option in self.chain.items()])))

    def get_all_expirations(self):
        return sorted(list(set([option.expiry for symbol, option in self.chain.items()])))

    def get(self, **kwargs):
        """
        Get filtered options

        Args:
            **kwargs (*): Option attribute and desired value
        Returns:
            dict: dict mapping option symbols to Option structure that pass the filter
        """
        
        #Construct filter function
        f = lambda o : all([ getattr(o, key) == val for key, val in kwargs.items()])

        #Return filtered options
        return {symbol : o for symbol, o in self.chain.items() if f(o)}       

    def get_at_strike(self, strike):
        return self.get(strike=strike)

    def get_at_expiry(self, expiry):
        return self.get(expiry=strike)

    def get_all_puts(self):
        return self.get(option_type=OptionType.PUT)
    
    def get_all_calls(self):
        return self.get(option_type=OptionType.CALL)
        

    








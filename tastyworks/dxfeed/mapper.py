import json
import logging

from tastyworks.dxfeed import greeks, quote, summary, trade

LOGGER = logging.getLogger(__name__)
KEY_MAP = {}


def map_message(message):
    if isinstance(message, str):
        message = json.loads(message)
    message = message[0]
    if 'data' not in message:
        return None
    data = message['data']
    if isinstance(data[0], str):
        first_sample = False
    else:
        first_sample = True
    msg_type = data[0][0] if first_sample else data[0]

    if quote.Quote.DXFEED_TEXT == msg_type:
        res = quote.Quote(data=data)
    elif greeks.Greeks.DXFEED_TEXT == msg_type:
        res = greeks.Greeks(data=data)
    elif trade.Trade.DXFEED_TEXT == msg_type:
        res = trade.Trade(data=data)
    elif summary.Summary.DXFEED_TEXT == msg_type:
        res = summary.Summary(data=data)

    return res

import asyncio
import calendar
import logging
from datetime import date, timedelta
from decimal import Decimal

from tastyworks.account_streamer import AccountStreamer
from tastyworks.models import option_chain, underlying
from tastyworks.models.account import OrderChangeAccountObject
from tastyworks.models.account_event import (AccountEvent, ActionAccountEvent,
                                             ActionAccountEventType,
                                             ChangeAccountEvent,
                                             ChangeAccountEventType)
from tastyworks.models.option import CompleteOption, Option, OptionType
from tastyworks.models.order import (Order, OrderDetails, OrderPriceEffect, OrderStatus, OrderType)
from tastyworks.models.session import TastyAPISession
from tastyworks.models.trading_account import TradingAccount
from tastyworks.models.underlying import UnderlyingType
from tastyworks.streamer import DataStreamer
from tastyworks.tastyworks_api import tasty_session

LOGGER = logging.getLogger(__name__)

ENABLE_AUTOCLOSE = True
#Limit Example
AUTOCLOSE_ORDER_TYPE = OrderType.LIMIT
CLOSE_LIMIT_DELTA = 0.05
STOP_TRIGGER_DELTA = None
# #Market Example
# AUTOCLOSE_ORDER_TYPE = OrderType.MARKET           NOT TESTED YET
# CLOSE_LIMIT_DELTA = None
# STOP_TRIGGER_DELTA = None
# #Stop Limit Example
# AUTOCLOSE_ORDER_TYPE = OrderType.STOP_LIMIT       NOT RECOMMENDED YET
# CLOSE_LIMIT_DELTA = -0.25
# STOP_TRIGGER_DELTA = -0.20
# #Stop Market Example
# AUTOCLOSE_ORDER_TYPE = OrderType.STOP_MARKET      NOT TESTED YET
# CLOSE_LIMIT_DELTA = None
# STOP_TRIGGER_DELTA = -0.20


async def create_closing_order(session: TastyAPISession, acct: TradingAccount, order: OrderChangeAccountObject,
    close_order_type: OrderType, limit_price_delta: float = None, stop_order_trigger: float = None):

        LOGGER.warning(f"Creating Closing Order: {AUTOCLOSE_ORDER_TYPE.name}")

        #Market Orders don't have price effect, assumes we're Buying first
        flipped_ope = (OrderPriceEffect.CREDIT if (not(getattr(order, 'price_effect_enum', None)) or OrderPriceEffect.DEBIT == order.price_effect_enum.DEBIT)
                      else OrderPriceEffect.DEBIT)

        details = OrderDetails(
            type=close_order_type,
            price=((order.price + limit_price_delta) if close_order_type.is_limit() else None),
            stop_trigger=(stop_order_trigger if close_order_type.is_stop() else None),
            price_effect=flipped_ope,
            is_open_order=False
        )
        new_order = Order(details)

        for leg in order.legs:
            opt = CompleteOption(
                instrument_type=leg.instrument_type,
                symbol_complete=leg.symbol,
                quantity=leg.quantity                
            )
            new_order.add_leg(opt)

        res = await acct.execute_order(new_order, session, dry_run=False)
        LOGGER.info(f"Closing Order opened?: {bool(res)}")
        
async def main_loop(session: TastyAPISession, streamer: AccountStreamer):

    accounts = await TradingAccount.get_remote_accounts(session)
    accounts = [acct for acct in accounts if not acct.is_margin]
    await streamer.add_account_sub([acct.account_number for acct in accounts])

    # Will log out the accounts in use and then create a closing order automatically
    async for item in streamer.listen():
        #LOGGER.info("Original Received item: %s" % item)
        myclass = AccountEvent.from_dict(item)
        is_account_subscribe = type(myclass) is ActionAccountEvent and myclass.action_enum == ActionAccountEventType.ACCOUNT_SUBSCRIBE
        is_order = type(myclass) is ChangeAccountEvent and myclass.type_enum == ChangeAccountEventType.ORDER
            
        if is_account_subscribe or is_order:
            LOGGER.info(myclass)

            if is_order:
                order = myclass.data_obj
                LOGGER.info(order)

                if ENABLE_AUTOCLOSE and order.is_open_order() and order.status_enum.is_filled(): #or order.status_enum.is_active():
                    await create_closing_order(session, accounts[0], myclass.data_obj, 
                                               AUTOCLOSE_ORDER_TYPE, CLOSE_LIMIT_DELTA, STOP_TRIGGER_DELTA)

def main():
    from tastyworks.__auth import USERNAME, PASSWORD
    tasty_client = tasty_session.create_new_session(USERNAME, PASSWORD)

    account_streamer = AccountStreamer(tasty_client)

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main_loop(tasty_client, account_streamer))
    except Exception:
        LOGGER.exception('Exception in main loop')
    finally:
        pending_tasks = [
            task for task in asyncio.Task.all_tasks() if not task.done()
        ]
        loop.run_until_complete(asyncio.gather(*pending_tasks))
        loop.close()


if __name__ == '__main__':
    main()

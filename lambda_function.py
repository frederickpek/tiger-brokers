import time
import traceback
import pandas as pd

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from secret import TIGER_ID, PRIME_ACCOUNT_ID
from utils import telegram_bot_sendtext, gen_ascii_plot

from tigeropen.trade.trade_client import TradeClient
from tigeropen.tiger_open_config import get_client_config
from tigeropen.common.consts import SecurityType, SegmentType, Currency, Market


def main():
    start_time = time.time()

    client_config = get_client_config(
        private_key_path="./private_key.PEM",
        tiger_id=TIGER_ID,
        account=PRIME_ACCOUNT_ID,
    )
    trade_client = TradeClient(client_config)

    def get_asset_balance(base_currency: str):
        portfolio_account = trade_client.get_prime_assets(base_currency=base_currency)
        securities_segment = portfolio_account.segments["S"]
        cash_balance = securities_segment.cash_balance
        gross_position_value = securities_segment.gross_position_value
        exchange_balance = cash_balance + gross_position_value
        return cash_balance, exchange_balance

    usd_cash_balance, exchange_balance_usd = get_asset_balance(base_currency="USD")
    sgd_cash_balance, exchange_balance_sgd = get_asset_balance(base_currency="SGD")

    exchange_balances = pd.Series(
        data={
            "Balance (USD):": f"${exchange_balance_usd:,.2f}",
            "Balance (SGD):": f"${exchange_balance_sgd:,.2f}",
        }
    ).to_string()

    positions = trade_client.get_positions(
        sec_type=SecurityType.STK, currency=Currency.ALL, market=Market.ALL
    )

    position_df = pd.DataFrame(
        [
            *(
                {
                    "asset": position.contract.symbol,
                    "value": f"${position.market_value:,.2f}",
                    "pnl": f"${position.unrealized_pnl:,.2f}",
                }
                for position in positions
            ),
            {
                "asset": "USD",
                "value": f"${usd_cash_balance:,.2f}",
                "pnl": f"$0.00",
            },
            {
                "asset": "SGD",
                "value": f"${sgd_cash_balance:,.2f}",
                "pnl": f"$0.00",
            },
        ]
    )

    start_dt = datetime.now() - timedelta(days=30)
    history = trade_client.get_analytics_asset(
        start_date=str(start_dt.date()), seg_type=SegmentType.SEC, currency=Currency.USD
    )["history"]

    history_plot = gen_ascii_plot(points=[info["asset"] for info in history])

    time_fmt = " %d %B %Y, %H:%M %p"
    time_zone = ZoneInfo("Asia/Singapore")
    dt = datetime.now(tz=time_zone).strftime(time_fmt)

    end_time = time.time()
    duration = f"[Finished in {end_time - start_time:,.3f}s]"

    msg = "\n\n".join(
        [
            dt,
            position_df.to_string(index=False),
            exchange_balances,
            history_plot,
            duration,
        ]
    )

    telegram_bot_sendtext("```" + msg + "```")


def lambda_handler(event=None, context=None):
    try:
        main()
    except Exception as err:
        telegram_bot_sendtext(f"{err}\n{traceback.format_exc()}")


if __name__ == "__main__":
    lambda_handler()

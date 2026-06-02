
import psycopg
import yfinance as yf


TICKERS = [
    "AAPL",
    "AMZN",
    "DIA",
    "GOOGL",
    "META",
    "MSFT",
    "NVDA",
    "QQQ",
    "SPY",
    "TSLA",
]

UPSERT_SQL = """
INSERT INTO stock_prices (
    ticker,
    trade_date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume
)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (ticker, trade_date)
DO UPDATE SET
    open_price = EXCLUDED.open_price,
    high_price = EXCLUDED.high_price,
    low_price = EXCLUDED.low_price,
    close_price = EXCLUDED.close_price,
    volume = EXCLUDED.volume;
"""


def download_recent_prices():
    rows = []

    for ticker in TICKERS:
        print(f"Downloading {ticker}...")

        history = yf.Ticker(ticker).history(
            period="10d",
            interval="1d",
            auto_adjust=False,
        )

        if history.empty:
            print(f"  No rows returned for {ticker}. Skipping.")
            continue

        history = history.dropna(
            subset=["Open", "High", "Low", "Close", "Volume"]
        )

        for trade_date, values in history.iterrows():
            rows.append(
                (
                    ticker,
                    trade_date.date(),
                    float(values["Open"]),
                    float(values["High"]),
                    float(values["Low"]),
                    float(values["Close"]),
                    int(values["Volume"]),
                )
            )

    return rows


def save_to_postgres(rows):

    with psycopg.connect(
        host="localhost",
        dbname="market_dashboard",
        user="postgres",
    ) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(UPSERT_SQL, rows)

    print(f"Saved or updated {len(rows)} rows.")


def main():
    rows = download_recent_prices()

    if not rows:
        print("No market-data rows were downloaded.")
        return

    save_to_postgres(rows)
    print("Market dashboard data is up to date.")


if __name__ == "__main__":
    main()

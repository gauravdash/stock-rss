import time
import yfinance as yf
from flask import Flask, Response
from feedgen.feed import FeedGenerator
import hashlib
import json

# --- Configuration ---
INDICES = {
    "FTSE 100": "^FTSE",
    "S&P 500": "^GSPC",
    "Nifty 50": "^NSEI"
}
UPDATE_INTERVAL_SECONDS = 60 * 60  # 60 minutes
DATA_STORE = {}  # { name: {value, 1d, 1m, 1y, status, timestamp} }

# --- Fetch Index Data ---
def fetch_index_data():
    print(f"\n--- Fetching data at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    for name, symbol in INDICES.items():
        try:
            ticker = yf.Ticker(symbol)

            # Get current price
            try:
                current_value = ticker.fast_info['last_price']
            except Exception:
                current_value = ticker.info.get('regularMarketPrice')

            # Market status
            try:
                market_state = ticker.info.get('marketState', '').upper()
                if market_state == "REGULAR":
                    status = "Open"
                elif market_state in ("CLOSED", "POST", "PRE"):
                    status = "Closed"
                else:
                    status = "Unknown"
            except Exception:
                status = "Unknown"

            # Download historical data
            hist = yf.download(symbol, period="1y", interval="1d", progress=False, auto_adjust=True)
            if hist.empty:
                raise ValueError("No historical data returned")

            # Extract prices
            last_close = hist['Close'].iloc[-1].item()
            prev_close = hist['Close'].iloc[-2].item()
            month_ago = hist['Close'].iloc[-21].item() if len(hist) >= 21 else None
            year_ago = hist['Close'].iloc[0].item()

            # Calculate returns
            one_day_return = ((last_close - prev_close) / prev_close) * 100 if prev_close else None
            one_month_return = ((last_close - month_ago) / month_ago) * 100 if month_ago else None
            one_year_return = ((last_close - year_ago) / year_ago) * 100 if year_ago else None

            # Store results
            timestamp = int(time.time())
            DATA_STORE[name] = {
                'value': int(round(current_value)),
                '1d': round(one_day_return, 1) if one_day_return is not None else None,
                '1m': round(one_month_return, 1) if one_month_return is not None else None,
                '1y': round(one_year_return, 1) if one_year_return is not None else None,
                'status': status,
                'timestamp': timestamp
            }

            # Print to console
            readable_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            print(
                f"{name:<10} | {DATA_STORE[name]['value']:<6} | "
                f"1D: {DATA_STORE[name]['1d']}% | "
                f"1M: {DATA_STORE[name]['1m']}% | "
                f"1Y: {DATA_STORE[name]['1y']}% | "
                f"Status: {status} "
                f"(as of {readable_time})"
            )

        except Exception as e:
            print(f"Error fetching {name}: {e}")

# --- Flask App ---
app = Flask(__name__)

def build_html_table():
    def style_return(value):
        if value is None or value == "N/A":
            return f"<td style='text-align:right;'>{value}</td>"
        try:
            num = float(str(value).replace('%', ''))
            color = "#008000" if num > 0 else "#cc0000" if num < 0 else "black"
            return f"<td style='text-align:right; color:{color};'>{value}</td>"
        except ValueError:
            return f"<td style='text-align:right;'>{value}</td>"

    rows = ""
    for index_name, info in DATA_STORE.items():
        value = info['value']
        status = info.get('status', "Unknown")
        ret_1d = f"{info['1d']}%" if info['1d'] is not None else "N/A"
        ret_1m = f"{info['1m']}%" if info['1m'] is not None else "N/A"
        ret_1y = f"{info['1y']}%" if info['1y'] is not None else "N/A"
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(info['timestamp']))

        rows += f"""
        <tr>
            <td style="text-align:left;">{index_name}</td>
            <td style="text-align:center;">{status}</td>
            <td style="text-align:right;">{value}</td>
            {style_return(ret_1d)}
            {style_return(ret_1m)}
            {style_return(ret_1y)}
            <td style="text-align:center;">{timestamp}</td>
        </tr>
        """

    return f"""
    <style>
        table {{
            border-collapse: collapse;
            width: 100%;
            font-family: Arial, sans-serif;
            font-size: 14px;
        }}
        th, td {{
            border: 1px solid #ccc;
            padding: 6px 8px;
        }}
        th {{
            background-color: #f5f5f5;
            text-align: center;
        }}
        tr:hover {{
            background-color: #f9f9f9;
        }}
    </style>
    <table>
        <tr>
            <th>Index</th>
            <th>Status</th>
            <th>Value</th>
            <th>1D Return</th>
            <th>1M Return</th>
            <th>1Y Return</th>
            <th>Timestamp</th>
        </tr>
        {rows}
    </table>
    """

def needs_update():
    """Check if data needs to be refreshed."""
    if not DATA_STORE:
        return True
    latest_timestamp = max(info['timestamp'] for info in DATA_STORE.values())
    return (time.time() - latest_timestamp) > UPDATE_INTERVAL_SECONDS

@app.route('/rss')
def rss_feed():
    if needs_update():
        fetch_index_data()

    # Ignore timestamps in GUID calculation
    hashable_data = {
        name: {k: v for k, v in info.items() if k != 'timestamp'}
        for name, info in DATA_STORE.items()
    }
    data_hash = hashlib.md5(json.dumps(hashable_data, sort_keys=True).encode()).hexdigest()

    fg = FeedGenerator()
    fg.title('Stock Index Latest Values & Returns')
    fg.link(href='http://localhost:5000/rss')
    fg.description('Latest index values with daily, monthly, and yearly returns')
    fg.generator("Stock RSS Feed Generator")
    fg.language('en')

    table_html = build_html_table()

    fe = fg.add_entry()
    fe.title("Latest Index Data & Returns")
    fe.content(content=f"{table_html}", type='CDATA')
    fe.guid(data_hash, permalink=False)

    if DATA_STORE:
        latest_time = max(info['timestamp'] for info in DATA_STORE.values())
    else:
        latest_time = int(time.time())
    fe.pubDate(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(latest_time)))

    return Response(fg.rss_str(pretty=True), mimetype='application/rss+xml; charset=utf-8')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

"""
This program has the the following Python3 depedancies:

- json          - hashlib
- requests      - mysql.connector
- datetime      - pytz
- time

You will need to setup your VigroCX API. You need to
contact them to allow. You will also need to setup a
MySQL server to log the data. This program executes
every minite and will log the minute by miniute trade
data of coins choosen. 

Impotant, choose the tickers you want to have in the
list variable "tickers". Case doesn't matter. Just the
ticker thats on VigroCX.
"""

import json
import requests
from datetime import datetime
import time
import pytz
import mysql.connector
import hashlib


# Assuming 'America/Vancouver' as the timezone or PST
pst_timezone = pytz.timezone('America/Vancouver')


# API Information - Create: https://virgocx.ca/en-virgocx-api
apiKey = "your_api_key"
apiSecret = "your_api_secret"


# MySQL connection parameters - You will have to setup up a mysql server for
# this program to work. It logs prices.
mysql_config = {
    'host': 'your host', # Probably 'localhost' or '%'
    'user': 'your user',
    'password': 'your password',
    'database': 'your database',
}


# ANSI escape codes for colors
blue_color_code = "\033[94m"  # Blue
purple_color_code = "\033[95m"  # Purple
red_color_code = "\033[91m"  # Red
yellow_color_code = "\033[93m"  # Yellow
reset_color_code = "\033[0m"  # Reset to default color


# Connect to MySQL
conn = mysql.connector.connect(user=mysql_config['user'], password=mysql_config['password'], host=mysql_config['host'], database=mysql_config['database'])
cursor = conn.cursor()

tickers = ['BTC', 'ETH', 'DOT', 'KSM']


def getTrailingStop():
    try:
        trailing_stop_percentage = float(input("\nWhat is the trailing stop percentage in a number? "))
        return trailing_stop_percentage
    except ValueError:
        print('\nPlease enter a number or press CTL+C to quit.\n')
        # Return the result of the recursive call
        return getTrailingStop()
    
    
def getTrailingLimit():
    try:
        trailing_limit_percentage = float(input("\nWhat is the trailing limit percentage in a number? "))
        return trailing_limit_percentage
    except ValueError:
        print('\nPlease enter a number or press CTL+C to quit.\n')
        # Return the result of the recursive call
        return getTrailingLimit()


def print_regular(ticker, highest_high, last_close, percentage_difference, qty):
    print(f"""
    {yellow_color_code}Coin:                     {blue_color_code}{ticker}{reset_color_code}
    {yellow_color_code}Highest High:             {blue_color_code}{highest_high}{reset_color_code}
    {yellow_color_code}Last Close:               {blue_color_code}{last_close}{reset_color_code}
    {yellow_color_code}Percentage Difference:    {blue_color_code}{percentage_difference}{reset_color_code}
    {yellow_color_code}Balance:                  {purple_color_code}{qty}{reset_color_code}
    """)

def print_limit_order(ticker, highest_high, last_close, percentage_difference, qty, price):
    print(f"""
    {yellow_color_code}Coin:                     {blue_color_code}{ticker}{reset_color_code}
    {yellow_color_code}Highest High:             {blue_color_code}{highest_high}{reset_color_code}
    {yellow_color_code}Last Close:               {blue_color_code}{last_close}{reset_color_code}
    {yellow_color_code}Percentage Difference:    {blue_color_code}{percentage_difference}{reset_color_code}
    {yellow_color_code}Balance:                  {purple_color_code}{qty}{reset_color_code}
    
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    This has triggered a Limit Order for {yellow_color_code}{ticker.upper()}{reset_color_code} at price: {red_color_code}{price}{reset_color_code}
    """)


def getCoinDataError(timestamp, error):
    error_log = f"""
    {timestamp}: There was an error.
    {yellow_color_code}{error}
    
    {blue_color_code}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{reset_color_code}
    """
    return error_log


# Function to log placed_limit_order to a file
def log_placed_limit_order(orders):
    with open('placed_limit_order.txt', 'w') as file:
        json.dump(orders, file)


# Function to read placed_limit_order from a file
def read_placed_limit_order():
    try:
        with open('placed_limit_order.txt', 'r') as file:
            orders = json.load(file)
            return orders
    except FileNotFoundError:
        return []


def getCoinData(ticker):
    print(f"\nTransfering Coin Data {ticker.upper()} to Database...\n")
    minute_data = requests.get(f'https://virgocx.ca/api/market/history/kline?symbol={ticker.upper()}/CAD&period=1')
    current_datetime = datetime.now()
    timestamp = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

    try:
        data = json.loads(minute_data.text)
    except json.JSONDecodeError as e:
        # Log the JSON decoding error
        with open('getCoinData.log', 'a+') as log_file:
            log_file.write(getCoinDataError(timestamp, e))
        return
    except Exception as e:
        # Log other exceptions
        with open('getCoinData.log', 'a+') as log_file:
            log_file.write(getCoinDataError(timestamp, e))
        return

    for timestamp, value in data.items():
        if timestamp == 'data':
            for data_point in value:
                # Extract the timestamp in milliseconds
                timestamp_milliseconds = data_point['createTime']

                # Convert to seconds and create a datetime object in UTC
                timestamp_seconds = timestamp_milliseconds / 1000
                utc_datetime = datetime.utcfromtimestamp(timestamp_seconds)

                # Convert to PST
                pst_datetime = utc_datetime.replace(tzinfo=pytz.utc).astimezone(pst_timezone)

                # Prepare the data for MySQL insertion
                mysql_data = (
                    timestamp_milliseconds,
                    pst_datetime.strftime('%Y-%m-%d %H:%M:%S'),  # Format datetime as a string
                    data_point['open'],
                    data_point['high'],
                    data_point['low'],
                    data_point['close'],
                )

                # MySQL SELECT query to check for existing records using "id" as primary key
                select_query = f"SELECT * FROM vigrocx_db.{ticker.lower()} WHERE id = %s"

                # Execute the SELECT query with the current data_point values
                cursor.execute(select_query, (timestamp_milliseconds,))

                # Fetch the result
                existing_record = cursor.fetchone()

                # Check if a record with the same id already exists
                if not existing_record:
                    # MySQL INSERT statement
                    insert_query = f"INSERT INTO vigrocx_db.{ticker.lower()} (id, time, open, high, low, close) VALUES (%s, %s, %s, %s, %s, %s)"

                    # Execute the INSERT statement
                    cursor.execute(insert_query, mysql_data)


def place_limit_order(apiKey, apiSecret, symbol, category, order_type, price, qty):
    parameters = {
        "apiKey": apiKey,
        "apiSecret": apiSecret,
        "category": category,
        "symbol": symbol,
        "type": order_type,
        "price": price,
        "qty": qty
    }
    
    hash_string = f"{parameters['apiKey']}{parameters['apiSecret']}{parameters['category']}{parameters['price']}{parameters['qty']}{parameters['symbol']}{parameters['type']}"

    # Step 3: Execute MD5 algorithm
    signature = hashlib.md5(hash_string.encode('utf-8')).hexdigest()

    # Step 4: Final parameters list
    final_params = {
        "symbol": symbol,
        "category": category,
        "type": order_type,
        "price": price,
        "qty": qty,
        "apiKey": apiKey,
        "sign": signature
    }

    return final_params


def call_place_order_api(params):
    response = requests.post(
        f"https://virgocx.ca/api/member/addOrder?apiKey={params['apiKey']}&symbol={params['symbol']}&sign={params['sign']}&category={params['category']}&qty={params['qty']}&price={params['price']}&type={params['type']}"
    )
    result = response.json()
    
    current_datetime = datetime.now()
    timestamp = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    # Log the response
    with open('place_order.log', 'a+') as log_file:
        print('\n~*~*~ Submission Response ~*~*~\n')
        print(timestamp)
        log_file.write('\n~*~*~ Submission Response ~*~*~\n')
        log_file.write(timestamp)
        for key, value in result.items():
            print(f"{key}: {value}")
            log_file.write(f"{key}: {value}\n")
        print('\n*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*\n')
        log_file.write('*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*\n')
                    
                    
def checkCoinThreshold(ticker, limit, stop):
    # Select high
    select_high = f"SELECT MAX(high) FROM vigrocx_db.{ticker.lower()}"
    # Execute the SELECT query
    cursor.execute(select_high)
    # Fetch the result
    result = cursor.fetchone()
    # The result will be a tuple with the highest value, access it like result[0]
    highest_high = result[0]
    
    # MySQL SELECT query to get the last close value
    select_last_close_query = f"SELECT close FROM vigrocx_db.{ticker.lower()} ORDER BY time DESC LIMIT 1"

    # Execute the SELECT query
    cursor.execute(select_last_close_query)

    # Fetch the result
    last_close_result = cursor.fetchone()

    # Extract the last close value from the result
    last_close = last_close_result[0]

    # Calculate the current percentage difference
    percentage_difference = ((last_close - highest_high) / last_close) * 100

    # Parameters (API Key and Secret Globally Set)
    symbol = f"{ticker.upper()}/CAD"
    category = 1  # 1 for Limit Order
    order_type = 2  # 2 for Sell
    price = float("{:.2f}".format(last_close - ((last_close * limit)/100)))
    # Set quantity
    coins_own = requests.get(f'https://virgocx.ca/api/member/accounts?apiKey=68fd5f0329804e67819ed6398e4cc891&sign=3f7bccde9402868a693ddf86452e135b')
    data = json.loads(coins_own.text)
    for key, value in data.items():
        if key == 'data':
            for data_point in value:
                if data_point['coinName'] == ticker.upper():
                    qty = data_point['balance']

    # Check if the percentage difference is below -6% if yes trigger sell limit at 2% less than current base price.
    if percentage_difference < stop:
        placed_limit_order = read_placed_limit_order()
        if ticker.upper() not in placed_limit_order:
            if qty > 0:
                print_limit_order(ticker, highest_high, last_close, percentage_difference, qty, price)
                params = place_limit_order(apiKey, apiSecret, symbol, category, order_type, price, qty)
                call_place_order_api(params)
                placed_limit_order.append(ticker.upper())
                log_placed_limit_order(placed_limit_order)
            else:
                print_regular(ticker, highest_high, last_close, percentage_difference, qty)
        else:
            print_regular(ticker, highest_high, last_close, percentage_difference, qty)           
    else:
        print_regular(ticker, highest_high, last_close, percentage_difference, qty)
        

trailing_stop = getTrailingStop()
trailing_limit = getTrailingLimit()

while True:
    try:
        for ticker in tickers:
            getCoinData(ticker)
            checkCoinThreshold(ticker, trailing_limit, trailing_stop)
            # Commit MySQL changes
            conn.commit()
        print('\n~*~ Press CTL+C to quit. ~*~\n')
        time.sleep(60)
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Cleaning up and exiting.\n")
        time.sleep(1)
        if 'cursor' in locals() and cursor is not None:
            print('\nClosing MySQL cursor')
            cursor.close()
            time.sleep(1)
        if 'conn' in locals() and conn is not None:
            print('Closing MySQL Connection\n')
            conn.close()
        break  # Exit the while loop
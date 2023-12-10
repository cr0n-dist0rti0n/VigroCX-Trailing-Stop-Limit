# VigroCX-Trailing-Stop-Limit
VigroCX, which is a Canadian Crypto Exchange, does not offer Trailing Stop Limit sell orders. This program is does a Trailing Stop Limit from the highest price to current price. It will collect data as it goes so the start of the "highest price" would be the first initialisation of the program. I will probably change this in the future to so that a user can set their timeperiod.

This program collects minute to minute data of any listed blockchains in "tickers" vairable. A MySQL table needs to be setup for each currency along with the reqired columns. You can modify the code below to create those colomns in a database:

CREATE TABLE your_table_name (
    id INT PRIMARY KEY,
    time TIMESTAMP,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT
);

This program has the the following Python3 depedancies:

- json
- requests
- datetime
- time
- hashlib
- mysql.connector
- pytz

It also requires the setup of a MySQL Database.

You will need to setup your VigroCX API. You need to
contact them to allow. You will also need to setup a
MySQL server to log the data. This program executes
every minite and will log the minute by miniute trade
data of coins choosen. 

Impotant, choose the tickers you want to have in the
list variable "tickers". Case doesn't matter. Just the
ticker thats on VigroCX.

I take no responsibility for any faulty or unintended sales / investments. Use at your own risk. I've only tested this on Linux based system. Not sure how it will run in MS Windows.

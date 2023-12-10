# VigroCX-Trailing-Stop-Limit
VigroCX, which is a Canadian Crypto Exchange, does not offer Trailing Stop Limit sell orders. This program is does a Trailing Stop Limit from the highest price to current price. It will collect data as it goes so the start of the "highest price" would be the first initialisation of the program. 

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

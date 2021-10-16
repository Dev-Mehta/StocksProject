# Project - Stock Market Prediction Using ML
As we all know, 90% of traders lose their money in the stock market.
 
But what do you think is the reason they lose their money?

The answer to this simple question is - Psychology. Warren Buffet has said this once - "Stock market is a device that transfers money from impatient to patient."

As computer engineering students, we could not have taught everybody about how to control their emotions, So instead we thought of making a trading system which never considers any emotion - that is our computers.

We have used 5 basic factors to develop ML model which gives buy and sell calls based on market scenario.
 - MACD
 - RSI
 - EMA Crossovers
 - Volume
 - Simple Price Action

## How to Run this Project?
To run this project in your PC, you need to have Python and Git installed.
Then you can go to command prompt and type,
```
git clone https://github.com/Dev-Mehta/StocksProject.git
```
After running this command this project will be cloned into your PC. Then you can change directory to this project and run another command.
```
pip install -r requirements.txt
```
This command will install all the requirements required to run this project.
```
python manage.py runserver
```
Use this command to fire up a local webserver just like we use XAMPP to run php programs, this command fires a webserver at port 8000 where our website will be running

Now you can open [http://127.0.0.1:8000](http://127.0.0.1:8000) to test the website locally.
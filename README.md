# CS50 – Final Project- Portfolio Analysis by A.I.
#### Video Demo:  <URL HERE>
#### Description: 
  In my final project, I develop a weak A.I. to recommend a stock to add into user portfolio. This development is built on CS50 problem set – Finance web application which allow to provide basic Functions of Quote, Buy , Sell, Statement. Now, I added additional basic analysis feature to 1) show 3 months stock price graph, 2) the risk level of your portfolio, 3) recommend stock based on risk level. In order to do that, I work in CS50 IDE environment and using Python, SQL and HTML language to develop the A.I. feature.

##### Architecture: Using Flask as the web framework and implement with Model(SQL & CSV) - View(HTML & CSS) - Controller(Python) design pattern with consume IEX Cloud API for data collection

![CS50 – Final Project](https://user-images.githubusercontent.com/83693925/127447079-5a635d3e-a258-46a0-8c0b-afa24937f6ba.jpg)
  
#### Coding:
#####3 months stock price graph:
Quote.html  -  embed the 3 months stock price graph. 
Application.py – modify the code to consume API in IEX Cloud to request 3 months specified stock
  
#####Portfolio Analysis:
Portfolio Analysis.html – new page to show analysis result
Appliction.py – add /portfolio route with programming to 
-	Call the statement function from the helpers.py to show the current user statement record
-	Consume API in IEX Cloud to request 3 months x100stocks by calling 100 stocks in the SP500 csv file (due to limited credit in IEX Cloud, I limit to 100 stocks and just get the data once (from May to July 2021). It is supposed to update the data every day to have latest 3 months)
-	Convert the data into dataframe (pandas) and put it into SQL database for permanent records
-	Extract the specified data from  the SQL database and convert back to dataframe for data manipulation
-	Calculate the average price of the stocks in portfolio
-	Calculate the variance and standard deviation for risk assessment
-	Calculate the correlation coefficient against each stocks in the selected 100
-	Based on the risk level to recommend either the most positive correlated stock or the most negative correlated stock
Helpers.py
-	Add the get_avg_prices function to for average calculation
-	Add the correlation function to calculation the correlation coefficient of user portfolio against selected 100 stocks by using Pearson Correlation Coefficient method

  

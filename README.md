# Bitcoin Sentiment
 Project for the course "Introduction to Programming"

## Overview
The idea for this project originated in the increasing importance of social media for asset prices, especially crypto currencies. 

This script creates a dashboard which plots a time series of bitcoin prices and a generated time series of daily sentiment scores, using Natural Language Toolkits Vader algorithm (trained for social media texts ), derived from the top 100 posts of the reddit.com/r/bitcoin subreddit. 

With this dashboard one can examine the relationship between social media sentiment and the bitcoin price.

### Structure
* app.py: main file, run this in python to launch the dashboard
* functions.py: contains function for access to reddit data
* assets
	* style.css: style file for the dashboard, taken from https://github.com/plotly/dash-sample-apps/tree/master/apps/dash-web-trader
	* bitcoin_logo.png: bitcoin logo for the dashboard
* data
	* reddit_posts.csv: stored daily top 100 posts in r/bitcoin from 01.01.2018, updated when running app.py


## Dashboard
![Alt text](/assets/preview.png)

The dashboard can be started by running app.py. This creates a locally hosted dashboard and a link to access it will be in the console output (cmd+click on it)

The dashboard is created using the plotly dash package, which allows to build interactive dashboards in Python.

In the dashboard we set the the range of dates to be displayed and the data to be shown can be selected in the dropdown menu.

## Data
Here a short description on how the underlying data is generated. The code is explained in more detail in the comments. 

### First Data Source: Pushshift
The Pushshift API allows one to download reddit posts. In this project we will download the daily top 100 posts (ordered by score) of a given subreddit. 

**Past Data**
Past data (stored in reddit_posts.csv) has been downloaded using the getPushshiftData.

**Updated Data**
Each time app.py is run, the data is updated: 
1. Check if yesterday is larger than the last stored date in the already existing data. 
2. If yes, download the top 100 posts for the remaining days
	* Notice: Sometimes Pushshift does not already have stored the latest posts. Therefore we omit all dates where we have less than 100 entries, so the last dates in the existing data is always the last day we have 100 entries. When updating the data again, the data might be available and we get a new last date in the stored data. Occasionally, data is not available for some dates (ca. 25 times sind 01.01.2018)

### Second Data Source: Quandl
Using the Quandl API we download daily price data from 01.01.2018 until today.

## Natural Language Processing 
The Natural Language Processing Toolkit is used to determine the sentiment of the reddit posts and to create a daily series of sentiment scores as described below:

1. For each day, we tokenise each of the 100 entries: First we filter out stop words (meaning words which do add any meaning to the entries) and then we remove any punctuation or emojis. 
2. Using Natural Language Toolkits Vader Sentiment Analyizer (which is specifically for social media texts) we assign each of the 100 daily posts a sentiment score from -1 to 1.
3. Now an arbitrary threshold is set from which onwards a posts is considered negative, neutral or positive. (Below -0.2 negative, above 0.2 positive, between neural).
4. For each day a mean of the 100 sentiment score is calculated to receive a time series.


# Bitcoin Sentiment
 Project for the course "Introduction to Programming"

## Overview
The project is structured into 2 files. The file “functions.py” contains all functions needed for the data queries. The file “app.py” contains the construction of the data and the code for the dashboard. Running app.py generates a link, with which one can access the dashboard in the browser. 

The “style.css” file was taken from [dash-sample-apps/apps/dash-web-trader at master · plotly/dash-sample-apps · GitHub](https://github.com/plotly/dash-sample-apps/tree/master/apps/dash-web-trader), but was edited.

The “reddit_posts.csv” file was created using the  getPushshiftData function in “functions.py” and is updated every time “app.py” is run, it starts at 1.1.2018.

With the data from reddit_posts.csv a daily sentiment score is calculated with the Natural Language Toolkit Vader Sentiment Intensity Analyzer, which is a rule based model for sentiment analysis of social media texts.

Additionally a bitcoin price series is downloaded from Quandl. This two dataseries are to be plotted on a Plotly Dash dashboard and then can be used whether a change in social media (reddit) sentiment can predict a price change in Bitcoin or the other way around. 

And we can see that there is quite some relationship among both timeseries, as we can see that both move quiet closely together. Notice however, that the size of changes does not correspond, as both values are in different units. 

## Data
There are two data sources for this project. First there is the Pushshift API with which one can download reddit posts. The function getPushshift data downloads the top 100 reddit posts (with the highest score)  after and before given timestamps. This data is then saved to a data frame, where each column presents a given date, indicated by a timestamp of the day at midnight.

From these collected daily entries those, which have less than 100 entries are filtered out. This can happen because on some dates the Pushshift API does not have data stored, so we have 0 entries for that given date. 

In the end we receive a data frame where columns represent the 100 entries for a given date. This data frame is then preprocessed for our natural language processing algorithm. For each item in the top 100 posts per days certain stop words (words which do not add any meaning to the posts, like “and” ,”this”, etc.)  and punctuation and emojis are filtered out. This is done with the English stop words from the natural language processing toolkit and the RegexpTokenizer. Now for each of the daily top 100 reddit posts we get a sentiment score ranging from -1 to 1. We now set an arbitrary threshold from which onwards we view a post as clearly negative, positive or neutral. For this project 0.2 is chosen, so posts with a polarity score over 0.2 are considered positive, those with a score below -0.2 are considered negative. Those in-between are considered neutral. Now for each day the mean score is calculated. 

This time series, a 30-day moving average of this time series and the bitcoin price series are now merged together. 

We now can plot this on our plotly dash dashboard. 

## Dashboard
To create a dashboard we use the plotly dash package, which allows to build interactive dashboards in Python.

We want our dashboard to have a sidebar with a short description and user controls on the left hand side, and the graphs being displayed on the right hand side.

Therefore we initialise a DatePickerRange and Dropdown on the left hand side, and link those with callbacks on the bottom of the “app.py” file to the graphs on the right hand side. For the first graph we want a graph with two y-axis, for the second graph one y-axis is enough, as the values are in the same unit (as they represent the daily percentage change). 
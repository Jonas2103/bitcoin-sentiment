# Necessary Import
import pandas as pd
import requests
import datetime
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
import numpy as np

# Initialize Tokenizer and set stopwords
tokenizer = RegexpTokenizer(r'\w+')
stop_words = stopwords.words('english')

# Define functions for data download
def getPushshiftData(after, before, sub):
    """ Returns list of titles of top 100 reddit posts for a specific subreddit for a given time period
    Args:
        after: startpoint of the time period
        before: end point of the time period
        sub: specific subreddit
    """
    url = 'https://api.pushshift.io/reddit/submission/search/?after='+str(after)+'&before='+str(before)+'&subreddit='+str(sub)+'&limit=1000&sort_type=score&sort=desc'
    r = requests.get(url).json()
    titles = []
    # access title element in downloaded json file
    for x in r['data']:
        titles.append(x['title'])
    return titles


def getDates(start, end):
    """Returns a dataframe of daily start and end dates for the reddit request
    Args:
        start: start date
        end: end date
    """
    delta = end - start
    after_days = [start + datetime.timedelta(days=i) for i in range(delta.days + 1)]
    before_days = [(start + datetime.timedelta(days=1)) + datetime.timedelta(days=i) for i in range(delta.days + 1)]
    df = pd.DataFrame({'after': after_days, 'before': before_days})
    df['after'] = (df['after'] - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
    df['before'] = (df['before'] - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
    return df 


def process_text(headlines):
    """Tokenizes the language input, removes stop words, emojis and puncutation
    Args:
        headlines: list of headlines/titles
    """
    tokens = []
    for line in headlines:
        toks = tokenizer.tokenize(line)
        toks = [t.lower() for t in toks if t.lower() not in stop_words]
        tokens.append(' '.join(toks))
    
    return tokens


def updateData(existing_data):
    """Updates existing_data, to include all dates until yesterday
    existing_data: dataframe of existing data, where in each column there are the top 100 reddit posts in a given subreddit on a given day
    """
    temp_data = existing_data
    # Create a list/index of existing dates
    dates = pd.to_datetime(temp_data.columns.astype(int), unit='s')
    # Calculate timestamp for yesterday at midnight (to get last starting point for data download)
    yesterday_midnight = datetime.datetime.combine(datetime.date.today()-datetime.timedelta(days=1), datetime.datetime.min.time())

    # Check if last datapoint is earlier than yesterday midnight#
    if yesterday_midnight > dates[-1]:
        # Calculate starting point for new data download (one day after last entry) and generate series of timestamps
        start = dates[-1] + datetime.timedelta(days=1)
        ts = getDates(start, yesterday_midnight)

        # Create new dictionary with missing entries
        temp_dict={}
        for i in ts.index:
            temp_dict[ts['after'][i]]=getPushshiftData(ts['after'][i], ts['before'][i], "bitcoin")
        
        # Correct for dates with less than 100 posts, whole date as missing value, to not falsify sentiment score
        adj_dict = {}
        for i in temp_dict.keys():
            if len(temp_dict[i]) == 100:
                adj_dict[i] = temp_dict[i]
            else:
                adj_dict[i] = [np.nan] * 100

        # Now append data to original / input data
        for i in adj_dict.keys():
            temp_data[i] = adj_dict[i]
        
        # Reorder columns to keep chronological order
        temp_data.columns = temp_data.columns.astype(int)
        temp_data = temp_data.reindex(sorted(temp_data.columns), axis=1)
        
        # Remove date columns with less than 100 values (we set those to np.nan)
        temp_data = temp_data.drop(temp_data.select_dtypes('float').columns, axis=1)
    
    return temp_data


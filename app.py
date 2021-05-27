# Necessary Imports
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import functions
import quandl
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA
import datetime

        
# Reading Existing Data
data = pd.read_csv(r'data/reddit_posts.csv')

# Update by additional by missing days (data starts at 1.1.2018, additional days = yesterday - last day already in data
new_data = functions.updateData(data) # This step might take a while
new_data.to_csv(r'data/reddit_posts.csv', index=False) # Save data to csv for next time

# Get dates from data column names, define start and end point for bitcoin price download
dates = pd.to_datetime(new_data.columns.astype(int), unit='s')
start = dates[0].date()
end = datetime.date.today()

# Get Bitcoin Price Data
quandl.ApiConfig.api_key = "zyETYrDnqS3e4kcfs8Qy" # Insert you API code here
bitcoin_price = quandl.get("BCHAIN/MKPRU", start_date=start.strftime("%Y-%m-%d"), end_date=end.strftime("%Y-%m-%d"))

# Now data is preprocessed for natural language processing
# Removing punctuation, emojis and filler words
for i in new_data.columns:
    new_data[i] = functions.process_text(new_data[i])

# Initizalize Sentiment Intensity Analyzer
sia = SIA()
scores = pd.DataFrame()

# Calculte compound polarity score for each reddit post title
for i in new_data.columns:
    results = []
    for line in new_data[i]:
        pol_score = sia.polarity_scores(line)
        results.append(pol_score['compound']) # Pol score returns a negative, neutral and positive value, we select only the compound value
    scores[i] = results

# Convert all scores above a certain threshold (here 0.2) into 1, all below a threshold (-0.2) into -1. Between = 0
scores = scores.apply(lambda x: [1 if y > 0.2 else y for y in x])
scores = scores.apply(lambda x: [-1 if y < -0.2 else y for y in x])
scores = scores.apply(lambda x: [0 if 0.2 >= y >= -0.2 else y for y in x])

# For each date now the mean of the converted scores is calculated
sen_values = []
sen_dates = []

for i in scores.columns:
    sen_values.append(scores[i].mean())
    sen_dates.append(pd.to_datetime(i, unit='s'))

# Create DataFrame from Result
sentiment = pd.DataFrame({'Dates': sen_dates, 'Sentiment': sen_values})
sentiment = sentiment.set_index('Dates')
sentiment['Rolling Sentiment'] = sentiment['Sentiment'].rolling(30).mean()

# Merge DataFrame with Bitcoin Price DataFrame
# Add columns for daily returns/changes
df = bitcoin_price.merge(sentiment, left_index=True, right_index=True)
df['Dates'] = df.index
df['Change Sentiment'] = df['Sentiment'].pct_change()
df['Change Rolling Sentiment'] = df['Rolling Sentiment'].pct_change()
df['Change Value'] = df['Value'].pct_change()

# Create a melted / long format DataFrame for Top Line Graph with 2 y axis
melted = df.melt(id_vars=['Dates'], value_vars=['Value', 'Sentiment', 'Rolling Sentiment'], var_name='Metric', value_name='Values')
melted = melted.sort_values('Dates')


# Function not for data collection but needed later for dropdown menu
# Gets all options in a list of dictionaries
def get_options(list_metrics):
    dict_list = []
    for i in list_metrics:
        dict_list.append({'label': i, 'value': i})

    return dict_list

# Load Dash App
app = dash.Dash()

# Create Layout for Dash App with HTML Tags and external css file
# 2 Columns, left Column: Info, control elements(DatePicker and DropDown)
app.layout = html.Div(
    className="row",
    children=[
        html.Div(
            className="three columns div-left-panel",
            children=[
                html.Div(
                    className="div-info",
                    children=[
                        html.Img(
                            className="logo", src=app.get_asset_url("bitcoin_logo.png"), style={'height':'25%', 'width':'25%', 'padding':'20%'}
                        ),
                        html.H6(className="title-header", children="""Bitcoin Overview"""),
                        html.P(
                            """
                            This app queries Bitcoin price data and a dataset of the top 100 daily posts
                            in the /r/Bitcoin subreddit. From these 100 posts a sentiment score ranging 
                            from -1 to 1 is generated.
                            """
                        )
                    ], style={'textAlign':'center'}
                ),
                dcc.DatePickerRange(
                    id='date-input',
                    min_date_allowed=start,
                    max_date_allowed=end,
                    initial_visible_month=end,
                    start_date=start,
                    end_date=end,
                    style={'padding-left':'5%', 'padding-right':'5%', 'padding-bottom':'30%', 'background-color':'#22252b',
                    'color':'#22252b'}
                ),
                html.Div(id='date-output'),
                dcc.Dropdown(
                    id='metricselector',
                    options=get_options(melted['Metric'].unique()),
                    multi=True,
                    value=melted['Metric'].sort_values()[0],
                    className='metricselector',
                    style={'width':'90%', 'padding-left':'8%', 'padding-right':'2%', 'height':'200%'}
                ),

            ], style={'height':'100vh'}
        ), 
        html.Div(
            className='nine columns div-right-panel',
            children = [
                html.Div(
                    html.H3('Bitcoin Chart')
                ),
                dcc.Graph(
                    id='timeseries',
                    animate=True, 
                    style={'height':'50vh'}
                ),
                dcc.Graph(
                    id='change',
                    animate=True, 
                    style={'height':'30vh'}
                )
            ]
        )
    ]
)


# Create Callbacks to add Interactivity

# First callback for timeseries graph
@app.callback(Output('timeseries', 'figure'), 
                [Input('date-input', 'start_date'),
                Input('date-input', 'end_date'),
                Input('metricselector' , 'value')])
def update_timeseries(start_date, end_date, selected_dropdown_value):
    """Updates the timeseries graph with chosen inputs
    Args:
        start_date: Date to start graph, from DatePickerRange
        end_date: Date to end graph, from DatePickerRange
        selected_dropdown_value: list of values selected in Dropdown
    """
    # Convert start point and endpoint to datetime format, create variables
    start_point = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_point = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    trace = []
    df_sub = melted
    # If selected metrics are 'Rolling Sentiment' or 'Sentiment' draw trace on second y-axis, else on first y-axis
    # Select data between start and end date
    for metric in selected_dropdown_value:
        if metric == 'Rolling Sentiment' or metric == 'Sentiment':
            trace.append(go.Scatter(
                x=df_sub[(df_sub['Metric'] == metric) & (df_sub['Dates'] >= start_point) & (df_sub['Dates'] <= end_point)]['Dates'],
                y=df_sub[(df_sub['Metric'] == metric) & (df_sub['Dates'] >= start_point) & (df_sub['Dates'] <= end_point)]['Values'],
                mode='lines',
                name=metric,
                textposition='bottom center',
                yaxis='y2'))
        else:
            trace.append(go.Scatter(
                x=df_sub[(df_sub['Metric'] == metric) & (df_sub['Dates'] >= start_point) & (df_sub['Dates'] <= end_point)]['Dates'],
                y=df_sub[(df_sub['Metric'] == metric) & (df_sub['Dates'] >= start_point) & (df_sub['Dates'] <= end_point)]['Values'],
                mode='lines',
                name=metric,
                textposition='bottom center',
                yaxis='y1'))

    # Flatten trace
    traces = [trace]
    data = [val for sublist in traces for val in sublist]

    # Create timerseries graph, x Axis between start and end date
    figure = {
        'data':data,
        'layout':go.Layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            plot_bgcolor='rgba(0, 0, 0, 0)',
            margin={'b': 15},
            hovermode='x',
            autosize=True,
            title={'text': 'Bitcoin Sentiment Analysis', 'font': {'color': 'white'}, 'x': 0.5},
            yaxis=dict(title='Bitcoin Price'),
            yaxis2=dict(
                title='Sentiment',
                overlaying='y',
                side='right'),
            xaxis={'range': [df_sub[df_sub['Dates'] >= start_point]['Dates'].min(), df_sub[df_sub['Dates'] <= end_point]['Dates'].max()]},
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )            
        )
    }
    return figure

@app.callback(Output('change', 'figure'), 
                [Input('date-input', 'start_date'),
                Input('date-input', 'end_date'),
                Input('metricselector' , 'value')])
def update_change(start_date, end_date, selected_dropdown_value):
    """Updates the change graph with input data
    Args:
        start_date: Date to start graph, from DatePickerRange
        end_date: Date to end graph, from DatePickerRange
        selected_dropdown_value: list of values selected in Dropdown
    """
    # Convert start point and endpoint to datetime format, create variables
    trace=[]
    df_sub=df
    start_point = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_point = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    # If selected metrics are 'Rolling Sentiment' or 'Sentiment' draw trace on second y-axis, else on first y-axis
    # Select data between start and end date
    for metric in selected_dropdown_value:
        if metric in ['Value', 'Sentiment', 'Rolling Sentiment']:
            trace.append(go.Scatter(
                x=df_sub[(df_sub['Dates'] >= start_point) & (df_sub['Dates'] <= end_point)].index,
                y=df_sub[(df_sub['Dates'] >= start_point) & (df_sub['Dates'] <= end_point)]['Change '+metric],
                mode='lines',
                name='Change '+metric,
                textposition='bottom center'))

    # Flatten trace
    traces = [trace]
    data = [val for sublist in traces for val in sublist]

    # Create change graph, x Axis between start and end date
    figure = {
        'data': data,
        'layout': go.Layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            plot_bgcolor='rgba(0, 0, 0, 0)',            
            margin = {'t': 50},
            hovermode='x',
            autosize=True,
            title={'text': 'Daily % Chg', 'font': {'color': 'white'}, 'x': 0.5},
            xaxis={'showticklabels': True, 'range': [df_sub[df_sub['Dates'] >= start_point].index.min(), df_sub[df_sub['Dates'] <= end_point].index.max()]},
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
    }
    return figure

# Run Dash App
if __name__ == '__main__':
    app.run_server(debug=True)
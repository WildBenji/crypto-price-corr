import pandas as pd
import pandas_datareader as web
import pandas_datareader.data as pdr
from scipy.stats import spearmanr, pearsonr

import datetime as dt  
from datetime import date

###################################

import plotly.express as px

###################################

from sklearn.preprocessing import minmax_scale

###################################

import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_table
import dash_bootstrap_components as dbc 
from dash.exceptions import PreventUpdate

###################################

import yfinance 

###################################


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

_crypto_dic = {
            'BTC' : 'Bitcoin', 
            'ETH' : 'Ethereum', 
            'XRP' : 'Ripple',              
            'BNB' : 'Binance Coin',
            'ADA' : 'Cardano', 
            'XLM' : 'Stellar', 
            'DOGE' : 'Dogecoin', 
            'BCH' : 'Bitcoin Cash',
            'KSM' : 'Kusuma'
            }

app.layout = html.Div(children=[

    html.H3(
        id='Main title',
        children='Historical cryptocurrencies scaled values and their correlation',
        style={'text-align':'center'}
        ),

    dcc.Markdown('''
    ###### App created by [Benjamin Baret](https://www.linkedin.com/in/benjamin-baret-6957471bb), code availabe [here]()
    ''', style={'text-align':'center'}),

    dcc.Dropdown(
    id='crypto_dropdown',
    options=[
        {'label' : b, 'value' : a } for  a, b in _crypto_dic.items()
    ],
    value='BTC',
    searchable=True,
    multi=True,
    style = {'display': True,
             'width' : '1500px',
             'margin-top': 20,
             'margin-bottom' : 20,
             'margin-left': 20,
             'margin-right' : 20
             },
    clearable=False,
    placeholder="Select Cryptocurrencies" 
    ),

    dcc.DatePickerRange(
    id='my-date-picker-range',
    min_date_allowed=dt.date(2019, 12, 12),
    max_date_allowed=dt.date.today(),
    start_date=dt.date(2019, 12, 12),
    end_date=dt.date.today(),
    with_portal=False, # met le calendrier en pleine page lorsque sélectionné
    style = {'display': True,
             'margin-top': 20,
             'margin-bottom' : 20,
             'margin-left': 40,
             'margin-right' : 20
             },
    ),

    dcc.Graph(id='graph-output'),

    html.Div(id='dropdown-selection-output'),

    dash_table.DataTable(
    id='correlation-table',
    sort_action='native',
    style_cell={'textAlign': 'center', 'width' : '50%'},
    columns=[
            {'name': 'Currency', 'id': 'Currency'}, # id correspond aux données renvoyées par corr_table 
            {'name' : 'Spearman Coefficient', 'id' : 'Spearman Coefficient'} # idem
            ]
    ),    

    ])


######################################################################################################################


@app.callback(
    [dash.dependencies.Output(component_id='graph-output', component_property='figure'), # réfère à la property "figure" de Graph
    dash.dependencies.Output(component_id='correlation-table', component_property='data')],  # réfère à la property "data" de Datatable
    [dash.dependencies.Input(component_id='crypto_dropdown', component_property='value'),
     dash.dependencies.Input(component_id='my-date-picker-range', component_property='start_date'),
     dash.dependencies.Input(component_id='my-date-picker-range', component_property='end_date')],
     prevent_initial_call=False
     )


def graph_output(_crypto, start_date, end_date):

        if _crypto is None :
            raise PreventUpdate
        else:
            pass

        start_date = pd.to_datetime(dt.datetime.strptime(start_date, '%Y-%m-%d'))
        start_date = start_date.to_pydatetime()

        end_date = pd.to_datetime(dt.datetime.strptime(end_date, '%Y-%m-%d'))
        end_date = end_date.to_pydatetime()
        
        _delta = start_date - end_date       # as timedelta

        all_data = pd.DataFrame(data={'Date' : [start_date + dt.timedelta(days=i) for i in range(_delta.days+1)]})
        all_data['Date'] = pd.to_datetime(all_data['Date'])
        all_data['Date'] = all_data['Date'].dt.date

        yfinance.pdr_override()

        print(_crypto)
        print(type(_crypto))

        if type(_crypto) != list:
            _crypto = [_crypto]
            print(type(_crypto))
        else:
            pass
        
        for _currency in _crypto:

            print(_currency)
            _trading_pair = f'{_currency}' +'-EUR'
            data = pdr.get_data_yahoo(_trading_pair, start_date, end_date)['Adj Close']
            data = pd.DataFrame(data)
            data.reset_index(inplace=True)

            # La date renvoyée est en dt.datetime et seul la date m'intéresse donc je convertis pour me débarasser de l'heure
            data['Date'] = data['Date'].dt.date
            data[f'{_currency}'] = minmax_scale(data['Adj Close'], feature_range=(0, 100))
            data.rename(columns={'Adj Close' : f'{_currency}' + '_actual'}, inplace=True)
            all_data = pd.merge(all_data, data, how='right')

        all_data.drop_duplicates(subset=['Date'], inplace=True)

        _selection = [i for i in all_data.columns if '_actual' not in i and i!='Date']

        fig = px.line(
            all_data, 
            x='Date', 
            y=_selection,
            hover_data='',
            hover_name=None,
            text=None,
            labels={'variable' : ''}  # enlève le titre des légendes
            )

        fig.update_layout(
            title=f'{", ".join(_crypto)} historical price scaled',
            xaxis_title='',
            yaxis_title='Scaled price',
            showlegend=True,
            
            )

        fig.update_traces(
            hovertemplate='<i>Value</i> : %{y:.2f} - ' + 
                          '%{x} - ' 
                          #"<b>{_traces_label}</b>", 
            )


        _base_crypto = _crypto[0]
        spearmanr_res=[]

        for i in _crypto[1:]:
        
            spearmanr_corr = spearmanr(all_data[_base_crypto], all_data[i])
            spearmanr_res.append(spearmanr_corr.correlation)

        corr_table = pd.DataFrame(data=zip( _crypto[1:], spearmanr_res),
                    columns=['Currency', 'Spearman Coefficient'])

        print(corr_table)

        return fig, corr_table.to_dict(orient='records')
        

@app.callback(
    dash.dependencies.Output('dropdown-selection-output', 'children'),
    [dash.dependencies.Input('crypto_dropdown', 'value')])

def update_text_output(value):

    return 'Correlation coefficient score to {}'.format(value[0] if type(value)==list else value)


######################################################################################################################


if __name__ == '__main__':
    app.run_server(debug=True)
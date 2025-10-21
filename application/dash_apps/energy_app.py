from application import server, db, session
from flask import g
from application.log_events import log_event
from application.models import Energy

import base64
import io
import dash
from dash import Dash, dcc, ctx, html, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import datetime
from datetime import datetime
import json
from sqlalchemy.dialects.mysql import insert

# connection = pymysql.connect(
#        host='database',
#        port=3306,
#        user='user',
#        password="password",
#        db='emc_lab_energy',
#        cursorclass=pymysql.cursors.DictCursor
#    )
#
# cursor = connection.cursor()

def fetch_energy():
    """Fetches all instruments from the 'instrument' table."""
    records = Energy.query.all()
    data = [r.__dict__ for r in records]
    for row in data:
        row.pop('_sa_instance_state', None)

    return data

# def query_dataframe(value, start, end):
#     records = Energy.query(Energy.value).filter(Energy.date > start, Energy.date < end)
#     data = [r.__dict__ for r in records]
#     for row in data:
#         row.pop('_sa_instance_state', None)
#
#     return data
#
# print(query_dataframe('consumption', datetime(2025, 1,1), datetime(2025, 10,1)))

def graph_scale_fct(scale, figure, value, df):
    df.set_index('date', inplace=True)

    if scale == 'Day':
        df_new = df.resample('D').sum()
        figure['layout']['xaxis']['tickformat'] = '%b %d, %Y'
        figure['layout']['xaxis']['dtick'] = 'D1'

    elif scale == 'Week':
        df_new = df.resample('W').sum()
        figure['layout']['xaxis']['tickformat'] = '%b %U, %Y'
        figure['layout']['xaxis']['dtick'] = 604800000

    elif scale == 'Month':
        df_new = df.resample('MS').sum()
        figure['layout']['xaxis']['tickformat']='%b, %Y'
        figure['layout']['xaxis']['dtick'] = 'M1'

    elif scale == 'Year':
        df_new = df.resample('Y').sum()
        figure['layout']['xaxis']['tickformat'] = '%Y'
        figure['layout']['xaxis']['dtick'] = 31557600000

    else:
        df_new = df
        figure['layout']['xaxis']['tickformat'] = None
        figure['layout']['xaxis']['dtick'] = None

    figure['data'][0]['x'] = df_new.index
    figure['data'][0]['y'] = df_new['consumption'] if value == 'Consumption' else df_new['price']

    return figure

def init_app(server):

    app = Dash(server=server, routes_pathname_prefix='/energy_app/', assets_folder='assets', external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=False, prevent_initial_callbacks = True)

    initial_data = fetch_energy()
    database = pd.DataFrame(initial_data)
    df = pd.DataFrame(initial_data)

    today = datetime.today()
    option = []
    month = 8
    year = 2024
    month_list = ['January', 'February', 'March', 'April', 'Mai', 'June', 'July', 'August', 'September', 'October',
                  'November', 'December']

    while year != today.year or month != today.month:
        option.append(f'{month_list[month]} {year}')

        if month == 11:
            month = 0
            year = year + 1
        else:
            month = month + 1

    month_dropdownmenu = dcc.Dropdown(options=option, value=option[-1], id='month_dropdownmenu',
                                      style={'width': '160px'}, clearable=False)
    database_info = html.Label(children='Upload new data', id='database_info',
                               style={'font-weight': 'bold', 'font-size': '18'})

    upload_month = dcc.Upload(
        id='upload_data',
        children=[
            'Drag and Drop or ',
            html.A('Select a File')
        ], style={
            'width': '500px',
            'height': '100px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin-top': '10px',
            'margin-bottom': '20px'
        })

    date_range = dbc.Stack([html.Label(children='Date range', style={'font-weight': 'bold'}),
                            dcc.DatePickerRange(id="date_range", start_date=datetime(today.year, 1, 1),
                                                end_date=today)], style={'margin-top': 10})

    date = dcc.DatePickerSingle(
        id='date_picker',
        min_date_allowed=datetime(2024, 9, 1),
        max_date_allowed=today,
        date=datetime.today(),
    )

    filtered_data = database[((database['date'] > datetime(today.year, today.month, today.day, 0, 0, 0)) & (
                database['date'] < datetime(today.year, today.month, today.day, 9, 0, 0))) | (
                                         (database['date'] > datetime(today.year, today.month, today.day, 18, 0, 0)) & (
                                             database['date'] < datetime(today.year, today.month, today.day, 23, 59,
                                                                         0)))]
    sum = filtered_data['consumption'].sum()

    energy_consumed = dbc.Stack(
        [
            date,
            html.Div(id='energy_consumed', children=f'Energy consumed out of working time: {round(sum, 1)} KWh')
        ], direction='horizontal', gap=2, style={'margin-top': 10}
    )

    graph_value = html.Div([html.Label(children='Value', style={'font-weight': 'bold'}),
                            dcc.RadioItems(id='graph_value', options=['Consumption', 'Price'], value='Consumption',
                                           inline=True, inputStyle={"margin-right": "5px"},
                                           labelStyle={"margin-right": "5px"})], style={'margin-top': 10})
    graph_scale = html.Div([html.Label(children='Scale', style={'font-weight': 'bold'}),
                            dcc.RadioItems(id='graph_scale', options=['intra-Day', 'Day', 'Week', 'Month', 'Year'],
                                           value='Month', inline=True, inputStyle={"margin-right": "5px"},
                                           labelStyle={"margin-right": "5px"})], style={'margin-top': 10})

    hovertemplate = "%{x}:<br>Consumption: %{value} KWh</br><extra></extra>"
    filtered_db = df[df['date'] > datetime(today.year, 1, 1)]

    figure = go.Figure(
        data=go.Bar(x=filtered_db['date'], y=filtered_db['consumption'], hovertemplate=hovertemplate),
        layout=go.Layout(
            title=dict(text="EMC lab energy consumption", font=dict(size=25, weight='bold')),
            barcornerradius=15,
            hovermode='closest',
            showlegend=False,
            plot_bgcolor='white',
            xaxis={'title_text': 'Date', 'title_font': dict(size=16, weight='bold'), 'tickfont': dict(size=16)},
            yaxis={'title_text': 'Consumption (kWh)', 'title_font': dict(size=16, weight='bold'),
                   'gridcolor': 'lightgrey', 'tickfont': dict(size=16), 'fixedrange': True},
            uniformtext={
                "mode": "hide",
                "minsize": 16
            },
            hoverlabel={
                'font': {
                    'size': 16,
                }},
            margin={"t": 50, "b": 0, 'r': 0, 'l': 0},
        ))

    # df_monthly_summary = summarize_data(df)

    figure = graph_scale_fct('Month', figure, 'Consumption', filtered_db)

    chart = dcc.Loading(dcc.Graph(id='chart', figure=figure,
                                  config={'toImageButtonOptions': {'filename': 'typ_graph'}, 'responsive': True,
                                          'displaylogo': False,
                                          'modeBarButtonsToRemove': ['zoom', 'pan', 'zoomin', 'zoomout', 'autoscale',
                                                                     'resetscale',
                                                                     'lasso2d', 'select2d']},
                                  style={'height': '1064px', 'width': '100%', 'fontWeight': 'bold'}
                                  ), overlay_style={"visibility": "visible", "filter": "blur(2px)"}, type="circle")

    upload_data = html.Div([database_info, upload_month, energy_consumed, graph_value, graph_scale, date_range],
                           style={'border': '5px solid #d6d6d6', 'border-radius': '10px', 'padding': '10px'})
    chart_div = html.Div([chart], style={'width': '100%'})

    app.layout = html.Div([

        html.Div(
                dbc.Stack([
                    upload_data, chart_div
                ], gap=3, direction='horizontal'),
                style={'margin-left': 20, 'margin-right': 20, 'border': '5px solid #d6d6d6', 'border-radius': '10px',
                       'padding': '20px'}), dcc.Store(id='data', data=database.to_json())
    ], style={'display': 'block', 'flexDirection': 'column', 'minHeight': '100vh', 'margin-top':'20px', 'margin-bottom':'20px'})

    app.callback(Output('energy_consumed', 'children'),
                  Input('date_picker', 'date'),
                  prevent_initial_call=True
                  )(energy_consumed_fct)

    app.callback(
        Output('chart', 'figure'),
        Output('database_info', 'children', allow_duplicate=True),
        Output('data', 'data'),
        Input('upload_data', 'contents'),
        State('upload_data', 'filename'),
        State('date_range', 'start_date'),
        State('date_range', 'end_date'),
        State('graph_value', 'value'),
        State('graph_scale', 'value'),
        State('chart', 'figure'),
        prevent_initial_call=True,
        running=[(Output("database_info", "children"), 'Uploading data', 'Upload new data')]
        )(upload_data)

    app.callback(Output('chart', 'figure', allow_duplicate=True),
                 Input('graph_value', 'value'),
                 Input('graph_scale', 'value'),
                 Input('date_range', 'start_date'),
                 Input('date_range', 'end_date'),
                 State('chart', 'figure'),
                 State('data', 'data'),
                 prevent_initial_call=True
                 )(energy_chart)

    return app.server

def energy_consumed_fct(date):

    date = datetime.fromisoformat(date)
    initial_data = fetch_energy()
    data = pd.DataFrame(initial_data)

    filtered_data = data[((data['date'] > datetime(date.year, date.month, date.day, 0, 0, 0)) & (
                data['date'] < datetime(date.year, date.month, date.day, 9, 0, 0))) | (
                                     (data['date'] > datetime(date.year, date.month, date.day, 18, 0, 0)) & (
                                         data['date'] < datetime(date.year, date.month, date.day, 23, 59, 0)))]
    sum = filtered_data['consumption'].sum()

    return f'Energy consumed out of working time: {round(sum, 1)} KWh'


def upload_data(upload_data_contents, upload_data_filename, start_date, end_date, value, scale, figure):
    if upload_data_contents is not None:
        content_type, content_string = upload_data_contents.split(',')
        decoded = base64.b64decode(content_string)

        initial_data = fetch_energy()
        data = pd.DataFrame(initial_data)

        try:
            if 'xlsx' in upload_data_filename:
                df = pd.read_excel(io.BytesIO(decoded))
            elif 'csv' in upload_data_filename:
                df = pd.read_csv(io.BytesIO(decoded))
            else:
                return no_update, 'There is an error processing this file'

            records = df.to_dict(orient='records')
            stmt = insert(Energy)
            update_dict = {c.name: stmt.inserted[c.name] for c in Energy._table_.columns if c.name != 'date'}
            stmt = stmt.on_duplicate_key_update(**update_dict)

            db.session.execute(stmt, records)
            db.session.commit()

            # df.drop(df.index[0:9], axis='index', inplace=True)
            # df.drop(df.columns[[2,3,4,6,7,8]], axis='columns', inplace=True)
            # df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], format="%d.%m.%Y %H:%M:%S", errors='coerce')
            #
            # database = data['Date']
            #
            # diff_df = df[~ df.iloc[:, 0].isin(database)].copy()
            # common_df = df[df.iloc[:, 0].isin(database)].copy()
            #
            # if not common_df.empty:
            #
            #     tuple = list(common_df.itertuples(index=False, name=None))
            #     tuple = [item_tuple + (item_dates,) for item_tuple, item_dates in zip(tuple, common_df.iloc[:, 0])]
            #     sql = "UPDATE consumption_price SET Date = %s, Consumption = %s, Price = %s WHERE Date = %s"
            #     connection.ping(reconnect=True)
            #     cursor.executemany(sql, tuple)
            #
            # if not diff_df.empty:
            #
            #     sql = "INSERT INTO consumption_price (Date, Consumption, Price) VALUES (%s, %s, %s)"
            #     connection.ping(reconnect=True)
            #     cursor.executemany(sql, list(diff_df.itertuples(index=False, name=None)))
            #     connection.commit()

        except:
            return no_update, 'There is an error processing this file'

        filtered_data = data[(data['date'] > pd.to_datetime(start_date)) & (data['date'] < pd.to_datetime(end_date))]

        figure['data'][0]['x'] = filtered_data['date']
        figure['data'][0]['y'] = filtered_data[value]

        graph_scale_fct(scale, figure, value, filtered_data)

        return figure, 'Data successfully loaded', data.to_json()

def energy_chart(value, scale, start_date, end_date, figure, data):
    trigger = ctx.triggered_id
    data = pd.read_json(data)
    data = data[(data['date'] > pd.to_datetime(start_date)) & (data['date'] < pd.to_datetime(end_date))]

    if trigger == 'graph_value':
        figure = graph_consumption_price(value, figure, data)
        figure = graph_scale_fct(scale, figure, value, data)
        return figure

    elif trigger == 'graph_scale':

        figure = graph_scale_fct(scale, figure, value, data)
        return figure

    elif trigger == 'date_range':
        figure, data = date_range_chart(figure, value, scale, data)

        return figure


def graph_consumption_price(value, figure, data):

    if value == 'Consumption':
        figure['data'][0]['y'] = data['consumption']
        figure['data'][0]['hovertemplate'] = "%{x}:<br>Consumption: %{value} KWh</br><extra></extra>"
        figure['layout']['title']['text'] = "EMC lab energy consumption"
        figure['layout']['yaxis']['title']['text'] = "Consumption (kWh)"

    elif value == 'Price':
        figure['data'][0]['y'] = data['price']
        figure['data'][0]['hovertemplate'] = "%{x}:<br>Price: %{value} €</br><extra></extra>"
        figure['layout']['title']['text'] = "EMC lab energy price"
        figure['layout']['yaxis']['title']['text'] = "Price (€)"

    return figure

def date_range_chart(figure, value, scale, data):

    value = value.lower()
    figure['data'][0]['x'] = data['date']
    figure['data'][0]['y'] = data[value]

    graph_scale_fct(scale, figure, value, data)

    return figure, data
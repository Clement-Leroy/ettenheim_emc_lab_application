import numpy as np
import csv
import pandas as pd
import os
import plotly.graph_objects as go
import webbrowser
import signal
#import threading
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from IPython.display import display, HTML
from dash import Dash, html, dcc, Input, Output, State
import base64
import io
import json

external_scripts = ["https://cdnjs.cloudflare.com/ajax/libs/jquery/1.12.1/jquery.min.js",
                    "https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js",
                    'https://trentrichardson.com/examples/timepicker/jquery-ui-timepicker-addon.js']

external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://code.jquery.com/ui/1.13.3/themes/base/jquery-ui.css']

def init_app(server):
    # Dash server
    app = Dash(__name__, server=server, routes_pathname_prefix='/motor_driver_report/', external_stylesheets=external_stylesheets, external_scripts=external_scripts)        # Dash application

    # Data cache
    _cache = {}

    # Layout with sidebar
    app.layout = html.Div([

        # Sidebar
        html.Div([
            html.H2("CSV Viewer Controls", style={"textAlign": "center", "fontSize": "14px"}),

            html.Label("Upload files"),
            dcc.Upload([dbc.Button('Upload csv files', color='secondary', outline=True)],
                id='upload', multiple=True
            ),

            html.Label("Select CSV file"),
            dcc.Dropdown(
                id='csv-file',
                options=[]
            ),

            html.Label("Select filter (1)"),
            dcc.Dropdown(
                id='filter1-sel',
                options=[],  # will be filled dynamically
                value='' # default selection
            ),

            html.Label("Select filter (2)"),
            dcc.Dropdown(
                id='filter2-sel',
                value='' # default selection
            ),

            html.Label("Select filter (3)"),
            dcc.Dropdown(
                id='filter3-sel',
                options=[],  # will be filled dynamically
                value='' # default selection
            ),

            html.Label("Select filter (4)"),
            dcc.Dropdown(
                id='filter4-sel',
                value='' # default selection
            ),

            html.Label("X-axis:"),
            dcc.Dropdown(
                id='x-col',
                options=[],  # will be filled dynamically
                value='' # default selection
            ),

            html.Label("Y-axis:"),
            dcc.Dropdown(
                id='y-col',
                options=[],  # will be filled dynamically
                value='' # default selection
            ),

            # Filter (1) control
            html.Label(id='filter1-label', children='Filter by:'),
            dcc.Dropdown(
                id='filter1-val',
                multi=True,  # allow selecting multiple values
                value=''
            ),

            # Filter (2) control
            html.Label(id='filter2-label', children='Filter by:'),
            dcc.Dropdown(
                id='filter2-val',
                multi=True,  # allow selecting multiple values
                value=''
            ),

            # Filter (3) control
            html.Label(id='filter3-label', children='Filter by:'),
            dcc.Dropdown(
                id='filter3-val',
                multi=True,  # allow selecting multiple values
                value=''
            ),

            # Filter (4) control
            html.Label(id='filter4-label', children='Filter by:'),
            dcc.Dropdown(
                id='filter4-val',
                multi=True,  # allow selecting multiple values
                value=''
            ),

            dcc.Checklist(
                id='auto-populate-filter',
                options=[
                    {'label': 'Auto populate filters', 'value': 'y'}
                ],
                value=[] # default selection
            ),

            html.Br(),
            html.Label("Display mode:"),
            dcc.RadioItems(
                id='mode',
                options=[
                    {'label': 'Lines', 'value': 'lines'},
                    {'label': 'Markers', 'value': 'markers'},
                    {'label': 'Lines+Markers', 'value': 'lines+markers'}
                ],
                value='lines+markers'
            ),

            dcc.Checklist(
                id='grid-check',
                options=[{'label': 'Show Grid', 'value': 'grid'}],
                value=['grid']
            ),

        ], style={
            "flex": "0 0 350px",
            "padding": "10px 15px",
            "background-color": "#f8f9fa",
            "fontSize": "12px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "flex-start",
            "alignItems": "stretch",
            "boxSizing": "border-box",
            "overflowY": "auto"
        }),

        # Main content
        html.Div([
            #html.H2("CSV Data Viewer", style={"textAlign": "center", "fontSize": "14px"}),
            dcc.Loading(id='loading-graph', type='circle', children=dcc.Graph(id='csv-plot', style={"flex": "1", "width": "100%", "height": "100%"}))
        ], style={
            "flex": "1",
            "padding": "10px",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "stretch",
            "justifyContent": "stretch",
            "fontSize": "12px"
        }),
        dcc.Store(id='data', data={})

    ], style={
        "display": "flex",
        "height": "1000px",
        "flexDirection": "row",
        "margin": "0",
        "padding": "0"
    })


    @app.callback(Output('csv-file', 'options'),
              Output('data', 'data'),
              Input('upload', 'contents'),
              Input('upload', 'filename'),
              State('csv-file', 'options'),
              State('data', 'data'),
              prevent_initial_call=True
              )
    def upload_data(contents, filenames, options, data):
        if contents is None:
            raise PreventUpdate

        for filename, content in zip(filenames, contents):

            if 'csv' in filename:

                content_type, content_string = content.split(',')
                decoded = base64.b64decode(content_string)

                options.append(filename)

                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

                if filename in list(data.keys()):
                    data[filename].append(df.to_json())
                else:
                    data[filename] = df.to_json()

        return options, data


    # @app.callback(
    #     Output("stop-btn", "children"),
    #     Input("stop-btn", "n_clicks")
    #     )
    # def stop_server(n_clicks):
    #     if n_clicks:
    #         os.kill(os.getpid(), signal.SIGINT)
    #         return "Stopping ..."
    #     return "Stop Server"

    @app.callback(
        [
            Output('filter1-sel', 'options'),
            Output('filter1-sel', 'value'),
            Output('filter2-sel', 'options'),
            Output('filter2-sel', 'value'),
            Output('filter3-sel', 'options'),
            Output('filter3-sel', 'value'),
            Output('filter4-sel', 'options'),
            Output('filter4-sel', 'value'),
            Output('x-col', 'options'),
            Output('x-col', 'value'),
            Output('y-col', 'options'),
            Output('y-col', 'value'),
        ],
        Input('csv-file', 'value'),
        State('data', 'data'),
        prevent_initial_call=True
    )
    def update_columns_dropdowns(selected_file, data):
        if not selected_file:
            raise PreventUpdate

        # Clear cache
        _cache.clear()

        data = pd.read_json(data[selected_file])

        # Load just the first row to get headers
        headers = list(data.columns)
        # Add empty option at the top of the list
        #options = [{"label": "", "value": ""}] + [{'label': col, 'value': col} for col in headers]
        options = [{'label': col, 'value': col} for col in headers]

        # default: pick first column for X, second column for Y (if exists)
        x_default = headers[0] if len(headers) > 0 else None
        y_default = headers[1] if len(headers) > 1 else None

        return options, x_default, options, y_default , options, [None], options, [None], options, [None], options, [None]

    # ==== Callback Filter(1) selection ===
    @app.callback(
        [
            Output('filter1-label', 'children'),
            Output('filter1-val', 'options'),
            Output('filter1-val', 'value'),
        ],
        [
            Input('filter1-sel', 'value'),
            Input('csv-file', 'value'),
            Input('auto-populate-filter', 'value')
        ],
    State('data', 'data'),
    prevent_initial_call=True
    )
    def update_filter1_label_and_values(selected_filter, selected_file, filter_autopop, data):
        label = f"Filter (1) by {selected_filter}:" if selected_filter else "Filter by:"

        # if we don't have a column or file, clear filter values
        if not selected_filter or not selected_file:
            return label, [], []

        data = pd.read_json(data[selected_file])
        try:
            # read only the column we need (fast)
            df = data[selected_filter]

            unique_vals = df.dropna().unique().tolist()
            opts = [{'label': str(v), 'value': v} for v in unique_vals]

            if 'y' in filter_autopop: return label, opts, list(unique_vals) # selects all values of the list
            else: return label, opts, [] # default no selection for multi-select, so return empty list for value
        except Exception:
            # fallback to empty if something goes wrong reading the column
            return label, [], []

    # ==== Callback Filter(2) selection ===
    @app.callback(
        [
            Output('filter2-label', 'children'),
            Output('filter2-val', 'options'),
            Output('filter2-val', 'value'),
        ],
        [
            Input('filter2-sel', 'value'),
            Input('csv-file', 'value'),
            Input('auto-populate-filter', 'value')
        ],
        State('data', 'data'),
        prevent_initial_call=True
    )
    def update_filter2_label_and_values(selected_filter, selected_file, filter_autopop, data):
        label = f"Filter (2) by {selected_filter}:" if selected_filter else "Filter by:"

        # if we don't have a column or file, clear filter values
        if not selected_filter or not selected_file:
            return label, [], []

        data = pd.read_json(data[selected_file])
        try:
            # read only the column we need (fast)
            df = data[selected_filter]

            unique_vals = df.dropna().unique().tolist()
            opts = [{'label': str(v), 'value': v} for v in unique_vals]
            if 'y' in filter_autopop: return label, opts, list(unique_vals) # selects all values of the list
            else: return label, opts, [] # default no selection for multi-select, so return empty list for value
        except Exception:
            # fallback to empty if something goes wrong reading the column
            return label, [], []

    # ==== Callback Filter(3) selection ===
    @app.callback(
        [
            Output('filter3-label', 'children'),
            Output('filter3-val', 'options'),
            Output('filter3-val', 'value'),
        ],
        [
            Input('filter3-sel', 'value'),
            Input('csv-file', 'value'),
            Input('auto-populate-filter', 'value')
        ],
        State('data', 'data'),
        prevent_initial_call=True
    )
    def update_filter3_label_and_values(selected_filter, selected_file, filter_autopop, data):
        label = f"Filter (3) by {selected_filter}:" if selected_filter else "Filter by:"

        # if we don't have a column or file, clear filter values
        if not selected_filter or not selected_file:
            return label, [], []

        pd.read_json(data[selected_file])
        try:
            # read only the column we need (fast)
            df = data[selected_filter]
            unique_vals = df[selected_filter].dropna().unique().tolist()
            opts = [{'label': str(v), 'value': v} for v in unique_vals]
            if 'y' in filter_autopop: return label, opts, list(unique_vals) # selects all values of the list
            else: return label, opts, [] # default no selection for multi-select, so return empty list for value
        except Exception:
            # fallback to empty if something goes wrong reading the column
            return label, [], []

    # ==== Callback Filter(4) selection ===
    @app.callback(
        [
            Output('filter4-label', 'children'),
            Output('filter4-val', 'options'),
            Output('filter4-val', 'value'),
        ],
        [
            Input('filter4-sel', 'value'),
            Input('csv-file', 'value'),
            Input('auto-populate-filter', 'value')
        ],
        State('data', 'data')
    )
    def update_filter4_label_and_values(selected_filter, selected_file, filter_autopop, data):
        label = f"Filter (4) by {selected_filter}:" if selected_filter else "Filter by:"

        # if we don't have a column or file, clear filter values
        if not selected_filter or not selected_file:
            return label, [], []

        pd.read_json(data[selected_file])
        try:
            # read only the column we need (fast)
            df = data[selected_filter]
            unique_vals = df[selected_filter].dropna().unique().tolist()
            opts = [{'label': str(v), 'value': v} for v in unique_vals]
            if 'y' in filter_autopop: return label, opts, list(unique_vals) # selects all values of the list
            else: return label, opts, [] # default no selection for multi-select, so return empty list for value
        except Exception:
            # fallback to empty if something goes wrong reading the column
            return label, [], []

    # === Callback with filtering ===
    @app.callback(
        Output('csv-plot', 'figure'),
        Input('csv-file', 'value'),
        Input('x-col', 'value'),
        Input('y-col', 'value'),
        Input('mode', 'value'),
        Input('grid-check', 'value'),
        Input('filter1-sel', 'options'),
        Input('filter1-sel', 'value'),
        Input('filter2-sel', 'options'),
        Input('filter2-sel', 'value'),
        Input('filter3-sel', 'options'),
        Input('filter3-sel', 'value'),
        Input('filter4-sel', 'options'),
        Input('filter4-sel', 'value'),
        Input('filter1-val', 'value'),
        Input('filter2-val', 'value'),
        Input('filter3-val', 'value'),
        Input('filter4-val', 'value'),
        State('data', 'data'),
        prevent_initial_call=True
    )
    def update_graph(csv_filename, x_colname, y_colname, display_mode, grid_opt, filter1_sel_opt, filter1_sel_val, filter2_sel_opt, filter2_sel_val, filter3_sel_opt, filter3_sel_val, filter4_sel_opt, filter4_sel_val, filter1_vals, filter2_vals, filter3_vals, filter4_vals, data):
        if csv_filename is None:
            raise PreventUpdate

        # Read data
        data = pd.read_json(data[csv_filename])
        rawData = data.to_numpy()

        # rawData  = np.genfromtxt(csv_file, delimiter=",", dtype=None, encoding='utf-8')

        #Get number of columns in .csv file
        ncols = rawData.shape[1]

        # Try to cast NumPy array elements to float or int. Fall back to string if conversion fails.
        def safe_cast(array):
            try:
                # Try float first
                return array.astype(float)
            except (ValueError, TypeError):
                try:
                    # Try int if float fails
                    return array.astype(int)
                except (ValueError, TypeError):
                    # Fallback to string
                    return array.astype(str)


        column_list = list(data.columns)

        # Mapping csv data to variables (float, int, str) - NEED TO THINK ABOUT APPROPRIATE TYPE MAPPING
        SteppedParam1 = safe_cast(rawData[1:, column_list.index(filter1_sel_val) if filter1_sel_val in column_list else -1])
        SteppedParam2 = safe_cast(rawData[1:, column_list.index(filter2_sel_val) if filter2_sel_val in column_list else -1])
        SteppedParam3 = safe_cast(rawData[1:, column_list.index(filter3_sel_val) if filter3_sel_val in column_list else -1])
        SteppedParam4 = safe_cast(rawData[1:, column_list.index(filter4_sel_val) if filter4_sel_val in column_list else -1])

        # Pick a column to filter on (change this to fit your data)
        filter_column = rawData[0][1]  # example: second column
        filter_values = np.unique(SteppedParam1)

        fig = go.Figure()

        x = rawData[1:, column_list.index(x_colname) if x_colname in column_list else -1].astype(float)
        y = rawData[1:, column_list.index(y_colname) if y_colname in column_list else -1].astype(float)

        # Retreive user-facing labels
        def get_label(options, value):
            for opt in options:
                if opt["value"] == value:
                    return opt["label"]
            return value # fallback if not found

        # Dataset filtering aimed at "set" values, not meant for "is" values. "set" values have a finite number of values.
        for value4 in (filter4_vals or [None]):       # Loops over the content of filter4_vals list or over [None]
            for value3 in (filter3_vals or [None]):   # Loops over the content of filter3_vals list or over [None]
                for value2 in (filter2_vals or [None]):  # Loops over the content of filter2_vals list or over [None]
                  for value in filter1_vals:
                      # define an appropriate mask. If the value is empty ignore it in the mask /// mask = (SteppedParam1 == value) & (SteppedParam2 == value2)
                      mask = (SteppedParam1 == value)
                      if value2: mask = mask & (SteppedParam2 == value2)
                      if value3: mask = mask & (SteppedParam3 == value3)
                      if value4: mask = mask & (SteppedParam4 == value4)

                      fig.add_trace(go.Scattergl(
                          x=x[mask],
                          y=y[mask],
                          mode=display_mode,
                          marker=dict(size=8, symbol="circle"),
                          line=dict(width=2),
                          name=f"{get_label(filter1_sel_opt, filter1_sel_val)} = {value}, {get_label(filter2_sel_opt, filter2_sel_val)} = {value2}, {get_label(filter3_sel_opt, filter3_sel_val)} = {value3}, {get_label(filter4_sel_opt, filter4_sel_val)} = {value4}"
                      ))

        # Toggle grid on/off depending on checklist state
        show_grid = 'grid' in grid_opt if grid_opt else False

        fig.update_layout(
            #title=dict(text=f"{y_colname} vs {x_colname}", x=0.5, xanchor="center"), #x-colname´, y_colname may not be specified at the beginning
            xaxis=dict(autorange=True, title=x_colname, showgrid=show_grid, gridcolor="lightgray", gridwidth=1, linecolor="black", linewidth=1, mirror=True, zeroline=True, zerolinecolor="black", zerolinewidth=1),
            yaxis=dict(autorange=True, title=y_colname, showgrid=show_grid, gridcolor="lightgray", gridwidth=1, linecolor="black", linewidth=1, mirror=True, zeroline=True, zerolinecolor="black", zerolinewidth=1),
            font=dict(family="DejaVu Sans, sans-serif", size=10, color="black"),
            plot_bgcolor='white',
            paper_bgcolor='white',
            width=1400,
            height=1000
        )

        return fig

    return app.server
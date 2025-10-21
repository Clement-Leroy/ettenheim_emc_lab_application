# dash_instruments.py
import dash
from flask import flash
import dash_ag_grid as dag
from dash import html, dcc, Input, Output, State, no_update, Dash, ctx
from dash_template_rendering import TemplateRenderer, render_dash_template_string
import dash_bootstrap_components as dbc
import pandas as pd
from application.models import Instrument
from application import server, db, session
from application.log_events import log_event

def fetch_instruments():
    """Fetches all instruments from the 'instrument' table."""
    records = Instrument.query.all()
    data = [r.__dict__ for r in records]
    for row in data:
        row.pop('_sa_instance_state', None)

    return data


def add_new_instrument_to_db(new_instrument):
    """Inserts a new instrument into the 'instrument' table."""
    instrument = Instrument(type=new_instrument['type'], brand=new_instrument['brand'], model=new_instrument['model'], ip=new_instrument['ip'], port=new_instrument['port'])
    db.session.add(instrument)
    db.session.commit()


def delete_instruments_from_db(instrument_id):
    """Deletes instruments from the 'instrument' table by ID."""
    if instrument_id:
        instrument = Instrument.query.get_or_404(instrument_id)
        db.session.delete(instrument)
        db.session.commit()


def init_app(server):
    """
    Creates and configures the Dash application to be mounted on the Flask server.
    """
    # Initial fetch of data to populate the grid
    initial_data = fetch_instruments()
    df = pd.DataFrame(initial_data)

    instrument_list = dag.AgGrid(
        id="instruments-grid",
        rowData=df.to_dict('records'),
        columnDefs=[
            {"headerName": "", "field": "edit", "sortable": False, "filter": False, 'cellRenderer': 'Button', 'width': 10},
            {"field": "id", 'hide': True},
            {"headerName": "Type", "field": "type", "sortable": True, "filter": True},
            {"headerName": "Brand", "field": "brand", "sortable": True, "filter": True},
            {"headerName": "Model", "field": "model", "sortable": True, "filter": True},
            {"headerName": "IP Address", "field": "ip", "sortable": True, "filter": True},
            {"headerName": "Port", "field": "port", "sortable": True, "filter": True},
        ],
        defaultColDef={"flex": 1, "minWidth": 100, "resizable": True},
        columnSize="sizeToFit",
        dashGridOptions={"domLayout": "autoHeight", 'rowSelection': "multiple"},
        className="ag-theme-alpine h-auto", style={'height': '100%', 'border':'0.1px solid grey'}
    )

    add = html.Div([
        html.Label('Type', style={'font-weight':'bold'}, className="form-label"),
        dcc.Input(id='new-type'),
        html.Label('Brand', style={'font-weight': 'bold'}),
        dcc.Input(id='new-brand'),
        html.Label('Model', style={'font-weight': 'bold'}),
        dcc.Input(id='new-model'),
        html.Label('IP', style={'font-weight': 'bold'}),
        dcc.Input(id='new-ip'),
        html.Label('Port', style={'font-weight': 'bold'}),
        dcc.Input(id='new-port'),
        html.Button('Save', n_clicks=0, id='save-btn', style={'background-color':'blue', 'margin-left': '20px'}),

    ], style={'padding':'20px', 'height': '100%', 'border':'0.1px solid grey'})

    edit = html.Div([
        html.Label('Type', style={'font-weight': 'bold'}, className="form-label"),
        dcc.Input(id='edit-type'),
        html.Label('Brand', style={'font-weight': 'bold'}),
        dcc.Input(id='edit-brand'),
        html.Label('Model', style={'font-weight': 'bold'}),
        dcc.Input(id='edit-model'),
        html.Label('IP', style={'font-weight': 'bold'}),
        dcc.Input(id='edit-ip'),
        html.Label('Port', style={'font-weight': 'bold'}),
        dcc.Input(id='edit-port'),
        html.Button('Cancel', n_clicks=0, id='edit-cancel-btn', style={'background-color': 'blue', 'margin-left': '20px'}),
        html.Button('Save', n_clicks=0, id='edit-save-btn', style={'background-color': 'green', 'margin-left': '20px'}),
        html.Button('Delete', n_clicks=0, id='edit-delete-btn', style={'background-color': 'red', 'margin-left': '20px'}),

    ], style={'padding': '20px', 'height': '100%', 'border':'0.1px solid grey'})

    tabs = dcc.Tabs(id="tabs", value='list', children=[
        dcc.Tab(label='List', id='list-tab', value='list', children=instrument_list, style={'display':'block'}),
        dcc.Tab(label='Edit', id='edit-tab', value='edit', children=edit, style={'display':'none'}),
        dcc.Tab(label='Add', id='add-tab', value='add', children=add, style={'display':'block'}),
    ]),


    app = Dash(server=server, url_base_pathname='/instrument/', assets_folder='assets')
    # TemplateRenderer(dash=app)

    # --- Dash Layout ---
    app.layout = html.Div(tabs, style={'height':'10vh'}), dcc.Store('instrument_id', data=None)

    # --- Callbacks for interactive functionality ---

    # @app.callback(
    #     Output("add-modal", "className"),
    #     Input("add-btn", "n_clicks"),
    #     Input("cancel-btn", "n_clicks"),
    #     State("add-modal", "className"),
    #     prevent_initial_call=True
    # )
    # def toggle_modal(n_add, n_cancel, current_class):
    #     if n_add > 0 or n_cancel > 0:
    #         if "hidden" in current_class:
    #             return current_class.replace("hidden", "flex")
    #         else:
    #             return current_class.replace("flex", "hidden")
    #     return current_class
    #
    #
    #
    #
    # @app.callback(
    #     Output("instruments-grid", "rowData", allow_duplicate=True),
    #     Output("store-data", "data", allow_duplicate=True),
    #     Input("delete-btn", "n_clicks"),
    #     State("instruments-grid", "selectedRows"),
    #     prevent_initial_call=True
    # )
    # def delete_instruments(n_clicks, selected_rows):
    #     if n_clicks > 0 and selected_rows:
    #         selected_ids = [row['id'] for row in selected_rows]
    #         delete_instruments_from_db(selected_ids)
    #         updated_data = fetch_instruments()
    #         return updated_data, updated_data
    #     return no_update, no_update

    init_callbacks(app)

    return app.server

def add_instrument(n_clicks, new_type, new_brand, new_model, new_ip, new_port):
    if n_clicks > 0 and all([new_type, new_brand, new_model, new_ip]):
        try:
            new_instrument = {
                'edit': 'Edit',
                'type': new_type,
                'brand': new_brand,
                'model': new_model,
                'ip': new_ip,
                'port': new_port
            }
            add_new_instrument_to_db(new_instrument)
            updated_data = fetch_instruments()

            log_event('Instrument add', session)

            return updated_data
        except Exception as e:
            flash("Failed to add new instrument")
            print(e)
            return no_update
    return no_update

def edit_instrument(cellRendererData, edit_cancel_btn, edit_save_btn, edit_delete_btn, rowData, id,  type, brand, model, ip, port):
    triggered_id = ctx.triggered_id

    if triggered_id == 'instruments-grid':

        instrument = rowData[cellRendererData['rowIndex']]
        id = instrument['id']
        type = instrument['type']
        brand = instrument['brand']
        model = instrument['model']
        ip = instrument['ip']
        port = instrument['port']

        tabs_value = 'edit-tab'
        list_tab_style = {'display':'none'}
        edit_tab_style = {'display': 'block'}
        add_tab_style = {'display': 'none'}

        rowData = no_update

    elif triggered_id == 'edit-cancel-btn':

        tabs_value = 'list-tab'
        list_tab_style = {'display': 'block'}
        edit_tab_style = {'display': 'none'}
        add_tab_style = {'display': 'block'}

        rowData = no_update

        type = None
        brand = None
        model = None
        ip = None
        port = None

        id = None

    elif triggered_id == 'edit-save-btn':

        log_event('Instrument edited', session)

        tabs_value = 'list-tab'
        list_tab_style = {'display': 'block'}
        edit_tab_style = {'display': 'none'}
        add_tab_style = {'display': 'block'}

        instrument = Instrument.query.filter_by(id=id).first()
        instrument.type = type
        instrument.brand = brand
        instrument.ip = ip
        instrument.port = port
        db.session.commit()

        rowData = fetch_instruments()

        type = None
        brand = None
        model = None
        ip = None
        port = None

        id = None

    elif triggered_id == 'edit-delete-btn':

        log_event('Instrument deleted', session)

        tabs_value = 'list-tab'
        list_tab_style = {'display': 'block'}
        edit_tab_style = {'display': 'none'}
        add_tab_style = {'display': 'block'}

        delete_instruments_from_db(id)
        rowData = fetch_instruments()

        type = None
        brand = None
        model = None
        ip = None
        port = None

        id = None

    print(rowData)
    return id, tabs_value, list_tab_style, edit_tab_style, add_tab_style, rowData, type, brand, model, ip, port

def init_callbacks(app):
    app.callback(
        Output("instruments-grid", "rowData"),
        Input("save-btn", "n_clicks"),
        State("new-type", "value"),
        State("new-brand", "value"),
        State("new-model", "value"),
        State("new-ip", "value"),
        State("new-port", "value"),
        prevent_initial_call=True
    )(add_instrument)

    app.callback(
        Output("instrument_id", "data"),
        Output("tabs", "value"),
        Output("list-tab", "style"),
        Output("edit-tab", "style"),
        Output("add-tab", "style"),
        Output("instruments-grid", "rowData", allow_duplicate=True),
        Output("edit-type", "value"),
        Output("edit-brand", "value"),
        Output("edit-model", "value"),
        Output("edit-ip", "value"),
        Output("edit-port", "value"),
        Input("instruments-grid", "cellRendererData"),
        Input("edit-cancel-btn", "n_clicks"),
        Input("edit-save-btn", "n_clicks"),
        Input("edit-delete-btn", "n_clicks"),
        State("instruments-grid", "rowData"),
        State("instrument_id", "data"),
        State("edit-type", "value"),
        State("edit-brand", "value"),
        State("edit-model", "value"),
        State("edit-ip", "value"),
        State("edit-port", "value"),
        prevent_initial_call=True
    )(edit_instrument)
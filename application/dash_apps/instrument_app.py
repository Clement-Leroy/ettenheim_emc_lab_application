from flask import flash
import dash
from dash import html, dcc, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
from application.models import Instrument
from application import server, db, session
from application.log_events import log_event
from dash.exceptions import PreventUpdate

from application.dash_apps.assets.layout_instrument import *

external_scripts = ["https://cdnjs.cloudflare.com/ajax/libs/jquery/1.12.1/jquery.min.js",
                    "https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js",
                    'https://trentrichardson.com/examples/timepicker/jquery-ui-timepicker-addon.js']

external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://code.jquery.com/ui/1.13.3/themes/base/jquery-ui.css', 'https://use.fontawesome.com/releases/v5.15.4/css/all.css']

def fetch_instruments():
    """Fetches all instruments from the 'instrument' table."""
    records = Instrument.query.all()
    data = [r.__dict__ for r in records]
    for row in data:
        row.pop('_sa_instance_state', None)

    return data


def add_new_instrument_to_db(new_instrument):
    """Inserts a new instrument into the 'instrument' table."""
    print(new_instrument)
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

    initial_data = fetch_instruments()

    tabs = dcc.Tabs(id="tabs", value='list', children=[
        dcc.Tab(label='List', id='list-tab', value='list', children=init_instrument_list(initial_data)),
        dcc.Tab(label='Add', id='add-tab', value='add', children=add),
        dcc.Tab(label='Edit', id='edit-tab', value='edit', disabled=True, children=edit),
    ]),

    app = dash.Dash(server=server, url_base_pathname='/instrument/', assets_folder='static', external_stylesheets=[dbc.themes.BOOTSTRAP], prevent_initial_callbacks = True)

    # --- Dash Layout ---
    app.layout = html.Div(tabs), dcc.Store('instrument_id', data=None)

    @app.callback(
        Output("instruments-grid", "rowData"),
        Output("tabs", "value", allow_duplicate=True),
        Output("list-tab", "disabled"),
        Output("edit-tab", "disabled"),
        Output("add-tab", "disabled"),
        Output("new-brand", "invalid"),
        Output("new-model", "invalid"),
        Output("new-ip", "invalid"),
        Output("new-type", "value"),
        Output("new-brand", "value"),
        Output("new-model", "value"),
        Output("new-ip", "value"),
        Output("new-port", "value"),
        # Output("modal-add-instrument", "is_open"),
        # Output("modal-body", "children"),
        Input("save-btn", "n_clicks"),
        State("new-type", "value"),
        State("new-brand", "value"),
        State("new-model", "value"),
        State("new-ip", "value"),
        State("new-port", "value"),
        prevent_initial_call=True
    )
    def add_instrument(n_clicks, new_type, new_brand, new_model, new_ip, new_port):

        rowData = tabs_value = list_tab_disabled = edit_tab_disabled = add_tab_disabled = no_update
        new_brand_invalid = new_model_invalid = new_ip_invalid = None

        if all([new_type, new_brand, new_model, new_ip]):

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
                rowData = pd.DataFrame(updated_data)
                rowData['edit'] = 'Edit'
                rowData = rowData.to_dict('records')

                log_event('Instrument added', session)

                tabs_value = 'list'
                list_tab_disabled = False
                edit_tab_disabled = True
                add_tab_disabled = False

                new_type = 'Power Supply'
                new_brand = new_model = new_ip = new_port = None

                # modal_is_open = True
                # modal_body_children = 'The new instrument has been successfully added !'

            except Exception as e:
                # modal_is_open = True
                # modal_body_children = 'The new instrument failed to be added !'
                raise PreventUpdate

        else:

            if new_brand is None:
                new_brand_invalid = True
            else:
                new_brand_invalid = None

            if new_model is None:
                new_model_invalid = True
            else:
                new_brand_invalid = None

            if new_ip is None:
                new_ip_invalid = True
            else:
                new_brand_invalid = None

        return rowData, tabs_value, list_tab_disabled, edit_tab_disabled, add_tab_disabled, new_brand_invalid, new_model_invalid, new_ip_invalid, new_type, new_brand, new_model, new_ip, new_port

    @app.callback(
        Output("instrument_id", "data"),
        Output("tabs", "value", allow_duplicate=True),
        Output("list-tab", "disabled", allow_duplicate=True),
        Output("edit-tab", "disabled", allow_duplicate=True),
        Output("add-tab", "disabled", allow_duplicate=True),
        Output("instruments-grid", "rowData", allow_duplicate=True),
        Output("edit-type", "value", allow_duplicate=True),
        Output("edit-brand", "value", allow_duplicate=True),
        Output("edit-model", "value", allow_duplicate=True),
        Output("edit-ip", "value", allow_duplicate=True),
        Output("edit-port", "value", allow_duplicate=True),
        Output("edit-brand", "invalid"),
        Output("edit-model", "invalid"),
        Output("edit-ip", "invalid"),
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
    )
    def edit_instrument(cellRendererData, edit_cancel_btn, edit_save_btn, edit_delete_btn, rowData, id, type, brand, model, ip, port):
        triggered_id = ctx.triggered_id

        edit_brand_invalid = edit_model_invalid = edit_ip_invalid = None

        if triggered_id == 'instruments-grid' and cellRendererData:

            instrument = rowData[cellRendererData['rowIndex']]
            id = instrument['id']
            type = instrument['type']
            brand = instrument['brand']
            model = instrument['model']
            ip = instrument['ip']
            port = instrument['port']

            tabs_value = 'edit'
            list_tab_disabled = True
            edit_tab_disabled = False
            add_tab_disabled = True

            rowData = no_update

        elif triggered_id == 'edit-cancel-btn':

            tabs_value = 'list'
            list_tab_disabled = False
            edit_tab_disabled = True
            add_tab_disabled = False

            type = brand = model = ip = port = id = no_update

            rowData = no_update


        elif triggered_id == 'edit-save-btn':
            print(model)

            if all([brand, model, ip]):

                try:

                    tabs_value = 'list'
                    list_tab_disabled = False
                    edit_tab_disabled = True
                    add_tab_disabled = False

                    instrument = Instrument.query.filter_by(id=id).first()
                    instrument.type = type
                    instrument.brand = brand
                    instrument.ip = ip
                    instrument.port = port
                    db.session.commit()

                    rowData = fetch_instruments()
                    rowData = pd.DataFrame(rowData)
                    rowData['edit'] = 'Edit'
                    rowData = rowData.to_dict('records')

                    log_event('Instrument edited', session)

                except Exception as e:
                    # modal_is_open = True
                    # modal_body_children = 'The new instrument failed to be added !'
                    raise PreventUpdate

            else:
                print(model)
                if model == '':
                    print('yes')
                tabs_value = list_tab_disabled = edit_tab_disabled = add_tab_disabled = no_update

                if brand == '':
                    edit_brand_invalid = True
                else:
                    edit_brand_invalid = None

                if model == '':
                    edit_model_invalid = True
                    print(edit_model_invalid)
                else:
                    edit_model_invalid = None

                if ip == '':
                    edit_ip_invalid = True
                else:
                    edit_ip_invalid = None

        elif triggered_id == 'edit-delete-btn':

            try:

                tabs_value = 'list'
                list_tab_disabled = False
                edit_tab_disabled = True
                add_tab_disabled = False

                delete_instruments_from_db(id)
                rowData = fetch_instruments()
                rowData = pd.DataFrame(rowData)
                rowData['edit'] = 'Edit'
                rowData = rowData.to_dict('records')

                type = brand = model = ip = port = id = no_update

                log_event('Instrument deleted', session)

            except:
                # modal_is_open = True
                # modal_body_children = 'The new instrument failed to be added !'
                raise PreventUpdate

        else:
            raise PreventUpdate

        return id, tabs_value, list_tab_disabled, edit_tab_disabled, add_tab_disabled, rowData, type, brand, model, ip, port, edit_brand_invalid, edit_model_invalid, edit_ip_invalid

    return app.server

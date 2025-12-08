import dash_ag_grid as dag
from dash import html, dcc, Input, Output, State, no_update, Dash, ctx
import pandas as pd
import dash_bootstrap_components as dbc

columnDefs=[
            {"headerName": "", "field": "edit", "cellRenderer": "Button", "sortable": False, "filter": False, 'width': 60, 'pinned': 'left', 'cellStyle': {'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'}, "cellRendererParams": {'className': "block text-center text-md text-white rounded no-underline cursor-pointer hover:bg-blue-600", }},
            {"field": "id", "hide": True},
            {"headerName": "Type", "field": "type", "sortable": True, "filter": True},
            {"headerName": "Brand", "field": "brand", "sortable": True, "filter": True},
            {"headerName": "Model", "field": "model", "sortable": True, "filter": True},
            {"headerName": "IP Address", "field": "ip", "sortable": True, "filter": True},
            {"headerName": "Port", "field": "port", "sortable": True, "filter": True},
        ]

def init_instrument_list(initial_data):

    df = pd.DataFrame(initial_data)
    df['edit'] = 'Edit'

    instrument_list = dag.AgGrid(
        id="instruments-grid",
        rowData=df.to_dict('records'),
        columnDefs=columnDefs,
        defaultColDef={"flex": 1, "resizable": True},
        columnSize="sizeToFit",
        dashGridOptions={"domLayout": "autoHeight", 'rowSelection': "multiple"},
        className="ag-theme-alpine h-auto", style={'height': '100%', 'border': '0.1px solid grey'}
    )

    return instrument_list

new_type = dbc.Row(
    [
        dbc.Label("Type", html_for="new-type", width=1, style={'font-weight': 'bold'}),
        dbc.Col(
            dbc.Select(id="new-type", placeholder="Enter type", value='Power Supply', options=['Power Supply', 'Electronic Load', 'Multimeter', 'Data logger', 'Climatic chamber']),
            width=11,
        ),
    ],
    className="mb-3",
)

new_brand = dbc.Row(
    [
        dbc.Label("Brand", html_for="new-brand", width=1, style={'font-weight': 'bold'}),
        dbc.Col(
            dbc.Input(type="text", id="new-brand", placeholder="Enter brand"),
            width=11,
        ),
    ],
    className="mb-3",
)

new_model = dbc.Row(
    [
        dbc.Label("Model", html_for="new-model", width=1, style={'font-weight': 'bold'}),
        dbc.Col(
            dbc.Input(type="text", id="new-model", placeholder="Enter model"),
            width=11,
        ),
    ],
    className="mb-3",
)

new_ip = dbc.Row(
    [
        dbc.Label("IP address", html_for="new-ip", width=1, style={'font-weight': 'bold'}),
        dbc.Col(
            dbc.Input(type="text", id="new-ip", placeholder="Enter IP address"),
            width=11,
        ),
    ],
    className="mb-3",
)

new_port = dbc.Row(
    [
        dbc.Label("Port", html_for="new-port", width=1, style={'font-weight': 'bold'}),
        dbc.Col(
            dbc.Input(type="number", id="new-port", placeholder="Enter port (optional)"),
            width=11,
        ),
    ],
    className="mb-3",
)

new_btn = html.Div(
    [
        dbc.Button('Submit', n_clicks=0, id='save-btn', color='success', className="me-1")
    ],
    style={'margin-top':'20px', 'margin-left':'20px'}
)

add = dbc.Form([new_type, new_brand, new_model, new_ip, new_port, new_btn], style={'padding':'20px', 'height': '100%', 'border':'0.1px solid grey'})


edit_type = dbc.Row(
    [
        dbc.Label("Type", html_for="edit-type", width=1, style={'font-weight': 'bold'}),
        dbc.Col(
            dbc.Select(id="edit-type", placeholder="Enter type", value='Power Supply', options=['Power Supply', 'Electronic Load', 'Multimeter', 'Data logger', 'Climatic chamber']),
            width=11,
        ),
    ],
    className="mb-3",
)

edit_brand = dbc.Row(
    [
        dbc.Label("Brand", html_for="edit-brand", width=1, style={'font-weight': 'bold'}),
        dbc.Col(
            dbc.Input(type="text", id="edit-brand", placeholder="Enter brand"),
            width=11,
        ),
    ],
    className="mb-3",
)

edit_model = dbc.Row(
    [
        dbc.Label("Model", html_for="edit-model", width=1, style={'font-weight': 'bold'}),
        dbc.Col(
            dbc.Input(type="text", id="edit-model", placeholder="Enter model"),
            width=11,
        ),
    ],
    className="mb-3",
)

edit_ip = dbc.Row(
    [
        dbc.Label("IP address", html_for="edit-ip", width=1, style={'font-weight': 'bold'}),
        dbc.Col(
            dbc.Input(type="text", id="edit-ip", placeholder="Enter IP address"),
            width=11,
        ),
    ],
    className="mb-3",
)

edit_port = dbc.Row(
    [
        dbc.Label("Port", html_for="edit-port", width=1, style={'font-weight': 'bold'}),
        dbc.Col(
            dbc.Input(type="number", id="edit-port", placeholder="Enter port (optional)"),
            width=11,
        ),
    ],
    className="mb-3",
)

new_btn = html.Div(
    [
        dbc.Stack(
            [
                dbc.Button('Cancel', n_clicks=0, id='edit-cancel-btn', className='btn btn-primary'),
                dbc.Button('Submit', n_clicks=0, id='edit-save-btn', className='btn btn-success'),
                dbc.Button('Delete', n_clicks=0, id='edit-delete-btn', className='btn btn-danger'),
            ], direction='horizontal', gap=3)
    ],
    style={'margin-top':'20px', 'margin-left':'20px'}
)

edit = dbc.Form([edit_type, edit_brand, edit_model, edit_ip, edit_port, new_btn], style={'padding':'20px', 'height': '100%', 'border':'0.1px solid grey'})

# edit = html.Div([
#     html.Label('Type', style={'font-weight': 'bold'}, className="form-label"),
#     dcc.Input(id='edit-type'),
#     html.Label('Brand', style={'font-weight': 'bold'}),
#     dcc.Input(id='edit-brand'),
#     html.Label('Model', style={'font-weight': 'bold'}),
#     dcc.Input(id='edit-model'),
#     html.Label('IP', style={'font-weight': 'bold'}),
#     dcc.Input(id='edit-ip'),
#     html.Label('Port', style={'font-weight': 'bold'}),
#     dcc.Input(id='edit-port'),
#     html.Button('Cancel', n_clicks=0, id='edit-cancel-btn', className='btn btn-primary'),
#     html.Button('Submit', n_clicks=0, id='edit-save-btn', className='btn btn-success'),
#     html.Button('Delete', n_clicks=0, id='edit-delete-btn', className='btn btn-danger'),
#     ], style={'padding': '20px', 'height': '100%', 'border':'0.1px solid grey'})

# modal = dbc.Modal(
#             [
#                 dbc.ModalHeader(dbc.ModalTitle("Instrument"), close_button=True),
#                 dbc.ModalBody(
#                     id='modal-body',
#                     children="The new instrument has been successfully added !"
#                 ),
#                 dbc.ModalFooter(
#                     dbc.Button(
#                         "Close",
#                         id="close-backdrop",
#                         className="ms-auto",
#                         n_clicks=0,
#                     )
#                 ),
#             ],
#             id="modal-add-instrument",
#             is_open=False,
#         ),
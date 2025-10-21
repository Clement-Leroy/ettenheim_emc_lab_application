from dash import dcc, ctx, html, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import base64
import datetime
from datetime import date
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import math

from application.dash_apps.emc_projects_dashboard import read_database

cellStyle =  {
    "styleConditions": [
        {
            "condition": "params.value === 'Upcoming'",
            "style": {"backgroundColor": "LightSkyBlue"},
        },
        {
            "condition": "params.value === 'Ongoing'",
            "style": {"backgroundColor": "Gold"},
        },
        {
            "condition": "params.value === 'Completed'",
            "style": {"backgroundColor": "mediumaquamarine"},
        },
        {
            "condition": "params.value === 'Canceled'",
            "style": {"backgroundColor": "lightcoral"},
        },
    ]
}

columnDefs_project_list=[
    {"headerName": "",
     "field": "Show",
     "cellRenderer": "Button",
     "cellRendererParams": {'className': "block text-center text-md text-white rounded no-underline cursor-pointer hover:bg-blue-600"},
     'width': 70, 'pinned': 'left',
     'cellStyle': {'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'}, 'sortable': False},
    {"headerName":"Start Date","field": "Start Date", 'flex':1, 'filter': 'agDateColumnFilter', "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals", "Before","After","Between"], "debounceMs": 500}},
    {"headerName":"End Date","field": "End Date", 'flex':1, 'filter': 'agDateColumnFilter', "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals", "Before","After","Between"], "debounceMs": 500}},
    {"headerName":"Location","field": "Location", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Number","field": "Number", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Project","field": "Project", 'width':350, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Project ID","field": "Project ID", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"PM","field": "PM", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Category","field": "Category", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Type","field": "Typ", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Client","field": "Client", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"PL","field": "PL", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Hours","field": "Work [hours]", 'flex':1, "filter": "agNumberColumnFilter", "filterParams": {"filterOptions": ["Equals", "Does not equals", "Greater than", "Less than", "Between"], "debounceMs": 500}},
    {"headerName":"Status","field": "Status", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}, "cellStyle": cellStyle},
    ]

columnDefs_project = [
    {"headerName":"", "checkboxSelection": True, 'width': 45, 'pinned': 'left', 'sortable': False},
    {"headerName":"Test Service","field": "Test_Service", 'flex':1, "editable": True, "cellEditor": "agSelectCellEditor", "cellEditorParams": {"values": ["EMC-BCI", "EMC-CE", "EMC-CI", "EMC-DOC", "EMC-ESD", "EMC-IC1", "EMC-IC2", "EMC-RE1", "EMC-RE2", "EMC-RI", "EMC-SET", "EMC-SW", "EMC-PRO"]}},
    {"headerName":"Tester","field": "Tester", 'flex':1, "editable": True, "cellEditor": "agSelectCellEditor", "cellEditorParams": {"values": ["Jan", "Philipp", "Rolf", "Lukas", "Clement", 'Anita']}},
    {"headerName":"Location","field": "Location", 'flex':1, "editable": True, "cellEditor": "agSelectCellEditor", "cellEditorParams": {"values": ["ALSE", "SAC 3", "SK", "Pulses", "ESD", "Office"]}},
    {"headerName":"Start Date","field": "Start_Date", 'flex':1, "editable": True, "cellEditor": "agDateStringCellEditor"},
    {"headerName":"Stop Date","field": "Stop_Date", 'flex':1, "editable": True, "cellEditor": "agDateStringCellEditor"},
    {"headerName":"Hours","field": "Hours", 'flex':1, "editable": True, "cellDataType": 'number'},
    {"headerName":"Status","field": "Status", 'flex':1, "editable": False}
]

project_table = html.Div(dag.AgGrid(
            id="project_table",
            columnDefs=columnDefs_project,
            rowData=[],
            defaultColDef={"cellDataType": False},
            dashGridOptions = {'singleClickEdit':True, 'suppressRowTransform': True, "rowSelection": "multiple"},
            style = {'margin-bottom':10}
        ))

check = html.Img(src="https://cdn-icons-png.flaticon.com/512/5610/5610944.png",style={'height': '20px','width':'20px'})
cross = html.Img(src="https://cdn-icons-png.flaticon.com/512/10100/10100000.png",style={'height': '20px','width':'20px'})

USERNAME_PASSWORD_PAIRS = [['username','password']]

external_scripts = ["https://cdnjs.cloudflare.com/ajax/libs/jquery/1.12.1/jquery.min.js",
                    "https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js",
                    'https://trentrichardson.com/examples/timepicker/jquery-ui-timepicker-addon.js']

external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://code.jquery.com/ui/1.13.3/themes/base/jquery-ui.css']

project_list_btn=dbc.Stack([
                html.Div(html.Button('Add project',id='add_project',n_clicks=0,style={'width':'150px','borderRadius':'5px'})),
                html.Div(html.Button('Save backup',id='save_backup',n_clicks=0,style={'width':'150px','borderRadius':'5px'})),
                dcc.Download(id="download_backup"),
                dcc.Upload(id='upload-backup', children=html.Div(html.Button('Load backup',id='load_backup',n_clicks=0,style={'width':'150px','borderRadius':'5px'}))),
                html.Div(dbc.Button(id='loading-screen', children=['No action selected'],disabled=True, style = {'width':'270px', 'borderRadius':'5px', 'border':'none','align-items':'center', 'font-weight':'bold', 'backgroundColor':'#119DFF'})),
            ],direction="horizontal",gap=3,style={'margin-left':'30px','margin-bottom':'20px','align-items':'center'})


start_date_input = html.Div(dbc.Stack([html.Label('Start Date', style={'fontWeight':'bold'}), dcc.DatePickerSingle(id="start_date_input",style={'width':150})]))
stop_date_input = html.Div(dbc.Stack([html.Label('Stop Date', style={'fontWeight':'bold'}), dcc.DatePickerSingle(id="stop_date_input",style={'width':150})]))
project_input = html.Div(dbc.Stack([html.Label('Project', style={'fontWeight':'bold'}), dcc.Input(id="project_input", value='', style={'width':150, "height": 35})]))
project_ID = html.Div(dbc.Stack([html.Label('Project ID', style={'fontWeight':'bold'}), dcc.Input(id="project_id_input", value='', style={'width':150, "height": 35})]))
location_input = html.Div(dbc.Stack([html.Label('Location', style={'fontWeight':'bold'}), dcc.Input(id="location_input",style={'width':150, "height": 35})]))
project_manager_input = html.Div(dbc.Stack([html.Label('Project manager', style={'fontWeight':'bold'}), dcc.Dropdown(['JS','PS','RG','LK','CL', 'AJ'],id="project_manager_input", clearable=False,style={'width':150, "height": 35})]))
category_input = html.Div(dbc.Stack([html.Label('Category', style={'fontWeight':'bold'}), dcc.Dropdown(['Internal', 'External'],id="category_input",style={'width':150, "height": 35})]))
type_input = html.Div(dbc.Stack([html.Label('Type', style={'fontWeight':'bold'}), dcc.Dropdown(['Paid','Non Paid'],id="type_input",style={'width':150, "height": 35})]))
client_input = html.Div(dbc.Stack([html.Label('Client', style={'fontWeight':'bold'}), dcc.Dropdown(['EXT','FAE / Sales', 'AE / PL'],id="client_input",style={'width':150, "height": 35})]))
PL_input = html.Div(dbc.Stack([html.Label('PL', style={'fontWeight':'bold'}), dcc.Dropdown(['C1 AC/DC - Lighting', 'E1 ADC', 'N1 Analog', 'A1 Automotive', 'R1 Other', 'I1 Power Magnetics', 'S1 Sensor', 'D1 STD DC/DC','K1 Telecom + Computing','B1 Automotive BMS','X1 Axign'],id="PL_input",style={'width':220, "height": 35})]))
contact_input = html.Div(dbc.Stack([html.Label('Contact', style={'fontWeight':'bold'}), dcc.Input(id="contact_input",style={'width':250, "height": 35})]))
quote_input = html.Div(dbc.Stack([html.Label('Quote', style={'fontWeight':'bold'}), dcc.Input(id="quote_input", readOnly=True,style={'width':150, "height": 35})]))
quote2_input = html.Div(dbc.Stack([html.Label('Quote2', style={'fontWeight':'bold'}), dcc.Input(id="Quote2",style={'width':150, "height": 35})]))
PO_input = html.Div(dbc.Stack([html.Label('PO', style={'fontWeight':'bold'}), dcc.Input(id="PO_input",style={'width':150, "height": 35})]))
draft_input = html.Div(dbc.Stack([html.Label('Draft', style={'fontWeight':'bold'}), dcc.Input(id="draft_input",style={'width':150, "height": 35})]))
report_input = html.Div(dbc.Stack([html.Label('Report', style={'fontWeight':'bold'}), dcc.Input(id="report_input",style={'width':150, "height": 35})]))
time_input = html.Div(dbc.Stack([html.Label('Time[H]', style={'fontWeight':'bold', 'margin-right':5}), dcc.Input(id="time_input", type='number', readOnly=True, style={'width':60, "height": 35, 'text-align': 'center'})], direction= 'horizontal', style={'margin-left': 320}))
invoice_input = html.Div(dbc.Stack([html.Label('Invoice', style={'fontWeight':'bold'}), dcc.Input(id="invoice_input",style={'width':150, "height": 35})]))
status_input = html.Div(dbc.Stack([html.Label('Status', style={'fontWeight':'bold'}), dcc.Dropdown(['Upcoming', 'Ongoing', 'Completed', 'Canceled'],clearable=False, value='Ongoing', id="status_input",style={'width':150, "height": 35})]))

ok_project_btn = html.Div(html.Button('OK', id='ok_project_btn', n_clicks=0, style={'width':100}))
cancel_btn = html.Div(html.Button('Cancel', id='cancel_btn', n_clicks=0, style={'width':100}))

project_window = html.Div([
                                html.Div(html.Label('Add new project', style={'fontWeight':'bold', 'fontSize':20, 'margin-left':10})),
                                dbc.Stack([project_input, project_ID, location_input, project_manager_input, start_date_input, stop_date_input], direction='horizontal',gap=3, style={'margin-bottom':10}),
                                dbc.Stack([category_input, type_input, client_input, PL_input, status_input], direction='horizontal',gap=3, style={'margin-bottom':10}),
                                dbc.Stack([ok_project_btn, cancel_btn], direction='horizontal',gap=1)],
                                id='project_window',style={'height':360,'width':1000,'display':'none','position':'fixed','top':'40%','left':'35%','backgroundColor':"#e0e0e0",'padding':'10px 10px','boxShadow':'0px 4px 8px rgba(0,0,0,0.1)','zIndex':'2002','borderRadius':'8px','overflow':'auto'})

yes_remove_btn = html.Div(html.Button('Confirm', id='yes_remove_btn', n_clicks=0, style={'width':90}))
no_remove_btn =  html.Div(html.Button('Cancel', id='no_remove_btn', n_clicks=0, style={'width':90}))

encoded_image = base64.b64encode(open("assets/warning.png", 'rb').read())

remove_window = html.Div([
    dbc.Row([
    dbc.Col(html.Div(html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()), style={'width':100})), width='auto'),
    dbc.Col([
            html.Label('Are you sure to remove definitively this project ?', style={'fontWeight':'bold', 'margin-bottom':5}),
            dbc.Stack([yes_remove_btn, no_remove_btn], direction='horizontal',gap=2)], align='center', width='auto'),
    ])
    ], id='remove_window',style={'display':'none','position':'fixed','top':'60%','left':'40%','backgroundColor':"#e0e0e0",'padding':'10px 10px','boxShadow':'0px 4px 8px rgba(0,0,0,0.1)','zIndex':'2003','borderRadius':'8px'})


project_description_label = html.Label(id='project_description_label', style={'fontWeight':'bold', 'fontSize':20})
add_test_service_btn = html.Button('+ Add Test Service', id='add_test_service_btn', n_clicks=0,style={'width':170, 'margin-right': 10})
remove_test_service_btn = html.Button('- Remove Test Service', id='remove_test_service_btn', n_clicks=0,style={'width':170})

project_input = html.Div(dbc.Stack([html.Label('Project', style={'fontWeight':'bold'}), dcc.Input(id="project_description_input",style={'width':150, "height": 35})]))
project_ID = html.Div(dbc.Stack([html.Label('Project ID', style={'fontWeight':'bold'}), dcc.Input(id="project_id_description_input", value='', style={'width':150, "height": 35})]))
location_input = html.Div(dbc.Stack([html.Label('Location', style={'fontWeight':'bold'}), dcc.Input(id="location_description_input",style={'width':150, "height": 35})]))
project_manager_input = html.Div(dbc.Stack([html.Label('Project manager', style={'fontWeight':'bold'}), dcc.Dropdown(['JS','PS','RG','LK','CL', 'AJ'],id="project_manager_description_input", clearable=False, style={'width':150})]))
category_input = html.Div(dbc.Stack([html.Label('Category', style={'fontWeight':'bold'}), dcc.Dropdown(['Internal', 'External'],id="category_description_input",style={'width':150})]))
type_input = html.Div(dbc.Stack([html.Label('Type', style={'fontWeight':'bold'}), dcc.Dropdown(['Paid','Non Paid'],id="type_description_input",style={'width':150})]))
client_input = html.Div(dbc.Stack([html.Label('Client', style={'fontWeight':'bold'}), dcc.Dropdown(['EXT','FAE / Sales', 'AE / PL'],id="client_description_input",style={'width':150})]))
PL_input = html.Div(dbc.Stack([html.Label('PL', style={'fontWeight':'bold'}), dcc.Dropdown(['C1 AC/DC - Lighting', 'E1 ADC', 'N1 Analog', 'A1 Automotive', 'R1 Other', 'I1 Power Magnetics', 'S1 Sensor', 'D1 STD DC/DC','K1 Telecom + Computing','B1 Automotive BMS','X1 Axign'],id="PL_description_input",style={'width':220})]))
status_input = html.Div(dbc.Stack([html.Label('Status', style={'fontWeight':'bold'}), dcc.Dropdown(['Upcoming', 'Ongoing', 'Completed', 'Canceled'],clearable=False,id="status_description_input",style={'width':150, "height": 35})]))

start_date_input = html.Div(dbc.Stack([html.Label('Start Date', style={'fontWeight':'bold'}), dcc.DatePickerSingle(id="start_date_description_input",style={'width':150})]))
stop_date_input = html.Div(dbc.Stack([html.Label('Stop Date', style={'fontWeight':'bold'}), dcc.DatePickerSingle(id="stop_date_description_input",style={'width':150})]))

ok_project_description_btn = html.Button('Update', id='close_project_description_btn', n_clicks=0,style={'width':150,'borderRadius':'5px', 'margin-right': 10})
cancel_project_description_btn = html.Div(html.Button('Cancel',id='cancel_project_description_btn',n_clicks=0,style={'width':'150px','borderRadius':'5px', 'margin-right': 10}))
remove_project_btn = html.Div(html.Button('Remove project',id='remove_project',n_clicks=0,style={'width':'150px','borderRadius':'5px'}))

project_description = html.Div([
                    dbc.Stack([project_description_label], direction='horizontal', style={'margin-bottom':10, 'margin-left':10}),
                    dbc.Stack([project_input, project_ID, location_input, project_manager_input, start_date_input, stop_date_input], direction='horizontal',gap=3, style={'margin-bottom':10}),
                    dbc.Stack([category_input, type_input, client_input, PO_input, PL_input, status_input], direction='horizontal',gap=3, style={'margin-bottom':10}),
                    dbc.Stack([quote_input, quote2_input, draft_input,report_input, invoice_input, contact_input], direction='horizontal',gap=3, style={'margin-bottom':10}),
                    dbc.Stack([add_test_service_btn, remove_test_service_btn], direction='horizontal'),
                    project_table,
                    dbc.Stack([ok_project_description_btn, cancel_project_description_btn, remove_project_btn, time_input], direction='horizontal',gap=1),
                                ],
                              id='project_description', style={'width':1100,'display':'none','position':'fixed','top':'25%','left':'30%','backgroundColor':"#e0e0e0",'padding':'10px 10px','boxShadow':'0px 4px 8px rgba(0,0,0,0.1)','zIndex':'2002','borderRadius':'8px','overflow':'auto'}
)

def lab_member_list_fct(project_data):
    project_data = project_data.to_dict('records')
    lab_member_list = {}
    for project in project_data:
        PM = project['PM']
        if PM not in list(lab_member_list.keys()):
            lab_member_list[PM] = [project]
        else:
            lab_member_list[PM].append(project)
    return lab_member_list

def create_project_timeline(lab_member_list):
    project_timeline_data_list = []
    row = 0
    ticktext = []
    tickvals = []
    for member, projects in lab_member_list.items():
        ticktext.append(member)
        val = ((len(projects)*0.1 + row) - row)/2 + row
        tickvals.append(val)

        for project in projects:
            if project['PM'] is not None:
                current_date = datetime.date.today()
                start = pd.to_datetime(project['Start Date'], format='%Y-%m-%d').date()
                end = pd.to_datetime(project['End Date'], format='%Y-%m-%d').date()
                if start == end:
                    end = end + datetime.timedelta(days=1)

                if start <= current_date <= end:
                    status = 'in progress'
                elif start < current_date:
                    status = 'completed'
                else:
                    status = 'upcoming'

                project_timeline_data = {
                    "Task": member,
                    "Start": start,
                    "Finish": end,
                    "Project": project["Project"],
                    "Status": status,
                    "Row": row
                }
                project_timeline_data_list.append(project_timeline_data)

                row = row + 0.1

        row = row + 0.1

    project_timeline_data_list = pd.DataFrame(project_timeline_data_list)
    project_timeline_figure = px.timeline(project_timeline_data_list, x_start='Start', x_end="Finish", y='Row',
                                          text='Project', color="Status", color_discrete_map=color_map, custom_data=[project_timeline_data_list['Start'].apply(lambda x: x.strftime("%B %d, %Y")), project_timeline_data_list['Finish'].apply(lambda x: x.strftime("%B %d, %Y")), project_timeline_data_list['Task'], project_timeline_data_list['Status']])

    project_timeline_figure.update_traces(width=0.09, marker=dict(cornerradius=30), insidetextanchor="middle", insidetextfont=dict(weight="bold"),
        hovertemplate="<b>Project: %{text}<br>PM: %{customdata[2]}<br>Status: %{customdata[3]}<br>Start Date: %{customdata[0]}<br>Stop Date: %{customdata[1]}<extra></extra>"
    )
    project_timeline_figure.update_yaxes(tickvals=tickvals, ticktext=ticktext)
    project_timeline_figure.update_layout(plot_bgcolor='white', title=dict(text="Personnel Timeline", font=dict(size=25, weight='bold'), xanchor="left", x=0.44), margin={'t':50,'b':0,'r':0,'l':0}, xaxis_title='', yaxis_title='', showlegend=False, xaxis={'tickfont': dict(size=16), 'range': [date(date.today().year,1,1), date(date.today().year+1, 1, 1),]}, yaxis={'fixedrange': True, 'tickfont':dict(size=16), 'range': [-0.1, project_timeline_data_list.iloc[-1]['Row'] + 0.1]})

    project_timeline_figure.add_trace(go.Scatter(
        x=[datetime.date.today(), datetime.date.today(), datetime.date.today() + datetime.timedelta(days=1),
           datetime.date.today() + datetime.timedelta(days=1)],
        y=[-0.1, project_timeline_data_list.iloc[-1]['Row'] + 0.1, project_timeline_data_list.iloc[-1]['Row'] + 0.1, -0.1],
        name='<b>Current Date</b>', showlegend=False,
        visible=True, fill="toself",
        mode='text', fillcolor='blue', opacity=0.3, hoverinfo='text'))

    return project_timeline_figure

color_map = {
    "completed": "green",
    "in progress": "yellow",
    "upcoming": "blue"
}

start_stop_date_timeline_input = html.Div([html.Label('Start → End Dates', style={'fontWeight':'bold'}),
                                    dcc.DatePickerRange(
                                    id='start_stop_date_timeline_input',
                                    start_date=date(date.today().year,1,1),
                                    end_date=date(date.today().year+1, 1, 1),
                                    style={'width':287}
                                    )])

timeline_checklist = html.Div([
    html.Label('Personnel List', style={'fontWeight':'bold', 'margin-left':'15px'}),
    dcc.Checklist(
        ['Philipp Schroer', 'Rolf Giessler', 'Jan Spindler', 'Clement Leroy', 'Lukas Kurz', 'Anita Joseph'],
        ['Philipp Schroer', 'Rolf Giessler', 'Jan Spindler', 'Clement Leroy', 'Lukas Kurz', 'Anita Joseph'],
        id='timeline_checklist',
        inputStyle={"margin-right": "10px", "margin-bottom": "10px"}
    )])

timeline_parameters = html.Div([
    html.Label('Timeline Parameters', style={'margin-bottom':'10px','fontWeight':'bold', 'fontSize':20}),
    dbc.Stack([start_stop_date_timeline_input, timeline_checklist], gap=2
    )], style={'border':'5px solid #d6d6d6','border-radius':'10px','padding':'10px', 'width':317})




def update_project_list():
    rowData = read_database("project_tracker")
    project_list = ['>>' for i in rowData.values]
    project_list = pd.Series(project_list)
    rowData['Show'] = project_list.values
    rowData['Start Date'] = pd.to_datetime(rowData['Start Date']).dt.strftime("%d/%m/%Y")
    rowData['End Date'] = pd.to_datetime(rowData['End Date']).dt.strftime("%d/%m/%Y")

    return rowData

project_list = dag.AgGrid(
    id="project_list_table",
    rowData=update_project_list().to_dict('records'),
    columnDefs=columnDefs_project_list,
    defaultColDef={'resizable': True},
    style={'width': '100%', 'center': True},
    dashGridOptions={"domLayout": "autoHeight"},
    dangerously_allow_code=True,)

project_timeline = dcc.Loading(dcc.Graph(id='project_timeline',
                            figure= create_project_timeline(lab_member_list_fct(read_database("project_tracker"))),
                            config={'toImageButtonOptions': {'filename':'Lab_member_timeline'}, 'responsive':True, 'displaylogo':False, 'modeBarButtonsToRemove': ['zoom', 'pan','zoomin','zoomout','autoscale','resetscale','lasso2d', 'select2d']},
                            style={'margin-left':'10px','width':'2130px','height': '1060px','fontWeight':'bold'}),
                            overlay_style={"visibility":"unvisible", "filter": "blur(2px)"},type="circle")

timeline_graph = html.Div([
                    dbc.Stack([timeline_parameters, project_timeline], direction='horizontal')],
                    style={'border':'5px solid #d6d6d6','border-radius':'10px','padding':'20px'})

def create_chart_figure(type, label_1, label_2, value, start_date, end_date):
    value = 'Work [hours]' if value == 'Working time' else value
    project_data = read_database("project_tracker")
    project_data = project_data[((start_date <= project_data['Start Date']) & (project_data['Start Date'] <= end_date)) | ((start_date <= project_data['End Date']) & (project_data['End Date'] <= end_date)) | ((project_data['Start Date'] <= start_date) & (project_data['End Date'] <= end_date)) | ((project_data['Start Date'] >= start_date) & (project_data['End Date'] >= end_date))]
    project_data = project_data.to_dict('records')

    label_value = {}
    for project in project_data:
        label_value_label_1 = project[label_1]
        label_value_label_2 = project[label_2] if label_2 is not None else None
        if value == 'Project' and label_value_label_1 is not None and project[label_1] is not None or value == 'Work [hours]' and not math.isnan(project[value]) and label_value_label_1 is not None and project[value] != 0:
            if project[label_1] not in list(label_value.keys()) or label_2 is not None and project[label_2] not in list(label_value[label_value_label_1].keys()):
                if label_2 is not None :
                    if project[label_1] not in list(label_value.keys()):
                        label_value[label_value_label_1] = {}
                    if label_value_label_2 not in list(label_value[label_value_label_1].keys()):
                        label_value[label_value_label_1].update({label_value_label_2:[project[value]]})
                    else:
                        label_value[label_value_label_1][label_value_label_2] = label_value[label_value_label_1][label_value_label_2] + [project[value]]
                else:
                    label_value[label_value_label_1] = [project[value]]
            else:
                if label_value_label_2 is not None:
                    label_value[label_value_label_1][label_value_label_2] = label_value[label_value_label_1][label_value_label_2] + [project[value]]
                else:
                    label_value[label_value_label_1] = label_value[label_value_label_1] + [project[value]]


    if type == 'Pie chart':
        if label_2 is None:

            labels = list(label_value.keys())

            values = []
            if value == 'Project':
                for label_value_value in label_value.values():
                    values.append(len(label_value_value))
            else:
                for label_value_value in label_value.values():
                    values.append(sum(label_value_value))

            hovertemplate = "%{label}: <br>%{value} Hours</br>%{percent}<extra></extra>" if value == 'Work [hours]' else "%{label}: <br>%{value} Projects</br>%{percent}<extra></extra>"
            figure = go.Figure(data=[go.Pie(labels=labels, values=values, hovertemplate = hovertemplate, marker=dict(line=dict(width=2)))],
                               layout=go.Layout(
                                   title=dict(text=f"{'Work time' if value == 'Work [hours]' else value} per {label_1}{'-' + label_2 if label_2 is not None else ''}", font=dict(size=25, weight='bold'), xanchor="left", x=0.6),
                                   hovermode='closest',
                                   showlegend=True,
                                   margin={"t": 50, "b": 0, 'r': 0, 'l': 0},
                                   uniformtext={
                                       "mode": "hide",
                                       "minsize": 16
                                   },
                                   hoverlabel={
                                       'font': {
                                           'size': 16,
                                       }},
                                   legend=dict(
                                       font=dict(size=16),
                                       yanchor="top",
                                       y=0.99,
                                       xanchor="left",
                                       x=0.8,
                                       bgcolor=None),

                               ))
        else:
            ids = []
            labels = []
            parents = []
            values = []
            for key_parent, value_parent in label_value.items():
                ids.append(key_parent)
                labels.append(key_parent)
                parents.append("")
                values.append(0)
                value_nb = 0
                for key_2, value_2 in label_value[key_parent].items():
                    ids.append(f"{key_parent} - {key_2}")
                    labels.append(key_2)
                    parents.append(key_parent)
                    values.append(len(value_2) if value == 'Project' else sum(value_2))
                    value_nb = value_nb + len(value_2) if value == 'Project' else value_nb + sum(value_2)
                for i, n in enumerate(values):
                    if n == 0:
                        values[i] = value_nb

            hovertemplate = "%{label}: <br>%{value} Hours</br><extra></extra>" if value == 'Work [hours]' else "%{label}: <br>%{value} Projects</br><extra></extra>"
            figure = go.Figure(go.Sunburst(
                        ids=ids,
                        labels=labels,
                        parents=parents,
                        values=values,
                        branchvalues="total", hovertemplate = hovertemplate, marker=dict(line=dict(width=2, color='black'))),
                        layout=go.Layout(
                       title=dict(text=f"{'Work time' if value == 'Work [hours]' else value} per {label_1}{'-' + label_2 if label_2 is not None else ''}", font=dict(size=25, weight='bold'), xanchor="left", x=0.6),
                       hovermode='closest',
                       showlegend=True,
                       margin={"t": 50, "b": 0, 'r': 0, 'l': 0},
                        uniformtext={
                            "mode": "hide",
                            "minsize": 16
                        },
                        hoverlabel={
                            'font': {
                                'size': 16,
                            }},
                       legend=dict(
                           font=dict(size=16),
                           yanchor="top",
                           y=0.99,
                           xanchor="left",
                           x=0.8,
                           bgcolor=None,
                       ))
                   )

    else:

        if label_2 is None:
            labels = list(label_value.keys())

            values = []
            if value == 'Project':
                for label_value_value in label_value.values():
                    values.append(len(label_value_value))
            else:
                for label_value_value in label_value.values():
                    values.append(sum(label_value_value))


            sorted_data = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)
            sorted_labels, sorted_values = zip(*sorted_data)

            hovertemplate = "%{label}: <br>%{value} Hours</br><extra></extra>" if value == 'Work [hours]' else "%{label}: <br>%{value} Projects</br><extra></extra>"
            traces = []
            for label_value, value_value in zip(sorted_labels, sorted_values):
                traces.append(go.Bar(name=label_value, x=[label_value], y=[value_value], text=value_value, hovertemplate=hovertemplate, texttemplate='%{text:.2s}', textposition='outside'))

        else:
            traces = []
            labels = []
            values = {}
            for key_parent, value_parent in label_value.items():
                labels.append(key_parent)
                for key_2, value_2 in label_value[key_parent].items():
                    if key_2 not in list(values.keys()):
                        values[key_2] = []
                    values[key_2].append((key_parent, len(value_2) if value == 'Project' else sum(value_2)))

            df = pd.DataFrame({
            'label': list(label_value.keys())
            })

            for key, val in values.items():
                y = []
                i=0
                for index, label in enumerate(labels):
                    try:
                        if val[index - i][0] == label:
                            y.append(val[index - i][1])
                        else:
                            y.append(0)
                            i=i+1
                    except:
                        y.append(0)

                df[key] = y

            df['sum'] = df.iloc[:, 1:].sum(axis=1)
            df = df.sort_values(by='sum', ascending=False)

            for column_name, column_series in df.iloc[:, 1:-1].items():
                hovertemplate = column_name + ": <br>%{value} Hours</br><extra></extra>" if value == 'Work [hours]' else column_name + ": <br>%{value} Projects</br><extra></extra>"
                traces.append(go.Bar(name=column_name, x=df['label'], y=column_series, text=column_series,
                                     hovertemplate=hovertemplate, texttemplate='%{text:.2s}', textposition='inside',
                ))

        figure = go.Figure(
                            data=traces,
                            layout=go.Layout(
                                title=dict(text=f"{'Work time' if value == 'Work [hours]' else value} per {label_1}{'-' + label_2 if label_2 is not None else ''}",
                                           font=dict(size=25, weight='bold'), xanchor="center"),
                                barcornerradius=15,
                                hovermode='closest',
                                barmode='stack',
                                showlegend=True,
                                plot_bgcolor='white',
                                xaxis={'tickfont':dict(size=16)},
                                yaxis={'gridcolor':'lightgrey', 'tickfont':dict(size=16)},
                                uniformtext= {
                                        "mode": "hide",
                                        "minsize": 16
                                },
                                hoverlabel= {
                                        'font': {
                                            'size': 16,
                                        }},
                                margin={"t": 50, "b": 0, 'r': 0, 'l': 0},
                                legend=dict(
                                    font=dict(size=16),
                                    yanchor="top",
                                    y=0.99,
                                    xanchor="left",
                                    x=1,
                                    bgcolor=None,
                                )
                            ))

    return figure

chart = dcc.Graph(
                id='chart',
                figure= create_chart_figure('Pie chart', 'PM', None, 'Project', datetime.datetime(date.today().year,1,1), datetime.datetime(date.today().year+1,1,1)),
                config={'toImageButtonOptions': {'filename':'typ_graph'}, 'responsive':True, 'displaylogo':False, 'modeBarButtonsToRemove': ['zoom', 'pan','zoomin','zoomout','autoscale','resetscale','lasso2d', 'select2d']},
                style={'height': '1062px','width':'2200px','fontWeight':'bold'})



type_chart = html.Div([html.Label('Pie or bar chart', style={'fontWeight':'bold', 'margin-left':'15px'}),
                    dcc.Dropdown(['Pie chart', 'Bar chart'],id="type_chart_input", value='Pie chart', clearable=False, style={'width':287})],)

chart_label_1 = html.Div([html.Label('Label 1', style={'fontWeight':'bold', 'margin-left':'15px'}),
                    dcc.Dropdown(['Project', 'PM', 'Category', 'Typ', 'Client', 'PL'],id="label_chart_input_1", value='PM', clearable=False, style={'width':287})],)

chart_label_2 = html.Div([html.Label('Label 2', style={'fontWeight':'bold', 'margin-left':'15px'}),
                    dcc.Dropdown(['Project', 'PM', 'Category', 'Typ', 'Client', 'PL'],id="label_chart_input_2", value=None, clearable=True, style={'width':287})],)

chart_value = html.Div([html.Label('Value', style={'fontWeight':'bold', 'margin-left':'15px'}),
                    dcc.Dropdown(['Project', 'Working time'],id="value_chart_input", value='Project', clearable=False, style={'width':287})])


chart_date = html.Div([
    html.Label('Start → End Dates', style={'fontWeight':'bold', 'margin-left':'15px'}),
    dcc.DatePickerRange(
        id='chart_date',
        start_date=date(date.today().year,1,1),
        end_date=date(date.today().year+1, 1, 1),
        style={'width':287}
    )])

chart_parameters = html.Div([html.Label('Chart parameters', style={'margin-bottom':'10px','fontWeight':'bold','fontSize':'20px'}),
                    dbc.Stack([type_chart, chart_label_1, chart_label_2, chart_value, chart_date],gap=2)],
                    style={'border':'5px solid #d6d6d6','border-radius':'10px','padding':'10px', 'width':317, 'margin-right':'10px'})

chart_graph = html.Div([
                    dbc.Stack([chart_parameters, chart], direction='horizontal')],
                    style={'border':'5px solid #d6d6d6','border-radius':'10px','padding':'20px'})

menu_btn = html.Div([
                html.Button("Project List", id="btn-project-list", style = {'width': 150, 'height':45,'fontWeight':'bold', "color":"white", "background-color": "#1c4efe"}, className='active_menu_btn'),
                html.Button("Timeline", id="btn-staff-timeline", style = {'width': 150, 'height':45,'fontWeight':'bold', "color":"white", "background-color": "#1c4efe"}, className='menu_btn'),
                html.Button("Graphs", id="btn_graph_report", style = {'width': 150, 'height':45,'fontWeight':'bold', "color":"white", "background-color": "#1c4efe"}, className='menu_btn'),
    ], style={'display': 'flex', 'margin-bottom':-10, 'align-items': 'end', 'margin-left':-800} )

# Header
logo=html.Img(src="https://community.element14.com/e14/assets/main/mfg-group-assets/monolithicpowersystemsLogo.png",style={'height': '50px','margin-right':'10px'})
title=html.H1("EMC Lab Project Management",style={'font-size':50,'font-weight':'bold'})
location=html.H1("EMC Lab Ettenheim",style={'font-size':50,'font-weight':'bold'})
header = html.Div([
            html.Div([
                logo
            ], style={'display': 'flex', 'align-items': 'center'}),
            menu_btn,
            title
        ], style={'display': 'flex', 'justify-content': 'space-between', 'padding': '10px 20px', 'background-color': '#1E2A38', 'color': 'white', 'margin-bottom': '20px', "z-index": "1001"})

# Footer
footer=html.Footer([html.P('Copyright © 2025 Monolithic Power Systems, Inc. All rights reserved.',style={'text-align':'center','color':'#666'})],style={'position':'relative','bottom':'0','width':'100%','padding':'20px 0px','background-color':'#e0e0e0','text-align':'center','margin-top':'20px',"z-index": "1000",})
# Main layout
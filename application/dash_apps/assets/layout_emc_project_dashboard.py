from dash import dcc, ctx, html, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import base64
import datetime
from datetime import date, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import math
import pymysql

connection = pymysql.connect(
       host='localhost',
       port=3306,
       user='root',
       password="password",
       db='emc_lab_database',
       cursorclass=pymysql.cursors.DictCursor,
        connect_timeout = 30,
        read_timeout = 60,
        write_timeout = 60
   )

color_map = {
        "completed": "green",
        "in progress": "yellow",
        "upcoming": "blue"
    }

def read_database(table):
    connection.ping(reconnect=True)
    cursor = connection.cursor()

    if table == "project_tracker":
        cursor.execute("SELECT * FROM emc_lab_database.project_tracker ORDER BY Number ASC")
        project_tracker = cursor.fetchall()
        project_tracker = pd.DataFrame(project_tracker)
        # project_tracker['Start Date'] = pd.to_datetime(project_tracker['Start Date'])
        # project_tracker['End Date'] = pd.to_datetime(project_tracker['End Date'])
        data = project_tracker

    elif table == "project_description":
        cursor.execute("SELECT * FROM emc_lab_database.project_description ORDER BY Number ASC")
        project_description = cursor.fetchall()
        project_description = pd.DataFrame(project_description).sort_values('Number')
        data = project_description

    return data.to_json(date_format='iso')

def lab_member_list_fct(project_data):

    project_data = pd.read_json(project_data)
    project_data['Start Date'] = pd.to_datetime(project_data['Start Date'])
    project_data['End Date'] = pd.to_datetime(project_data['End Date'])
    project_data = project_data.to_dict('records')

    lab_member_list = {}

    for project in project_data:
        PM = project['PM']
        if PM not in list(lab_member_list.keys()):
            lab_member_list[PM] = [project]
        else:
            lab_member_list[PM].append(project)
    return lab_member_list

def create_project_timeline(lab_member_list, start_date, end_date):

    if isinstance(start_date, str):
        if 'T' in start_date:
            start_date = start_date.split('T')[0]
            end_date = end_date.split('T')[0]

        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

    project_timeline_data_list = []
    row = 0
    ticktext = []
    tickvals = []
    for member, projects in lab_member_list.items():
        ticktext.append(member)
        val = ((len(projects)*0.1 + row) - row)/2 + row
        tickvals.append(val)

        for project in projects:
            if project['PM'] is not None and (project['Start Date'] < end_date and project['End Date'] > start_date):
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

def create_chart_figure(type, label_1, label_2, value, start_date, end_date):
    value = 'Work [hours]' if value == 'Working time' else value
    project_data = pd.read_json(read_database("project_tracker"))
    project_data['Start Date'] = pd.to_datetime(project_data['Start Date'])
    project_data['End Date'] = pd.to_datetime(project_data['End Date'])

    project_data = project_data[(project_data['Start Date'] <= end_date) & (project_data['End Date'] >= start_date)]
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
            style = {'height':'33vh'}
        ))

check = html.Img(src='data:image/png;base64,{}'.format(base64.b64encode(open("application/dash_apps/assets/check.png", 'rb').read()).decode()),style={'height': '20px','width':'20px'})
cross = html.Img(src='data:image/png;base64,{}'.format(base64.b64encode(open("application/dash_apps/assets/cross.png", 'rb').read()).decode()),style={'height': '20px','width':'20px'})

external_scripts = ["https://cdnjs.cloudflare.com/ajax/libs/jquery/1.12.1/jquery.min.js",
                    "https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js",
                    'https://trentrichardson.com/examples/timepicker/jquery-ui-timepicker-addon.js']

external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://code.jquery.com/ui/1.13.3/themes/base/jquery-ui.css']

today = date.today()
tomorrow = today + timedelta(days=1)

def serve_layout():

    project_list_btn=dbc.Stack([
                    dbc.Button('Add project',id='add_project', color='primary'),
                    dbc.Button('Save backup',id='save_backup', color='primary'),
                    dcc.Upload(id='upload-backup', children=dbc.Button('Load backup',id='load_backup', color='primary')),
                    dbc.Button(id='loading-screen', children=['No action selected'],disabled=True, style = {'width':'270px', 'borderRadius':'5px', 'border':'none','align-items':'center', 'font-weight':'bold', 'backgroundColor':'#119DFF'}),
                ],direction="horizontal",gap=3,style={'margin-left':'30px','margin-bottom':'10px','align-items':'center'})

    invoice_input = dbc.Row(
        [
            dbc.Label('Invoice', html_for='report_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Input(id="invoice_input", placeholder="Enter invoice"),
                width=10
            )
        ], className="mb-3"
    )

    time_input = dbc.Row(
        [
            dbc.Col(
                dbc.Label('Time [H]', html_for='time_input', style={'fontWeight':'bold'}), width='auto'
            ),
            dbc.Col(
                dbc.Input(id="time_input", readonly=True),
                width=5
            )
        ], className="align-items-center", style={'margin-left':'200px'}
    )

    report_input = dbc.Row(
        [
            dbc.Label('Report', html_for='report_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Input(id="report_input", placeholder="Enter report"),
                width=10
            )
        ], className="mb-3"
    )

    draft_input = dbc.Row(
        [
            dbc.Label('Draft', html_for='draft_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Input(id="draft_input", placeholder="Enter draft"),
                width=10
            )
        ], className="mb-3"
    )

    PO_input = dbc.Row(
        [
            dbc.Label('PO', html_for='PO_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Input(id="PO_input", placeholder="Enter PO"),
                width=10
            )
        ], className="mb-3"
    )

    quote_input = dbc.Row(
        [
            dbc.Label('Quote', html_for='quote_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Input(id="quote_input", readonly=True,),
                width=10
            )
        ], className="mb-3"
    )

    contact_input = dbc.Row(
        [
            dbc.Label('Contact', html_for='contact_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Input(id="contact_input", placeholder="Enter contact"),
                width=10
            )
        ], className="mb-3"
    )

    project_input = dbc.Row(
        [
            dbc.Label('Project', html_for='project_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Input(id="project_input", placeholder="Enter project name"),
                width=10
            )
        ], className="mb-3"
    )

    project_ID = dbc.Row(
        [
            dbc.Label('Project ID', html_for='project_id_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Input(id="project_id_input", placeholder="Enter project ID (optional)"),
                width=10
            )
        ], className="mb-3"
    )

    location_input = dbc.Row(
        [
            dbc.Label('Location', html_for='location_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Input(id="location_input", placeholder="Enter location (optional)"),
                width=10
            )
        ], className="mb-3"
    )

    project_manager_input = dbc.Row(
        [
            dbc.Label('Project manager', html_for='project_manager_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Select(['JS','PS','RG','LK','CL', 'AJ'], value='JS', id="project_manager_input", placeholder="Enter project manager"),
                width=10
            )
        ], className="mb-3"
    )

    category_input = dbc.Row(
        [
            dbc.Label('Category', html_for='category_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Select(['Internal', 'External'], value='Internal', id="category_input", placeholder="Enter category"),
                width=10
            )
        ], className="mb-3"
    )

    type_input = dbc.Row(
        [
            dbc.Label('Type', html_for='type_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Select(['Paid','Non Paid'], value='Paid', id="type_input", placeholder="Enter category"),
                width=10
            )
        ], className="mb-3"
    )

    client_input = dbc.Row(
        [
            dbc.Label('Client', html_for='client_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Select(['EXT','FAE / Sales', 'AE / PL'], value='EXT',id="client_input", placeholder="Enter category"),
                width=10
            )
        ], className="mb-3"
    )

    PL_input = dbc.Row(
        [
            dbc.Label('PL', html_for='PL_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Select(['C1 AC/DC - Lighting', 'E1 ADC', 'N1 Analog', 'A1 Automotive', 'R1 Other', 'I1 Power Magnetics', 'S1 Sensor', 'D1 STD DC/DC','K1 Telecom + Computing','B1 Automotive BMS','X1 Axign'], value='C1 AC/DC - Lighting', id="PL_input"),
                width=10
            )
        ], className="mb-3"
    )

    status_input = html.Div(
        [
            dbc.Label('Status', html_for='status_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Select(['Upcoming', 'Ongoing', 'Completed', 'Canceled'], value='Ongoing', id="status_input"),
                width=10
            )
        ], className="mb-3"
    )
    # start_date = str(date(current_date.year, current_date.month, current_date.day)), end_date = str(date(current_date.year, current_date.month, current_date.day + 1))

    date_input = html.Div(
        [
            dbc.Label('Date range', html_for='date_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dcc.DatePickerRange(id="date_input"),
                width=10
            )
        ], className="mb-3"
    )

    project_window_form = dbc.Form([
        dbc.Row([
                dbc.Col([
                    project_input, project_ID, location_input, project_manager_input, date_input
                ]),
                dbc.Col([
                    category_input, type_input, client_input, PL_input, status_input
                ]),
        ]),
    ])

    ok_project_btn = dbc.Button('Submit', id='ok_project_btn', color='success', outline=True)
    cancel_btn = dbc.Button('Cancel', id='cancel_btn', color='secondary', outline=True)

    project_window = dbc.Modal(centered=True, size='xl', keyboard=False, backdrop='static', children=[
                    dbc.ModalHeader([
                        html.Label('Add new project', style={'fontWeight':'bold', 'fontSize':20, 'margin-left':10})
                    ], close_button=False),
                    dbc.ModalBody([
                        project_window_form
                    ]),
                    dbc.ModalFooter([
                        dbc.Stack([ok_project_btn, cancel_btn], direction='horizontal',gap=3)
                    ])
                    ],
                    id='project_window',style={'padding':'10px','boxShadow':'0px 4px 8px rgba(0,0,0,0.1)'})


    project_description_label = html.Label(id='project_description_label', style={'fontWeight':'bold', 'fontSize':20})
    add_test_service_btn = dbc.Button('+ Add Test Service', outline=True, color='secondary', id='add_test_service_btn',style={'width':170, 'margin-right': 10})
    remove_test_service_btn = dbc.Button('- Remove Test Service', outline=True, color='secondary', id='remove_test_service_btn')

    ok_project_description_btn = dbc.Button('Update', id='close_project_description_btn', color='success', outline=True)
    cancel_project_description_btn = dbc.Button('Cancel',id='cancel_project_description_btn', color='secondary', outline=True)
    remove_project_btn = dbc.Button('Remove',id='remove_project', color='danger', outline=True)

    project_input = dbc.Row(
        [
            dbc.Label('Project', html_for='project_description_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Input(id="project_description_input", placeholder="Enter project name"),
                width=10
            )
        ], className="mb-3"
    )

    project_ID = dbc.Row(
        [
            dbc.Label('Project ID', html_for='project_id_description_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Input(id="project_id_description_input", placeholder="Enter project ID (optional)"),
                width=10
            )
        ], className="mb-3"
    )

    location_input = dbc.Row(
        [
            dbc.Label('Location', html_for='location_description_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Input(id="location_description_input", placeholder="Enter location (optional)"),
                width=10
            )
        ], className="mb-3"
    )

    project_manager_input = dbc.Row(
        [
            dbc.Label('Project manager', html_for='project_manager_description_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Select(['JS','PS','RG','LK','CL', 'AJ'], value='JS', id="project_manager_description_input", placeholder="Enter project manager"),
                width=10
            )
        ], className="mb-3"
    )

    category_input = dbc.Row(
        [
            dbc.Label('Category', html_for='category_description_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Select(['Internal', 'External'], value='Internal', id="category_description_input", placeholder="Enter category"),
                width=10
            )
        ], className="mb-3"
    )

    type_input = dbc.Row(
        [
            dbc.Label('Type', html_for='type_description_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Select(['Paid','Non Paid'], value='Paid', id="type_description_input", placeholder="Enter category"),
                width=10
            )
        ], className="mb-3"
    )

    client_input = dbc.Row(
        [
            dbc.Label('Client', html_for='client_description_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Select(['EXT','FAE / Sales', 'AE / PL'], value='EXT',id="client_description_input", placeholder="Enter category"),
                width=10
            )
        ], className="mb-3"
    )

    PL_input = dbc.Row(
        [
            dbc.Label('PL', html_for='PL_description_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Select(['C1 AC/DC - Lighting', 'E1 ADC', 'N1 Analog', 'A1 Automotive', 'R1 Other', 'I1 Power Magnetics', 'S1 Sensor', 'D1 STD DC/DC','K1 Telecom + Computing','B1 Automotive BMS','X1 Axign'], value='C1 AC/DC - Lighting', id="PL_description_input"),
                width=10
            )
        ], className="mb-3"
    )

    status_input = html.Div(
        [
            dbc.Label('Status', html_for='status_description_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dbc.Select(['Upcoming', 'Ongoing', 'Completed', 'Canceled'], value='Ongoing', id="status_description_input"),
                width=10
            )
        ], className="mb-3"
    )

    date_input = html.Div(
        [
            dbc.Label('Date range', html_for='date_description_input', style={'fontWeight':'bold'}),
            dbc.Col(
                dcc.DatePickerRange(id="date_description_input"),
                width=20
            )
        ], className="mb-3"
    )

    project_description_form = dbc.Form([
        dbc.Row([
                dbc.Col(project_input),
                dbc.Col(project_ID),
                dbc.Col(location_input),
                dbc.Col(project_manager_input),
        ]),
        dbc.Row([
                dbc.Col(category_input),
                dbc.Col(PL_input),
                dbc.Col(PO_input),
                dbc.Col(draft_input),
        ]),
        dbc.Row([
            dbc.Col(invoice_input, width=3),
            dbc.Col(report_input, width=3),
            dbc.Col(contact_input, width=6),
        ]),
        dbc.Row([
            dbc.Col(client_input, width=3),
            dbc.Col(type_input, width=3),
            dbc.Col(quote_input, width=3),
        ]),
        dbc.Row([
            dbc.Col(date_input),
            dbc.Col(status_input),
            dbc.Col(),
        ])
    ])

    project_description = dbc.Modal(centered=True, size='xl', keyboard=False, backdrop='static', children=[
                        dbc.ModalHeader([
                            project_description_label
                        ], close_button=False, style={'margin-bottom':10, 'margin-left':10}),
                        dbc.ModalBody([
                            project_description_form,
                            dbc.Stack([add_test_service_btn, remove_test_service_btn], direction='horizontal'),
                            project_table,
                        ]),
                        dbc.ModalFooter([
                            dbc.Col([
                                dbc.Stack([ok_project_description_btn, cancel_project_description_btn, remove_project_btn], direction='horizontal',gap=2, style={'margin-left':'10px'})
                            ]),
                            dbc.Col([
                                    time_input
                            ], className='ms-auto')
                        ])
        ], id='project_description', style={'padding':'10px 10px','boxShadow':'0px 4px 8px rgba(0,0,0,0.1)'}
    )

    yes_remove_btn = dbc.Button('Confirm', id='yes_remove_btn', color='success')
    no_remove_btn = dbc.Button('Cancel', id='no_remove_btn', color='secondary')

    encoded_image = base64.b64encode(open("application/dash_apps/assets/warning.png", 'rb').read())

    remove_window = dbc.Modal(centered=True, size='lg', keyboard=False, backdrop='static', children=[
        dbc.ModalBody([
            dbc.Row([
                dbc.Col(html.Div(html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()), style={'width':100})), width='auto'),
                dbc.Col([
                        html.P('Are you sure to remove definitively this project ?', style={'fontWeight':'bold', 'margin-bottom':5}),
                        ], align='center', width='auto'),
                ])
            ]),
        dbc.ModalFooter([
            dbc.Stack([yes_remove_btn, no_remove_btn], direction='horizontal',gap=2)
        ])
        ], is_open=False, id='remove_window',style={'boxShadow':'0px 4px 8px rgba(0,0,0,0.1)'})

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

    timeline_parameters = dbc.Card([
        dbc.CardBody([
            html.Label('Timeline Parameters', style={'margin-bottom':'10px','fontWeight':'bold', 'fontSize':20}),
            dbc.Stack([start_stop_date_timeline_input, timeline_checklist], gap=2)
            ])
        ], style={'padding':'10px', 'margin-left':'10px', 'margin-right':'10px'})




    def update_project_list():
        rowData = pd.read_json(read_database("project_tracker"))
        project_list = ['>>' for i in rowData.values]
        project_list = pd.Series(project_list)
        rowData['Show'] = project_list.values
        rowData['Start Date'] = pd.to_datetime(rowData['Start Date']).dt.strftime("%d/%m/%Y")
        rowData['End Date'] = pd.to_datetime(rowData['End Date']).dt.strftime("%d/%m/%Y")

        return rowData.to_json()

    project_list = dag.AgGrid(
        id="project_list_table",
        rowData=pd.read_json(update_project_list()).to_dict('records'),
        columnDefs=columnDefs_project_list,
        defaultColDef={'resizable': True},
        style={'width': '100%', 'height': '100%', 'center': True},
        dangerously_allow_code=True,
        dashGridOptions={'pagination': True, 'paginationPageSize': 20})

    project_timeline = dcc.Loading(dcc.Graph(id='project_timeline',
                                figure= create_project_timeline(lab_member_list_fct(read_database("project_tracker")), datetime.datetime(datetime.datetime.now().year,1,1,), datetime.datetime(datetime.datetime.now().year,12,31)),
                                config={'toImageButtonOptions': {'filename':'Lab_member_timeline'}, 'responsive':True, 'displaylogo':False, 'modeBarButtonsToRemove': ['zoom', 'pan','zoomin','zoomout','autoscale','resetscale','lasso2d', 'select2d']},
                                style={'fontWeight':'bold', 'height':'88.5vh'}),
                                overlay_style={"visibility":"unvisible", "filter": "blur(2px)"},type="circle")

    timeline_graph = dbc.Row([
                        dbc.Col(timeline_parameters, width=2),
                        dbc.Col(project_timeline, width=10)
        ], className="align-items-center")

    chart = dcc.Graph(
                    id='chart',
                    figure= create_chart_figure('Pie chart', 'PM', None, 'Project', datetime.datetime(date.today().year,1,1), datetime.datetime(date.today().year+1,1,1)),
                    config={'toImageButtonOptions': {'filename':'typ_graph'}, 'responsive':True, 'displaylogo':False, 'modeBarButtonsToRemove': ['zoom', 'pan','zoomin','zoomout','autoscale','resetscale','lasso2d', 'select2d']},
                    style={'height':'88.5vh','fontWeight':'bold'})



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

    chart_parameters = dbc.Card([
        dbc.CardBody([
            html.Label('Chart parameters', style={'margin-bottom': '10px', 'fontWeight': 'bold', 'fontSize': '20px'}),
            dbc.Stack([type_chart, chart_label_1, chart_label_2, chart_value, chart_date], gap=2)
            ])
        ], style={'padding':'10px', 'margin-left':'10px', 'margin-right':'10px'})

    chart_graph = dbc.Row([
                        dbc.Col(chart_parameters, width=2),
                        dbc.Col(chart, width=10)
        ], className="align-items-center")

    menu_btn = html.Div([
                    html.Button("Project List", id="btn-project-list", style = {'width': 150, 'height':45,'fontWeight':'bold', "color":"white", "background-color": "#1c4efe"}, className='active_menu_btn'),
                    html.Button("Timeline", id="btn-staff-timeline", style = {'width': 150, 'height':45,'fontWeight':'bold', "color":"white", "background-color": "#1c4efe"}, className='menu_btn'),
                    html.Button("Graphs", id="btn_graph_report", style = {'width': 150, 'height':45,'fontWeight':'bold', "color":"white", "background-color": "#1c4efe"}, className='menu_btn'),
        ], style={'display': 'flex', 'margin-bottom':-10, 'align-items': 'end', 'margin-left':-800})

    project_list_content = dbc.Card(
            [project_list_btn, project_list, project_description, project_window, remove_window],
             style={'padding':'10px', 'height': '92.5vh'})

    timeline_content = dbc.Card(
            [timeline_graph],
            style={'padding':'10px', 'height': '92.5vh'})

    graphs_content = dbc.Card(
            [chart_graph],
            style={'padding':'10px', 'height': '92.5vh'})

    table = dbc.Tabs(
        [
        dbc.Tab(label='Project List', tab_id='project_list', children=project_list_content, style={'padding':'10px'}),
        dbc.Tab(label='Timeline', tab_id='timeline', children=timeline_content, style={'padding':'10px'}),
        dbc.Tab(label='Graphs', tab_id='graphs', children=graphs_content, style={'padding':'10px'}),
    ], active_tab='project_list', id='tabs')


    layout = (dbc.Container([
        table
        ], fluid=True, style={'padding': '10px'}),
        dcc.Store(id='project_number', data=None),
        dcc.Download(id="download_backup"),
        dcc.Interval(id='interval', interval=3000, max_intervals=1))

    return layout
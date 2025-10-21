from dash import dcc, ctx, html, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import plotly.graph_objects as go
import dash_daq as daq

default_colors = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#e377c2','#7f7f7f']
name2color = {'Blue':'#1f77b4', 'Orange':'#ff7f0e', 'Green':'#2ca02c', 'Red':'#d62728', 'Purple':'#9467bd', 'Brown':'#8c564b', 'Pink':'#e377c2', 'Gray':'#7f7f7f'}
detector2color = {'Peak':'#1f77b4', 'QPeak':'#d62728', 'AVG':'#2ca02c'}

detector_to_color_gradient = {
    'Peak': {'9 kHz': 'rgb(106,174,214)', '120 kHz': 'rgb(46,126,188)', '200 kHz': 'rgb(46,126,188)', '1 MHz': 'rgb(8,74,145)'},
    'QPeak': {'9 kHz': 'rgb(251,105,74)', '120 kHz': 'rgb(217,37,35)', '200 kHz': 'rgb(217,37,35)', '1 MHz': 'rgb(152,12,19)'},
    'CAVG': {'9 kHz': 'rgb(115,196,118)', '120 kHz': 'rgb(47,151,78)', '200 kHz': 'rgb(47,151,78)', '1 MHz': 'rgb(0,100,40)'}
}

Gradient = {'Blue' : 'Blues', 'Orange' : 'Oranges', 'Green' : 'Greens', 'Red' : 'Reds', 'Purple' : 'Purples', 'Brown' : 'copper', 'Pink' : 'RdPu', 'Gray' : 'Grays'}

emission_h_layout = go.Layout(hovermode= 'closest',
           legend= {'bordercolor': 'gray',
                      'borderwidth': 0.5,
                      'orientation': 'h',
                      'x': 0.5,
                      'xanchor': 'center',
                      'y': -0.15},
           margin= {'b': 50, 'l': 50, 'r': 30, 't': 25},
           plot_bgcolor= 'white',
           title= {'font': {'size': 16, 'weight': 'bold'}, 'text': 'Horizontal Polarization'},
           xaxis= {'gridcolor': 'lightgrey',
                     'hoverformat': ('<b> {meta[0]}<br> Frequency (MHz):</b> {x:.2f} <b> <br> Level (dBµV/m):</b> {y:.2f}'),
                     'linecolor': 'black',
                     'mirror': True,
                     'showline': True,
                     'tickfont': {'size': 12, 'weight': 'bold'},
                     'ticks': 'outside',
                     'title': {'font': {'size': 16, 'weight': 'bold'}, 'text': 'Frequency (MHz)'},
                     'type': 'log'},
           yaxis= {'gridcolor': 'lightgrey',
                     'linecolor': 'black',
                     'mirror': True,
                     'showline': True,
                     'tickfont': {'size': 12, 'weight': 'bold'},
                     'ticks': 'outside',
                     'title': {'font': {'size': 16, 'weight': 'bold'}, 'text': 'Level (dBµV/m)'}})

emission_conduction_ground_layout = go.Layout(
               hovermode= 'closest',
               legend= {'bordercolor': 'gray',
                          'borderwidth': 0.5,
                          'orientation': 'h',
                          'x': 0.5,
                          'xanchor': 'center',
                          'y': -0.15},
               margin= {'b': 50, 'l': 50, 'r': 30, 't': 25},
               plot_bgcolor= 'white',
               title= {'font': {'size': 16, 'weight': 'bold'}, 'text': 'Ground Polarization'},
               xaxis= {'gridcolor': 'lightgrey',
                         'hoverformat': ('<b> {meta[0]}<br> Frequency (MHz):</b> {x:.2f} <b> <br> Level (dBµV/m):</b> {y:.2f}'),
                         'linecolor': 'black',
                         'mirror': True,
                         'showline': True,
                         'tickfont': {'size': 12, 'weight': 'bold'},
                         'ticks': 'outside',
                         'title': {'font': {'size': 16, 'weight': 'bold'}, 'text': 'Frequency (MHz)'},
                         'type': 'log'},
               yaxis= {'gridcolor': 'lightgrey',
                         'linecolor': 'black',
                         'mirror': True,
                         'showline': True,
                         'tickfont': {'size': 12, 'weight': 'bold'},
                         'ticks': 'outside',
                         'title': {'font': {'size': 16, 'weight': 'bold'}, 'text': 'Level (dBµV/m)'}})

emission_v_layout = go.Layout(hovermode= 'closest',
           legend= {'bordercolor': 'gray',
                      'borderwidth': 0.5,
                      'orientation': 'h',
                      'x': 0.5,
                      'xanchor': 'center',
                      'y': -0.15},
           margin= {'b': 50, 'l': 50, 'r': 30, 't': 25},
           plot_bgcolor= 'white',
           title= {'font': {'size': 16, 'weight': 'bold'}, 'text': 'Vertical Polarization'},
           xaxis= {'gridcolor': 'lightgrey',
                     'hoverformat': ('<b> {meta[0]}<br> Frequency (MHz):</b> {x:.2f} <b> <br> Level (dBµV/m):</b> {y:.2f}'),
                     'linecolor': 'black',
                     'mirror': True,
                     'showline': True,
                     'tickfont': {'size': 12, 'weight': 'bold'},
                     'ticks': 'outside',
                     'title': {'font': {'size': 16, 'weight': 'bold'}, 'text': 'Frequency (MHz)'},
                     'type': 'log'},
           yaxis= {'gridcolor': 'lightgrey',
                     'linecolor': 'black',
                     'mirror': True,
                     'showline': True,
                     'tickfont': {'size': 12, 'weight': 'bold'},
                     'ticks': 'outside',
                     'title': {'font': {'size': 16, 'weight': 'bold'}, 'text': 'Level (dBµV/m)'}})

emission_conduction_supply_layout = go.Layout(
               hovermode= 'closest',
               legend= {'bordercolor': 'gray',
                          'borderwidth': 0.5,
                          'orientation': 'h',
                          'x': 0.5,
                          'xanchor': 'center',
                          'y': -0.15},
               margin= {'b': 50, 'l': 50, 'r': 30, 't': 25},
               plot_bgcolor= 'white',
               title= {'font': {'size': 16, 'weight': 'bold'}, 'text': 'Supply Polarization'},
               xaxis= {'gridcolor': 'lightgrey',
                         'hoverformat': ('<b> {meta[0]}<br> Frequency (MHz):</b> {x:.2f} <b> <br> Level (dBµV/m):</b> {y:.2f}'),
                         'linecolor': 'black',
                         'mirror': True,
                         'showline': True,
                         'tickfont': {'size': 12, 'weight': 'bold'},
                         'ticks': 'outside',
                         'title': {'font': {'size': 16, 'weight': 'bold'}, 'text': 'Frequency (MHz)'},
                         'type': 'log'},
               yaxis= {'gridcolor': 'lightgrey',
                         'linecolor': 'black',
                         'mirror': True,
                         'showline': True,
                         'tickfont': {'size': 12, 'weight': 'bold'},
                         'ticks': 'outside',
                         'title': {'font': {'size': 16, 'weight': 'bold'}, 'text': 'Level (dBµV/m)'}})

sidebar_style = {
    "position": "fixed",
    "top": 80,
    "right": 0,
    "bottom": 80,
    "height": '100%',
    "width": "520px",
    "padding": "10px",
    "background-color": "#F4F6F7",  # Light gray background for the sidebar
    "color": "#34495E",  # Dark text color for readability
    "box-shadow": "0px 0px 10px rgba(0, 0, 0, 0.1)",  # Subtle shadow for depth
    "transform": "translateX(100%)",  # Hidden by default
    "transition": "transform 0.3s ease",
    "z-index": "1000",  # To make sure sidebar is on top
    'overflowY':'scroll'
}

# Button styles
button_style = {
    "width": "100%",  # Make the button take full width of sidebar
    "padding": "15px",
    "margin-bottom": "10px",  # Space between buttons
    "background-color": "#1F3A68",  # MPS-style blue background
    "color": "#FFF",  # White text
    "border": "none",
    "cursor": "pointer",
    "font-size": "18px",
    "font-family": "Arial, sans-serif",  # Clean sans-serif font
    "border-radius": "5px",  # Rounded corners for the buttons
    "transition": "background-color 0.3s ease",  # Button hover effect
}

submenu_style = {
    "display": "none",  # Submenu hidden initially
    "padding": "10px",
    "background-color": "#E9EFF1",  # Light blue background for submenu
    "color": "#34495E",  # Dark text for submenu
    "transition": "transform 0.3s ease",
    "transform": "translateY(-100%)",  # Hidden by default, off-screen
}

submenu_active_style = {
    "display": "block",  # Show submenu
    "transform": "translateY(0)",  # Slide it down
}

# Content area style
content_style = {
    "margin-right": "0px",  # No margin initially, so sidebar slides over
    "padding": "20px",
    "background-color": "#FFFFFF",  # White background for main content
    "color": "#34495E",  # Dark text color for readability
}

columnDefs_suspectTable = [{"checkboxSelection": {'function': "params.data.disabled == 'False'"}, 'showDisabledCheckboxes': True, "headerCheckboxSelection": True, 'width': 50, 'pinned': 'left'},
    {"headerName":"Suspects: Test Name","field": "source_file", 'width': 400, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Scan","field": "Scan", 'flex':1, "filter": "agNumberColumnFilter", "filterParams": {"filterOptions": ["Equals", "Does not equals", "Greater than", "Less than", "Between"], "debounceMs": 500}},
    {"headerName":"Band","field": "Band", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Polarization","field": "Polarization", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Frequency (MHz)","field": "Frequency (MHz)", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Detector","field": "Detector", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Meas.Value (dBµV/m)","field": "Meas.Value (dBµV/m)", 'flex':1, "filter": "agNumberColumnFilter", "filterParams": {"filterOptions": ["Equals", "Does not equals", "Greater than", "Less than", "Between"], "debounceMs": 500}},
    {"headerName":"Limit.Value (dBµV/m)","field": "Limit.Value (dBµV/m)", 'flex':1, "filter": "agNumberColumnFilter", "filterParams": {"filterOptions": ["Equals", "Does not equals", "Greater than", "Less than", "Between"], "debounceMs": 500}},
    {"headerName":"Diff (dB)","field": "Diff (dB)", 'flex':1, "filter": "agNumberColumnFilter", "filterParams": {"filterOptions": ["Equals", "Does not equals", "Greater than", "Less than", "Between"], "debounceMs": 500}},
    {"headerName":"RBW","field": "RBW", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Conclusion","field": "Pass_Fail", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"field": "disabled", "hide": True}]

getRowStyle_suspect = {
    "styleConditions": [
        {
            "condition": "params.data.Pass_Fail == 'Fail'",
            "style": {"backgroundColor": "lightcoral"},
        },
    ]
}

columnDefs_tests=[{"headerName":"",
        "field": "Show",
        "cellRenderer": "Button",
        "cellRendererParams": {'className': "block text-center text-md text-white rounded no-underline cursor-pointer hover:bg-blue-600", },
        'width': 70, 'pinned': 'left', 'cellStyle': {'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'}, 'sortable': False},
    {"headerName": "Test Name", "field": "source_file", 'flex':1, "hide": False, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName": "Type", "field": "Type", 'width': 250, "hide": False, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName": "Limits", "field": "Limits", 'flex': 1, "hide": False, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    # {"headerName":"Frequency Range","field": "Frequency Range", 'width': 180, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Operation Mode","field": "Operation Mode", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Modification","field": "Modification", 'flex': 1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName": "Date", "field": "Date", 'width': 200, "filter": "agDateColumnFilter", "filterParams": {"filterOptions": ["Equals", "Before", "After", "Between"]}},
    {"headerName":"Conclusion","field": "Passed_Failed", 'width': 150, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}}]

columnDefs_scans=[
    {"headerName":"<",
        "field": "",
        "headerComponent": "ButtonHeader",
        'width': 70, 'pinned': 'left', 'headerComponentParams': {'className': "block text-center text-md text-white rounded no-underline cursor-pointer hover:bg-blue-600 d-flex align-items-center justify-content-center"}, 'sortable': False,
     },
    {"headerName":"Scan","field": "Scan", 'flex':1, "checkboxSelection": True, "headerCheckboxSelection": True, "filter": "agNumberColumnFilter", "filterParams": {"filterOptions": ["Equals", "Does not equals", "Greater than", "Less than", "Between"], "debounceMs": 500}},
    {"headerName":"Bands","field": "Bands", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Frequency Range","field": "Frequency Range", 'width': 250, "filter": "agNumberColumnFilter", "filterParams": {"filterOptions": ["Equals", "Does not equals", "Greater than", "Less than", "Between"], "debounceMs": 500}},
    {"headerName":"Step","field": "Frequency Step", 'flex':1, "filter": "agNumberColumnFilter", "filterParams": {"filterOptions": ["Equals", "Does not equals", "Greater than", "Less than", "Between"], "debounceMs": 500}},
    {"headerName":"Polarization","field": "Polarization", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"RBW","field": "RBW", 'flex':1, "filter": "agNumberColumnFilter", "filterParams": {"filterOptions": ["Equals", "Does not equals", "Greater than", "Less than", "Between"], "debounceMs": 500}},
    {"headerName": "Meas. Time", "field": "Sweep Time", 'flex': 1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"headerName":"Detector","field": "Detectors", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    # {"headerName":"Conclusion","field": "Test_Pass", 'flex':1, "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains", "notContains", "Equals", "Does not equals"], "debounceMs": 500}},
    {"field": "id", "hide": True}]

getRowStyle_test = {
    "styleConditions": [
        {
            "condition": "params.data.Passed_Failed == 'FAILED'",
            "style": {"backgroundColor": "lightcoral"},
        },
    ]
}

columnDefs_limits = [{"checkboxSelection": {'function': "params.data.disabled == 'False'"}, 'showDisabledCheckboxes': True, "headerCheckboxSelection": True, 'width': 50, 'pinned': 'left'},
    {"headerName":"Name","field": "Name", 'flex':1},
    {"field": "chart", "hide": True},
    {"field": "disabled", "hide": True}]

columnDefs_noise = [{"headerName":"", "checkboxSelection": True, "headerCheckboxSelection": True, 'width': 50, 'pinned': 'left'},
    {"headerName":"Name","field": "Name", 'flex':1},
    {"headerName": "Bands", "field": "Bands", 'flex': 1},
    {"headerName": "Frequency Range", "field": "Frequency Range", 'flex': 1},
    {"headerName": "Detector", "field": "Detector", 'flex': 1},
    {"headerName": "Data", "field": "Data", "hide": True}]

columnDefs_line = [{"headerName":"Name","field": "Name", 'width': 500},
    {"headerName":"Color","field": "Color",'width':'90px','editable':True, 'flex':1,'cellEditor':'agSelectCellEditor', 'cellEditorParams': {'values':['Blue', 'Orange', 'Green', 'Red', 'Purple', 'Brown', 'Pink', 'Gray']}},
    {"headerName":"Width","field": "Width",'width':'90px','editable':True, 'flex':1,'cellEditor':{"function": "NumberInput"},"cellEditorParams" : {"placeholder": "Enter a number"}},
    {"headerName":"Type","field": "Type",'width':'90px', 'editable':True, 'flex':1,'cellEditor':'agSelectCellEditor', 'cellEditorParams': {'values':['solid','dash','dot']}}]




check = html.Img(src="https://cdn-icons-png.flaticon.com/512/5610/5610944.png",style={'height': '20px','width':'20px'})
cross = html.Img(src="https://cdn-icons-png.flaticon.com/512/10100/10100000.png",style={'height': '20px','width':'20px'})

logo=html.Img(src="https://community.element14.com/e14/assets/main/mfg-group-assets/monolithicpowersystemsLogo.png",style={'height': '50px','margin-right':'10px'})
title=html.H1("Emission With Bands",style={'font-size':50,'font-weight':'bold'})
location=html.H1("Ettenheim EMC Lab",style={'font-size':50,'font-weight':'bold','text-align':'right'})
footer=html.Footer([html.P('Copyright © 2024 Monolithic Power Systems, Inc. All rights reserved.',style={'text-align':'center','color':'#666'})],style={'position':'relative','bottom':'0','width':'100%','padding':'20px 0px','background-color':'#e0e0e0','text-align':'center','margin-top':'20px'})

sidebar_button = html.Button("Graph Parameters", id="toggle-button", n_clicks=0, disabled=True,
                             style={
                                 "position": "fixed",
                                 "right": "20px",
                                 "top": "10px",
                                 "z-index": "1001",
                                 "background-color": "#1F3A68",
                                 "color": "#FFF",
                                 "border": "none",
                                 "padding": "10px 20px",
                                 "cursor": "pointer",
                                 "font-size": "16px",
                                 "border-radius": "5px",
                                 "transition": "background-color 0.3s ease",  # Button hover effect
                                 "transition": "transform 0.3s ease",
                             })

limits_table_h = dag.AgGrid(
        id="limits-table-h",
        rowData=[],
        columnDefs=columnDefs_limits,
        dashGridOptions={"rowSelection": "multiple", "rowDragManaged": True,
                "rowDragEntireRow": True,
                "rowDragMultiRow": True,
                "suppressMoveWhenRowDragging": True,
                "isRowSelectable": {'function': "params.data.disabled == 'False'"}},
        defaultColDef={'resizable': True},
        selectAll=True,
        style={'center':True,'fontSize':'12px','height':'300px','width':'100%'})

line_table_h = dag.AgGrid(
        id="line-table-h",
        rowData=[],
        columnDefs=columnDefs_line,
        dashGridOptions={"rowDragManaged": True,
                "rowDragEntireRow": True,
                "rowDragMultiRow": True,
                "suppressMoveWhenRowDragging": True},
        defaultColDef={'resizable': True},
        style={'center':True,'fontSize':'12px','height':'300px','width':'100%'})

line_table_Div_h = html.Div([dbc.Stack([limits_table_h, line_table_h,],gap=2)],id='line-table-container-h',style={'width':800,'display':'none','position':'fixed','top':'20%','right':'23%','bg-color':'rgba(255,255,255,0.95)','padding':'10px 10px','boxShadow':'0px 4px 8px rgba(0,0,0,0.1)','zIndex':'1002','borderRadius':'8px','overflow':'auto'})

line_table_btn_h = html.Button('Show Line Display Parameters',id='line-table-btn-h',n_clicks=0,style={'width':'230px','height':'50px',"padding": "15px","background-color": "#1F3A68","color": "#FFF","border": "none","cursor": "pointer","font-size": "14px","font-family": "Arial, sans-serif","border-radius": "5px"})

line_menu_h = html.Div([dbc.Row((line_table_btn_h),justify='center')],style={'padding':'10px'})

log_btn_h = html.Div([html.Label('Horizontal Graph',style={'fontWeight':'bold','margin-left':'20px','margin-bottom':'5px'}),html.Label('X axis Scale',style={'fontWeight':'bold','margin-left':'20px','margin-bottom':'5px'}),dcc.RadioItems(id='xaxis-emission_h',options=[{'label':' Logarithmic','value':'log'},{'label':' Linear','value':'linear'}],value='log',inline=True,labelStyle={'fontWeight':'bold','margin-right':'10px','margin-bottom':'10px'},className='radio-item-spacing')])
input_x_min_max_h = html.Div([dbc.Row(html.Label('X axis limits',style={'fontWeight':'bold','margin-left':'20px','margin-bottom':'5px'})),
                            dbc.Row([dbc.Col([dbc.Stack([html.Label('Min',style={'fontWeight':'bold'}),dcc.Input(id='input_x_min-emission_h',type='number',value=None,debounce = True,style={'width':'75px', 'textAlign':'center'})],direction="horizontal",gap=2)]),dbc.Col([dbc.Stack([html.Label('Max',style={'fontWeight':'bold'}),dcc.Input(id='input_x_max-emission_h',type='number',value=None,debounce = True,style={'width':'75px', 'textAlign':'center'})],direction="horizontal",gap=2)])],className="g-0",style={'margin-bottom':'10px'})])
input_y_min_max_h = html.Div([dbc.Row(html.Label('Y axis limits',style={'fontWeight':'bold','margin-left':'20px','margin-bottom':'5px'})),
                            dbc.Row([dbc.Col([dbc.Stack([html.Label('Min',style={'fontWeight':'bold'}),dcc.Input(id='input_y_min-emission_h',type='number',value=None,debounce = True,style={'width':'75px', 'textAlign':'center'})],direction="horizontal",gap=2)]),dbc.Col([dbc.Stack([html.Label('Max',style={'fontWeight':'bold'}),dcc.Input(id='input_y_max-emission_h',type='number',value=None,debounce = True,style={'width':'75px', 'textAlign':'center'})],direction="horizontal",gap=2)])],className="g-0")])

log_btn_v = html.Div([html.Label('Vertical Graph',style={'fontWeight':'bold','margin-left':'20px','margin-bottom':'5px'}),html.Label('X axis Scale',style={'fontWeight':'bold','margin-left':'20px','margin-bottom':'5px'}),dcc.RadioItems(id='xaxis-emission_v',options=[{'label':' Logarithmic','value':'log'},{'label':' Linear','value':'linear'}],value='log',inline=True,labelStyle={'fontWeight':'bold','margin-right':'10px','margin-bottom':'10px'},className='radio-item-spacing')])
input_x_min_max_v = html.Div([dbc.Row(html.Label('X axis limits',style={'fontWeight':'bold','margin-left':'20px','margin-bottom':'5px'})),
                            dbc.Row([dbc.Col([dbc.Stack([html.Label('Min',style={'fontWeight':'bold'}),dcc.Input(id='input_x_min-emission_v',type='number',value=None,debounce = True,style={'width':'75px', 'textAlign':'center'})],direction="horizontal",gap=2)]),dbc.Col([dbc.Stack([html.Label('Max',style={'fontWeight':'bold'}),dcc.Input(id='input_x_max-emission_v',type='number',value=None,debounce = True,style={'width':'75px', 'textAlign':'center'})],direction="horizontal",gap=2)])],className="g-0",style={'margin-bottom':'10px'})])
input_y_min_max_v = html.Div([dbc.Row(html.Label('Y axis limits',style={'fontWeight':'bold','margin-left':'20px','margin-bottom':'5px'})),
                            dbc.Row([dbc.Col([dbc.Stack([html.Label('Min',style={'fontWeight':'bold'}),dcc.Input(id='input_y_min-emission_v',type='number',value=None,debounce = True,style={'width':'75px', 'textAlign':'center'})],direction="horizontal",gap=2)]),dbc.Col([dbc.Stack([html.Label('Max',style={'fontWeight':'bold'}),dcc.Input(id='input_y_max-emission_v',type='number',value=None,debounce = True,style={'width':'75px', 'textAlign':'center'})],direction="horizontal",gap=2)])],className="g-0")])

cursor_params = html.Div([
    dbc.Stack([html.Label('Activate cursors : ', style={'font-weight':'bold','font-size':18, 'marginRight':5}),daq.BooleanSwitch(id='activate_cursors_radiated_h', on=False)], direction='horizontal', style={'margin-bottom':10, 'margin-top':10}),
], style={'marginBottom':10})

cursor_left = html.Div([
    html.H2("Cursors left", style={"font-size": "18px", "margin-left": "10px","font-weight": "bold", "font-family": "Arial, sans-serif"}),
    dbc.Stack([html.Label('Source : ', style={'font-weight':'bold','font-size':16, 'marginRight':5}), dcc.Dropdown(id='trace_cursor_left_radiated_h', options=[], clearable=False, style={'width':370})], direction='horizontal', style={'margin-bottom':10}),
    dbc.Stack([html.Label('Position : ', style={'font-weight':'bold','font-size':16, 'marginRight':5}), dcc.Input(id='position_cursor_left_radiated_h', type='number', value=None)], direction='horizontal')
], style={"margin-bottom": "10px"})

cursor_right = html.Div([
    html.H2("Cursors right", style={"font-size": "18px", "margin-left": "10px","font-weight": "bold", "font-family": "Arial, sans-serif"}),
    dbc.Stack([html.Label('Source: ', style={'font-weight':'bold','font-size':16, 'marginRight':5}), dcc.Dropdown(id='trace_cursor_right_radiated_h', options=[], clearable=False, style={'width':370})], direction='horizontal', style={'margin-bottom':10}),
    dbc.Stack([html.Label('Position: ', style={'font-weight':'bold','font-size':16, 'marginRight':5}), dcc.Input(id='position_cursor_right_radiated_h', type='number', value=None)], direction='horizontal')
], style={"margin-bottom": "10px"})

cursors_result = html.Div([
    html.H2("Cursors result", style={"font-size": "18px", "margin-left": "10px","font-weight": "bold", "font-family": "Arial, sans-serif"}),
    dbc.Stack([html.Label('Δx: ', id='Δx_radiated_h', style={'font-weight':'bold','font-size':16, 'margin-right':50}), html.Label('1/Δx: ', id='1/Δx_radiated_h', style={'font-weight':'bold','font-size':16})], direction='horizontal', style={'margin-bottom':10}),
    dbc.Stack([html.Label('Δy: ', id='Δy_radiated_h', style={'font-weight':'bold','font-size':16, 'margin-right':50}), html.Label('Δy/Δx: ', id='Δy/Δx_radiated_h', style={'font-weight':'bold','font-size':16})], direction='horizontal')
], style={"margin-bottom": "10px"})

cursor_menu = html.Div([
    dbc.Stack([html.Label('Cursors direction : ', style={'font-weight': 'bold', 'font-size': 18, 'marginRight': 5}), dcc.RadioItems(id='cursors_direction_radiated_h', options=['Vertical', 'Horizontal'], value='Vertical', inline=True, labelStyle={"margin": "1rem"}, inputStyle={"margin-right": "5px"})], direction='horizontal'),
    cursor_left,
    cursor_right,
    cursors_result
], id='cursor_menu_radiated_h', style={'display':'none'})

horizontal_parameters_menu = html.Div([dbc.Stack([log_btn_h, input_x_min_max_h, input_y_min_max_h, cursor_params, cursor_menu,  line_menu_h], gap = 1)],id='Div_axes_param_h',style={'border':'1px solid #d6d6d6','border-radius':'10px','padding':'10px','margin-bottom':'10px', 'display':'none'})

cursor_params = html.Div([
    dbc.Stack([html.Label('Activate cursors : ', style={'font-weight':'bold','font-size':18, 'marginRight':5}),daq.BooleanSwitch(id='activate_cursors_radiated_v', on=False)], direction='horizontal', style={'margin-bottom':10, 'margin-top':10}),
], style={'marginBottom':10})

cursor_left = html.Div([
    html.H2("Cursors left", style={"font-size": "18px", "margin-left": "10px","font-weight": "bold", "font-family": "Arial, sans-serif"}),
    dbc.Stack([html.Label('Source : ', style={'font-weight':'bold','font-size':16, 'marginRight':5}), dcc.Dropdown(id='trace_cursor_left_radiated_v', options=[], clearable=False, style={'width':370})], direction='horizontal', style={'margin-bottom':10}),
    dbc.Stack([html.Label('Position : ', style={'font-weight':'bold','font-size':16, 'marginRight':5}), dcc.Input(id='position_cursor_left_radiated_v', type='number', value=None)], direction='horizontal')
], style={"margin-bottom": "10px"})

cursor_right = html.Div([
    html.H2("Cursors right", style={"font-size": "18px", "margin-left": "10px","font-weight": "bold", "font-family": "Arial, sans-serif"}),
    dbc.Stack([html.Label('Source: ', style={'font-weight':'bold','font-size':16, 'marginRight':5}), dcc.Dropdown(id='trace_cursor_right_radiated_v', options=[], clearable=False, style={'width':370})], direction='horizontal', style={'margin-bottom':10}),
    dbc.Stack([html.Label('Position: ', style={'font-weight':'bold','font-size':16, 'marginRight':5}), dcc.Input(id='position_cursor_right_radiated_v', type='number', value=None)], direction='horizontal')
], style={"margin-bottom": "10px"})

cursors_result = html.Div([
    html.H2("Cursors result", style={"font-size": "18px", "margin-left": "10px","font-weight": "bold", "font-family": "Arial, sans-serif"}),
    dbc.Stack([html.Label('Δx: ', id='Δx_radiated_v', style={'font-weight':'bold','font-size':16, 'margin-right':50}), html.Label('1/Δx: ', id='1/Δx_radiated_v', style={'font-weight':'bold','font-size':16})], direction='horizontal', style={'margin-bottom':10}),
    dbc.Stack([html.Label('Δy: ', id='Δy_radiated_v', style={'font-weight':'bold','font-size':16, 'margin-right':50}), html.Label('Δy/Δx: ', id='Δy/Δx_radiated_v', style={'font-weight':'bold','font-size':16})], direction='horizontal')
], style={"margin-bottom": "10px"})

cursor_menu_v = html.Div([
    dbc.Stack([html.Label('Cursors direction : ', style={'font-weight': 'bold', 'font-size': 18, 'marginRight': 5}), dcc.RadioItems(id='cursors_direction_radiated_v', options=['Vertical', 'Horizontal'], value='Vertical', inline=True, labelStyle={"margin": "1rem"}, inputStyle={"margin-right": "5px"})], direction='horizontal'),
    cursor_left,
    cursor_right,
    cursors_result
], id='cursor_menu_radiated_v', style={'display':'none'})


limits_table_v = dag.AgGrid(
        id="limits-table-v",
        rowData=[],
        columnDefs=columnDefs_limits,
        dashGridOptions={"rowSelection": "multiple", "rowDragManaged": True,
                         "rowDragEntireRow": True,
                         "rowDragMultiRow": True,
                         "suppressMoveWhenRowDragging": True,
                         "isRowSelectable": {'function': "params.data.disabled == 'False'"}},
        defaultColDef={'resizable': True},
        style={'center':True,'fontSize':'12px','height':'300px','width':'100%'})

line_table_v = dag.AgGrid(
        id="line-table-v",
        rowData=[],
        columnDefs=columnDefs_line,
        dashGridOptions={"rowSelection": "multiple", "rowDragManaged": True,
                         "rowDragEntireRow": True,
                         "rowDragMultiRow": True,
                         "suppressMoveWhenRowDragging": True},
        defaultColDef={'resizable': True},
        style={'center':True,'fontSize':'12px','height':'300px','width':'100%'})

line_table_Div_v = html.Div([dbc.Stack([limits_table_v, line_table_v],gap=2)],id='line-table-container-v',style={'width':800,'display':'none','position':'fixed','top':'20%','right':'23%','bg-color':'rgba(255,255,255,0.95)','padding':'10px 10px','boxShadow':'0px 4px 8px rgba(0,0,0,0.1)','zIndex':'1002','borderRadius':'8px','overflow':'auto'})

line_table_btn_v = html.Button('Show Line Display Parameters',id='line-table-btn-v',n_clicks=0,style={'width':'230px','height':'50px',"padding": "15px","background-color": "#1F3A68","color": "#FFF","border": "none","cursor": "pointer","font-size": "14px","font-family": "Arial, sans-serif","border-radius": "5px"})

line_menu_v = html.Div([dbc.Row((line_table_btn_v),justify='center')],style={'padding':'10px'})

vertical_parameters_menu = html.Div([dbc.Stack([log_btn_v,input_x_min_max_v,input_y_min_max_v, cursor_params, cursor_menu_v, line_menu_v], gap = 1)],id='Div_axes_param_v',style={'border':'1px solid #d6d6d6','border-radius':'10px','padding':'10px','margin-bottom':'10px', 'display':'none'})

line_table_btn = html.Button('Show Line Display Parameters',id='line_table_btn',n_clicks=0,style={'width':'230px','height':'50px',"padding": "15px","background-color": "#1F3A68","color": "#FFF","border": "none","cursor": "pointer","font-size": "14px","font-family": "Arial, sans-serif","border-radius": "5px"})

line_menu = html.Div([dbc.Row(html.Label('Line Display Parameters',style={'margin-bottom':'5px','margin-left':'25px','fontWeight':'bold'})),dbc.Row((line_table_btn),justify='center')],style={'border':'1px solid #d6d6d6','border-radius':'10px','padding':'10px','margin-bottom':'10px'})

marker_btn = html.Button('Clear Markers',id='clear_markers_btn',n_clicks=0,style={'width':'230px','height':'50px',"padding": "15px","background-color": "#1F3A68","color": "#FFF","border": "none","cursor": "pointer","font-size": "14px","font-family": "Arial, sans-serif","border-radius": "5px"})
marker_menu = html.Div([dbc.Row(dbc.Stack([html.Label('Activate Markers',style={'fontWeight':'bold','margin-right':'10px'}),daq.BooleanSwitch(id='activate-marker',on=False)],direction="horizontal",gap=0.5,style={'padding':'5px 20px','margin-bottom':'5px'}),justify='center'),dbc.Row([marker_btn],justify='center')],style={'border':'1px solid #d6d6d6','border-radius':'10px','padding':'10px','margin-bottom':'10px'})

minimize_suspectTable_radiated_btn = html.Div([dbc.Row(html.Button('Hide Suspect Table',id='minimize_suspectTable_radiated_btn',n_clicks=1,style={'width':'230px','height':'50px',"padding": "15px","background-color": "#1F3A68","color": "#FFF","border": "none","cursor": "pointer","font-size": "14px","font-family": "Arial, sans-serif","border-radius": "5px"}),justify='center')],style={'border':'1px solid #d6d6d6','border-radius':'10px','padding':'10px','margin-bottom':'10px'})

log_btn_ground = html.Div([html.Label('Ground Graph',style={'fontWeight':'bold','margin-left':'20px','margin-bottom':'5px'}),html.Label('X axis Scale',style={'fontWeight':'bold','margin-left':'20px','margin-bottom':'5px'}),dcc.RadioItems(id='xaxis-emission_ground',options=[{'label':' Logarithmic','value':'log'},{'label':' Linear','value':'linear'}],value='log',inline=True,labelStyle={'fontWeight':'bold','margin-right':'10px','margin-bottom':'10px'},className='radio-item-spacing')])
input_x_min_max_ground = html.Div([dbc.Row(html.Label('X axis limits',style={'fontWeight':'bold','margin-left':'20px','margin-bottom':'5px'})),
                            dbc.Row([dbc.Col([dbc.Stack([html.Label('Min',style={'fontWeight':'bold'}),dcc.Input(id='input_x_min-emission_ground',type='number',value=None,debounce = True,style={'width':'75px', 'textAlign':'center'})],direction="horizontal",gap=2)]),dbc.Col([dbc.Stack([html.Label('Max',style={'fontWeight':'bold'}),dcc.Input(id='input_x_max-emission_ground',type='number',value=None,debounce = True,style={'width':'75px', 'textAlign':'center'})],direction="horizontal",gap=2)])],className="g-0",style={'margin-bottom':'10px'})])
input_y_min_max_ground = html.Div([dbc.Row(html.Label('Y axis limits',style={'fontWeight':'bold','margin-left':'20px','margin-bottom':'5px'})),
                            dbc.Row([dbc.Col([dbc.Stack([html.Label('Min',style={'fontWeight':'bold'}),dcc.Input(id='input_y_min-emission_ground',type='number',value=None,debounce = True,style={'width':'75px', 'textAlign':'center'})],direction="horizontal",gap=2)]),dbc.Col([dbc.Stack([html.Label('Max',style={'fontWeight':'bold'}),dcc.Input(id='input_y_max-emission_ground',type='number',value=None,debounce = True,style={'width':'75px', 'textAlign':'center'})],direction="horizontal",gap=2)])],className="g-0")])

limits_table_ground = dag.AgGrid(
        id="limits-table-ground",
        rowData=[],
        columnDefs=columnDefs_limits,
        dashGridOptions={"rowDragManaged": True,
                         "rowDragEntireRow": True,
                         "rowSelection": "multiple",
                         "suppressMoveWhenRowDragging": True,
                         "isRowSelectable": {'function': "params.data.disabled == 'False'"}},
        defaultColDef={'resizable': True},
        style={'center':True,'fontSize':'12px','height':'300px','width':'100%'})

line_table_ground = dag.AgGrid(
        id="line-table-ground",
        rowData=[],
        columnDefs=columnDefs_line,
        dashGridOptions={"rowDragManaged": True,
                         "rowDragEntireRow": True,
                         "rowSelection": "multiple",
                         "suppressMoveWhenRowDragging": True},
        defaultColDef={'resizable': True, "filter": "agTextColumnFilter"},
        style={'center':True,'fontSize':'12px','height':'300px','width':'100%'})

line_table_Div_ground = html.Div([dbc.Stack([limits_table_ground, line_table_ground,],gap=2)],id='line-table-container-ground',style={'width':800,'display':'none','position':'fixed','top':'20%','right':'23%','bg-color':'rgba(255,255,255,0.95)','padding':'10px 10px','boxShadow':'0px 4px 8px rgba(0,0,0,0.1)','zIndex':'1002','borderRadius':'8px','overflow':'auto'})

line_table_btn_ground = html.Button('Show Line Display Parameters',id='line-table-btn-ground',n_clicks=0,style={'width':'230px','height':'50px',"padding": "15px","background-color": "#1F3A68","color": "#FFF","border": "none","cursor": "pointer","font-size": "14px","font-family": "Arial, sans-serif","border-radius": "5px"})

line_menu_ground = html.Div([dbc.Row((line_table_btn_ground),justify='center')],style={'padding':'10px'})

cursor_params = html.Div([
    dbc.Stack([html.Label('Activate cursors : ', style={'font-weight':'bold','font-size':18, 'marginRight':5}),daq.BooleanSwitch(id='activate_cursors_conducted_ground', on=False)], direction='horizontal', style={'margin-bottom':10, 'margin-top':10}),
], style={'marginBottom':10})

cursor_left = html.Div([
    html.H2("Cursors left", style={"font-size": "18px", "margin-left": "10px","font-weight": "bold", "font-family": "Arial, sans-serif"}),
    dbc.Stack([html.Label('Source : ', style={'font-weight':'bold','font-size':16, 'marginRight':5}), dcc.Dropdown(id='trace_cursor_left_conducted_ground', options=[], clearable=False, style={'width':370})], direction='horizontal', style={'margin-bottom':10}),
    dbc.Stack([html.Label('Position : ', style={'font-weight':'bold','font-size':16, 'marginRight':5}), dcc.Input(id='position_cursor_left_conducted_ground', type='number', value=None)], direction='horizontal')
], style={"margin-bottom": "10px"})

cursor_right = html.Div([
    html.H2("Cursors right", style={"font-size": "18px", "margin-left": "10px","font-weight": "bold", "font-family": "Arial, sans-serif"}),
    dbc.Stack([html.Label('Source: ', style={'font-weight':'bold','font-size':16, 'marginRight':5}), dcc.Dropdown(id='trace_cursor_right_conducted_ground', options=[], clearable=False, style={'width':370})], direction='horizontal', style={'margin-bottom':10}),
    dbc.Stack([html.Label('Position: ', style={'font-weight':'bold','font-size':16, 'marginRight':5}), dcc.Input(id='position_cursor_right_conducted_ground', type='number', value=None)], direction='horizontal')
], style={"margin-bottom": "10px"})

cursors_result = html.Div([
    html.H2("Cursors result", style={"font-size": "18px", "margin-left": "10px","font-weight": "bold", "font-family": "Arial, sans-serif"}),
    dbc.Stack([html.Label('Δx: ', id='Δx_conducted_ground', style={'font-weight':'bold','font-size':16, 'margin-right':50}), html.Label('1/Δx: ', id='1/Δx_conducted_ground', style={'font-weight':'bold','font-size':16})], direction='horizontal', style={'margin-bottom':10}),
    dbc.Stack([html.Label('Δy: ', id='Δy_conducted_ground', style={'font-weight':'bold','font-size':16, 'margin-right':50}), html.Label('Δy/Δx: ', id='Δy/Δx_conducted_ground', style={'font-weight':'bold','font-size':16})], direction='horizontal')
], style={"margin-bottom": "10px"})

cursor_menu_conducted_ground = html.Div([
    dbc.Stack([html.Label('Cursors direction : ', style={'font-weight': 'bold', 'font-size': 18, 'marginRight': 5}), dcc.RadioItems(id='cursors_direction_conducted_ground', options=['Vertical', 'Horizontal'], value='Vertical', inline=True, labelStyle={"margin": "1rem"}, inputStyle={"margin-right": "5px"})], direction='horizontal'),
    cursor_left,
    cursor_right,
    cursors_result
], id='cursor_menu_conducted_ground', style={'display':'none'})

ground_parameters_menu_conducted = html.Div([dbc.Stack([log_btn_ground,input_x_min_max_ground,input_y_min_max_ground, cursor_params, cursor_menu_conducted_ground, line_menu_ground], gap = 1)],id='Div_axes_param_ground',style={'border':'1px solid #d6d6d6','border-radius':'10px','padding':'10px','margin-bottom':'10px', 'display':'none'})

log_btn_supply = html.Div([html.Label('Supply Graph',style={'fontWeight':'bold','margin-left':'20px','margin-bottom':'5px'}),html.Label('X axis Scale',style={'fontWeight':'bold','margin-left':'20px','margin-bottom':'5px'}),dcc.RadioItems(id='xaxis-emission_supply',options=[{'label':' Logarithmic','value':'log'},{'label':' Linear','value':'linear'}],value='log',inline=True,labelStyle={'fontWeight':'bold','margin-right':'10px','margin-bottom':'10px'},className='radio-item-spacing')])
input_x_min_max_supply = html.Div([dbc.Row(html.Label('X axis limits',style={'fontWeight':'bold','margin-left':'20px','margin-bottom':'5px'})),
                            dbc.Row([dbc.Col([dbc.Stack([html.Label('Min',style={'fontWeight':'bold'}),dcc.Input(id='input_x_min-emission_supply',type='number',value=None,debounce = True,style={'width':'75px', 'textAlign':'center'})],direction="horizontal",gap=2)]),dbc.Col([dbc.Stack([html.Label('Max',style={'fontWeight':'bold'}),dcc.Input(id='input_x_max-emission_supply',type='number',value=None,debounce = True,style={'width':'75px', 'textAlign':'center'})],direction="horizontal",gap=2)])],className="g-0",style={'margin-bottom':'10px'})])
input_y_min_max_supply = html.Div([dbc.Row(html.Label('Y axis limits',style={'fontWeight':'bold','margin-left':'20px','margin-bottom':'5px'})),
                            dbc.Row([dbc.Col([dbc.Stack([html.Label('Min',style={'fontWeight':'bold'}),dcc.Input(id='input_y_min-emission_supply',type='number',value=None,debounce = True,style={'width':'75px', 'textAlign':'center'})],direction="horizontal",gap=2)]),dbc.Col([dbc.Stack([html.Label('Max',style={'fontWeight':'bold'}),dcc.Input(id='input_y_max-emission_supply',type='number',value=None,debounce = True,style={'width':'75px', 'textAlign':'center'})],direction="horizontal",gap=2)])],className="g-0")])

cursor_params = html.Div([
    dbc.Stack([html.Label('Activate cursors : ', style={'font-weight':'bold','font-size':18, 'marginRight':5}),daq.BooleanSwitch(id='activate_cursors_conducted_supply', on=False)], direction='horizontal', style={'margin-bottom':10, 'margin-top':10}),
], style={'marginBottom':10})

cursor_left = html.Div([
    html.H2("Cursors left", style={"font-size": "18px", "margin-left": "10px","font-weight": "bold", "font-family": "Arial, sans-serif"}),
    dbc.Stack([html.Label('Source : ', style={'font-weight':'bold','font-size':16, 'marginRight':5}), dcc.Dropdown(id='trace_cursor_left_conducted_supply', options=[], clearable=False, style={'width':370})], direction='horizontal', style={'margin-bottom':10}),
    dbc.Stack([html.Label('Position : ', style={'font-weight':'bold','font-size':16, 'marginRight':5}), dcc.Input(id='position_cursor_left_conducted_supply', type='number', value=None)], direction='horizontal')
], style={"margin-bottom": "10px"})

cursor_right = html.Div([
    html.H2("Cursors right", style={"font-size": "18px", "margin-left": "10px","font-weight": "bold", "font-family": "Arial, sans-serif"}),
    dbc.Stack([html.Label('Source: ', style={'font-weight':'bold','font-size':16, 'marginRight':5}), dcc.Dropdown(id='trace_cursor_right_conducted_supply', options=[], clearable=False, style={'width':370})], direction='horizontal', style={'margin-bottom':10}),
    dbc.Stack([html.Label('Position: ', style={'font-weight':'bold','font-size':16, 'marginRight':5}), dcc.Input(id='position_cursor_right_conducted_supply', type='number', value=None)], direction='horizontal')
], style={"margin-bottom": "10px"})

cursors_result = html.Div([
    html.H2("Cursors result", style={"font-size": "18px", "margin-left": "10px","font-weight": "bold", "font-family": "Arial, sans-serif"}),
    dbc.Stack([html.Label('Δx: ', id='Δx_conducted_supply', style={'font-weight':'bold','font-size':16, 'margin-right':50}), html.Label('1/Δx: ', id='1/Δx_conducted_supply', style={'font-weight':'bold','font-size':16})], direction='horizontal', style={'margin-bottom':10}),
    dbc.Stack([html.Label('Δy: ', id='Δy_conducted_supply', style={'font-weight':'bold','font-size':16, 'margin-right':50}), html.Label('Δy/Δx: ', id='Δy/Δx_conducted_supply', style={'font-weight':'bold','font-size':16})], direction='horizontal')
], style={"margin-bottom": "10px"})

cursor_menu_conducted_supply = html.Div([
    dbc.Stack([html.Label('Cursors direction : ', style={'font-weight': 'bold', 'font-size': 18, 'marginRight': 5}), dcc.RadioItems(id='cursors_direction_conducted_supply', options=['Vertical', 'Horizontal'], value='Vertical', inline=True, labelStyle={"margin": "1rem"}, inputStyle={"margin-right": "5px"})], direction='horizontal'),
    cursor_left,
    cursor_right,
    cursors_result
], id='cursor_menu_conducted_supply', style={'display':'none'})

limits_table_supply = dag.AgGrid(
        id="limits-table-supply",
        rowData=[],
        columnDefs=columnDefs_limits,
        dashGridOptions={"rowDragManaged": True,
                         "rowDragEntireRow": True,
                         "rowSelection": "multiple",
                         "suppressMoveWhenRowDragging": True,
                         "isRowSelectable": {'function': "params.data.disabled == 'False'"}},
        defaultColDef={"rowDragManaged": True,
                "rowDragEntireRow": True,
                "rowSelection": "multiple",
                "suppressMoveWhenRowDragging": True, "filter": "agTextColumnFilter"},
        style={'center':True,'fontSize':'12px','height':'300px','width':'100%'})

line_table_supply = dag.AgGrid(
        id="line-table-supply",
        rowData=[],
        columnDefs=columnDefs_line,
        dashGridOptions={"rowDragManaged": True,
                         "rowDragEntireRow": True,
                         "rowSelection": "multiple",
                         "suppressMoveWhenRowDragging": True},
        defaultColDef={"rowDragManaged": True,
                "rowDragEntireRow": True,
                "rowSelection": "multiple",
                "suppressMoveWhenRowDragging": True, "filter": "agTextColumnFilter"},
        style={'center':True,'fontSize':'12px','height':'300px','width':'100%'})

line_table_Div_supply = html.Div([dbc.Stack([limits_table_supply, line_table_supply],gap=2)],id='line-table-container-supply',style={'width':800,'display':'none','position':'fixed','top':'20%','right':'23%','bg-color':'rgba(255,255,255,0.95)','padding':'10px 10px','boxShadow':'0px 4px 8px rgba(0,0,0,0.1)','zIndex':'1002','borderRadius':'8px','overflow':'auto'})

line_table_btn_supply = html.Button('Show Line Display Parameters',id='line-table-btn-supply',n_clicks=0,style={'width':'230px','height':'50px',"padding": "15px","background-color": "#1F3A68","color": "#FFF","border": "none","cursor": "pointer","font-size": "14px","font-family": "Arial, sans-serif","border-radius": "5px"})

line_menu_supply = html.Div([dbc.Row((line_table_btn_supply),justify='center')],style={'padding':'10px'})

supply_parameters_menu_conducted = html.Div([dbc.Stack([log_btn_supply,input_x_min_max_supply,input_y_min_max_supply, cursor_params, cursor_menu_conducted_supply, line_menu_supply], gap = 1)],id='Div_axes_param_supply',style={'border':'1px solid #d6d6d6','border-radius':'10px','padding':'10px','margin-bottom':'10px', 'display':'none'})

marker_btn_conducted = html.Button('Clear Markers',id='clear_markers_btn_conducted',n_clicks=0,style={'width':'230px','height':'50px',"padding": "15px","background-color": "#1F3A68","color": "#FFF","border": "none","cursor": "pointer","font-size": "14px","font-family": "Arial, sans-serif","border-radius": "5px"})
marker_menu_conducted = html.Div([dbc.Row(dbc.Stack([html.Label('Activate Markers',style={'fontWeight':'bold','margin-right':'10px'}),daq.BooleanSwitch(id='activate-marker-conducted',on=True)],direction="horizontal",gap=0.5,style={'padding':'5px 20px','margin-bottom':'5px'}),justify='center'),dbc.Row([marker_btn_conducted],justify='center')],style={'border':'1px solid #d6d6d6','border-radius':'10px','padding':'10px','margin-bottom':'10px'})

minimize_suspectTable_conducted_btn = html.Div([dbc.Row(html.Button('Hide Suspect Table',id='minimize_suspectTable_conducted_btn',n_clicks=1,style={'width':'230px','height':'50px',"padding": "15px","background-color": "#1F3A68","color": "#FFF","border": "none","cursor": "pointer","font-size": "14px","font-family": "Arial, sans-serif","border-radius": "5px"}),justify='center')],style={'border':'1px solid #d6d6d6','border-radius':'10px','padding':'10px','margin-bottom':'10px'})




sidebar_div = html.Div(id="sidebar", style=sidebar_style, children=[
        html.H2("Graph Parameters", style={"font-size": "24px", "margin-bottom": "20px", "font-weight": "bold", "font-family": "Arial, sans-serif"}),
        html.Hr(style={"border-color": "#BDC3C7"}),  # Light gray line

        # Emission Results Button
        html.Button("Radiated Electric", id="radiated-btn", style=button_style, disabled=True),

        # Emission Results Submenu
        html.Div(id="radiated-electric-submenu", children=[
            dbc.Stack([horizontal_parameters_menu, vertical_parameters_menu, minimize_suspectTable_radiated_btn], gap=1)
        ], style=submenu_style),

        # Immunity Button
        html.Button("Conducted Voltage", id="conducted-btn", style=button_style, disabled=True),

        # Immunity Submenu
        html.Div(id="conducted-voltage-submenu", children=[
            dbc.Stack([ground_parameters_menu_conducted, supply_parameters_menu_conducted, minimize_suspectTable_conducted_btn], gap=1)
        ], style=submenu_style),
    ])

project = dbc.Stack([
                html.Div(dcc.Dropdown(placeholder="Select a project",id='Project-list',options=[],style={'width':'500px'})),
                html.Div(dcc.Upload(id='load-project',children=[html.Button('Load a project',id='Load-project',n_clicks=0,style={'width':'150px','borderRadius':'5px'})])),
                html.Div(html.Button('Remove a project',id='Remove-project',n_clicks=0,style={'width':'150px','borderRadius':'5px'})),
                html.Div(dbc.Button(id='project-loading-screen', children=['No loaded project'],disabled=True, style = {'width':'270px', 'borderRadius':'5px', 'border':'none','align-items':'center', 'font-weight':'bold', 'backgroundColor':'#119DFF'}))
            ],direction="horizontal",gap=3,style={'margin-left':'30px','align-items':'center'})

limits = dbc.Stack([
                html.Div(dcc.Upload(id='load-limits', accept='.txt,.csv,.xlsx',children=[html.Button('Load limits',id='Load-limit',n_clicks=0,style={'width':'150px','borderRadius':'5px'})])),
                html.Div(dbc.Button(id='limits-loading-screen', children=['No limits selected'],disabled=True, style = {'width':'270px', 'borderRadius':'5px', 'border':'none','align-items':'center', 'font-weight':'bold', 'backgroundColor':'#119DFF'}))
            ],direction="horizontal",gap=3,style={'margin-left':'200px','align-items':'center'})

project_limits = dbc.Row([dbc.Col(project), dbc.Col(limits)],style={'margin-bottom':'20px'})


radiated_table = dag.AgGrid(
        id="radiated_table",
        rowData=[],
        columnDefs=columnDefs_tests,
        defaultColDef={'resizable': True},
        getRowStyle=getRowStyle_test,
        style={'width':'100%','center':True},
        dangerously_allow_code=True,
        dashGridOptions={"rowSelection": "multiple", "suppressRowClickSelection": True, "animateRows": False,"domLayout": "autoHeight", "overlayNoRowsTemplate": "Select a project","rowDragManaged": True, "rowDragEntireRow": True, "suppressMoveWhenRowDragging": True, 'suppressRowTransform': True})

radiated_horizontal=dcc.Loading([dcc.Graph(id='emission_radiated_horizontal',
                                           figure=go.Figure( data=[], layout=emission_h_layout),
                                           config={'toImageButtonOptions': {'filename':'EmissionWithBand_EMC_chart_screenshot'}, 'responsive':True, 'displaylogo':False, 'editable':True, 'edits': {'annotationTail':False, 'annotationText':True, 'axisTitleText':False, 'colorbarPosition':False, 'colorbarTitleText':False, 'legendPosition':False, 'legendText':False, 'shapePosition':False, 'titleText':False}, 'modeBarButtonsToRemove': ['zoom', 'pan','zoomin','zoomout','autoscale','resetscale','lasso2d', 'select2d']},
                                           style={'height': '600px','width':'100%','fontWeight':'bold', 'display':'none'})],
                                id='loading-emission_horizontal', overlay_style={"visibility":"unvisible", "filter": "blur(2px)"},type="circle", display= 'hide')

radiated_vertical=dcc.Loading([dcc.Graph(id='emission_radiated_vertical',
                                         figure=go.Figure( data=[], layout=emission_v_layout),
                                         config={'toImageButtonOptions': {'filename':'EmissionWithBand_EMC_chart_screenshot'}, 'responsive':True, 'displaylogo':False, 'editable':True, 'edits': {'annotationTail':False, 'annotationText':True, 'axisTitleText':False, 'colorbarPosition':False, 'colorbarTitleText':False, 'legendPosition':False, 'legendText':False, 'shapePosition':False, 'titleText':False}, 'modeBarButtonsToRemove': ['zoom', 'pan','zoomin','zoomout','autoscale','resetscale','lasso2d', 'select2d']},
                                         style={'height': '600px','width':'100%','fontWeight':'bold', 'display':'none'})],
                              id='loading-emission_vertical',overlay_style={"visibility":"visible", "filter": "blur(2px)"},type="circle", display= 'hide')

suspectTable_radiated = dag.AgGrid(
        id = "suspectsTable-radiated",
        rowData = [],
        columnDefs = columnDefs_suspectTable,
        getRowStyle=getRowStyle_suspect,
        defaultColDef = {'resizable': True},
        style = {'width':'100%','center':True, 'display':'block'},
        dashGridOptions = {"rowSelection": "multiple", "suppressRowClickSelection": True, "animateRows": False,"domLayout": "autoHeight", "rowDragManaged": True,
                "rowDragEntireRow": True,
                "suppressMoveWhenRowDragging": True,
                "isRowSelectable": {'function': "params.data.disabled == 'False'"}})

emission_tab=html.Div([dbc.Stack([radiated_table, radiated_horizontal, radiated_vertical, suspectTable_radiated], gap=3, style={'height': '100%','width':'100%','border':'1px solid #d6d6d6','border-top':'none','margin-top':'-20px', 'padding':'10px'})])



conducted_table = dag.AgGrid(
        id="conducted_table",
        rowData=[],
        columnDefs=columnDefs_tests,
        defaultColDef={'resizable': True},
        getRowStyle=getRowStyle_test,
        style={'width':'100%','center':True},
        dangerously_allow_code=True,
        dashGridOptions={"rowSelection": "multiple", "suppressRowClickSelection": True, "animateRows": False,"domLayout": "autoHeight", "overlayNoRowsTemplate": "Select a project","rowDragManaged": True, "rowDragEntireRow": True, "suppressMoveWhenRowDragging": True, 'suppressRowTransform': True})

conducted_ground=dcc.Loading([dcc.Graph(id='conducted_ground',
                                           figure=go.Figure( data=[], layout=emission_h_layout),
                                           config={'toImageButtonOptions': {'filename':'EmissionWithBand_EMC_chart_screenshot'}, 'responsive':True, 'displaylogo':False, 'editable':True, 'edits': {'annotationTail':False, 'annotationText':True, 'axisTitleText':False, 'colorbarPosition':False, 'colorbarTitleText':False, 'legendPosition':False, 'legendText':False, 'shapePosition':False, 'titleText':False}, 'modeBarButtonsToRemove': ['zoom', 'pan','zoomin','zoomout','autoscale','resetscale','lasso2d', 'select2d']},
                                           style={'height': '600px','width':'100%','fontWeight':'bold', 'display':'none'})],
                                id='loading-ground', overlay_style={"visibility":"unvisible", "filter": "blur(2px)"},type="circle", display= 'hide')

conducted_supply=dcc.Loading([dcc.Graph(id='conducted_supply',
                                         figure=go.Figure( data=[], layout=emission_v_layout),
                                         config={'toImageButtonOptions': {'filename':'EmissionWithBand_EMC_chart_screenshot'}, 'responsive':True, 'displaylogo':False, 'editable':True, 'edits': {'annotationTail':False, 'annotationText':True, 'axisTitleText':False, 'colorbarPosition':False, 'colorbarTitleText':False, 'legendPosition':False, 'legendText':False, 'shapePosition':False, 'titleText':False}, 'modeBarButtonsToRemove': ['zoom', 'pan','zoomin','zoomout','autoscale','resetscale','lasso2d', 'select2d']},
                                         style={'height': '600px','width':'100%','fontWeight':'bold', 'display':'none'})],
                              id='loading-supply',overlay_style={"visibility":"visible", "filter": "blur(2px)"},type="circle", display= 'hide')

suspectTable_conducted = dag.AgGrid(
        id = "suspectsTable-conducted",
        rowData = [],
        columnDefs = columnDefs_suspectTable,
        getRowStyle=getRowStyle_suspect,
        defaultColDef = {'resizable': True},
        style = {'width':'100%','center':True, 'display':'block'},
        dashGridOptions = {"rowSelection": "multiple", "suppressRowClickSelection": True, "animateRows": False,"domLayout": "autoHeight", "rowDragManaged": True,
                "rowDragEntireRow": True,
                "suppressMoveWhenRowDragging": True,
                "isRowSelectable": {'function': "params.data.disabled == 'False'"}})

conducted_tab=html.Div([dbc.Stack([conducted_table, conducted_ground, conducted_supply, suspectTable_conducted], gap=3, style={'height': '100%','width':'100%','border':'1px solid #d6d6d6','border-top':'none','margin-top':'-20px', 'padding':'10px'})])

tabs = dcc.Tabs(id='tabs',value='radiated_tab', children=[
        dcc.Tab(id='radiated_tab', label='Emission - Radiated Electric',disabled=True,children=emission_tab,style={'font-size':18,'font-weight': 'bold'},selected_style={'font-size':18,'font-weight': 'bold'}),
        dcc.Tab(id='conducted_tab', label='Emission - Conducted Voltage',disabled=True,children = conducted_tab ,style={'font-size':18,'font-weight': 'bold'},selected_style={'font-size':18,'font-weight': 'bold'}),
    ],style={'padding':'20px 0px'})
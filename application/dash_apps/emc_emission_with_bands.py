import dash
from dash import dcc, ctx, html, Input, Output, State, no_update
from dash.exceptions import PreventUpdate
import pandas as pd
import base64
import tempfile
import math
import numpy as np
import pymysql
from sqlalchemy import create_engine, text
from application.dash_apps.assets.layout_emc_emission_with_bands import *

from application import server, db, session
from application.log_events import log_event
from application.models import emc_emission_with_bands_limits


project_connection = {}
selected_data = {}
suspect_data = {}

limit_engine = create_engine(
    'mysql+pymysql://root:password@localhost:3306/emc_lab_database',
     pool_recycle = 3600
)

def get_limit_data(limit):

    try:

        query = emc_emission_with_bands_limits.query.filter_by(limit_name=limit)
        sql_statement = query.statement
        data = pd.read_sql(sql_statement, limit_engine)

        return data
    except:
        print('Limit not found')
        return None

def init_app(server):

    app = dash.Dash(__name__, server=server, routes_pathname_prefix='/emc_emission_with_bands_app/', assets_folder='assets', external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=False, prevent_initial_callbacks = True)

    app.layout = (html.Div([
        sidebar_button,
        sidebar_div,

        html.Div(
            [
                project_limits,
                tabs,
            ], style={'flex': '1', 'padding': '20px'}),
        line_table_Div_h,
        line_table_Div_v,
        line_table_Div_ground,
        line_table_Div_supply,
    ],
    ),
                  dcc.Store(id='hide-button', data=None),
                  dcc.Store(id='action_radiated', data='start'),
                  dcc.Store(id='action_conducted', data='start'),
                  dcc.Store(id='cursor_data', data={'radiated horizontal': {'left': {}, 'right': {}},
                                                    'radiated vertical': {'left': {}, 'right': {}},
                                                    'conducted ground': {'left': {}, 'right': {}},
                                                    'conducted supply': {'left': {}, 'right': {}}}),
    )

    @app.callback(Output('Project-list', 'options', allow_duplicate=True),
                  # Output('load-project', 'filename'),
                  Output('project-loading-screen', 'children', allow_duplicate=True),
                  Output('project-loading-screen', 'style', allow_duplicate=True),
                  Input('load-project', 'filename'),
                  Input('load-project', 'contents'),
                  Input('Remove-project', 'n_clicks'),
                  State('Project-list', 'value'),
                  State('Project-list', 'options'),
                  State('project-loading-screen', 'style'),
                  prevent_initial_call=True)
    def update_project_list(project_path, project_content, remove_click, value, options, loading_style):
        triggered_id = ctx.triggered_id

        if triggered_id == 'load-project':
            return add_project(project_path, project_content, options, loading_style)

        elif triggered_id == 'Remove-project' and value is not None:
            return remove_project(value, options, loading_style)

    def add_project(filename, content, options, loading_style):
        if filename.endswith('.db'):
            try:
                project_name = filename.split('.')[0]

                options.append(project_name)

                content_type, content_string = content.split(',')
                decoded = base64.b64decode(content_string)

                with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
                    tmp.write(decoded)
                    tmp.flush()
                    tmp.close()
                    tmp_path = tmp.name

                # conn = sqlite3.connect(tmp_path)

                project_connection[project_name] = create_engine(f"sqlite:///{tmp_path}")

                selected_data[project_name] = {'radiated': {}, 'conducted': {}}
                suspect_data[project_name] = {'radiated': None, 'conducted': None}

                # test_infos = pd.read_sql_query("SELECT * FROM 'Test Infos'", conn)
                # scan_settings = pd.read_sql_query("SELECT * FROM 'Scan settings'", conn)
                # suspects_table = pd.read_sql_query("SELECT * FROM 'Suspects Table'", conn)
                #
                # for index, test in test_infos.iterrows():
                #     source_file = test['source_file']
                #     if test['Type'] == 'Radiated Electric Emissions':
                #         data[project_name]['radiated']['test_infos'] = test_infos.to_json()
                #         data[project_name]['radiated'][source_file] = {'data': None, 'scan_settings': scan_settings[scan_settings['source_file'] == source_file].to_json(), 'suspects_table': suspects_table[suspects_table['source_file'] == source_file].to_json()}
                #
                #     elif test['Type'] == 'Conducted Electric Emissions':
                #         data[project_name]['conducted']['test_infos'] = test_infos.to_json()
                #         data[project_name]['conducted'][source_file] = {'test_infos': test_infos.to_json(), 'data': None, 'scan_settings': scan_settings[scan_settings['source_file'] == source_file].to_json(), 'suspects_table': suspects_table[suspects_table['source_file'] == source_file].to_json()}

                loading_style['backgroundColor'] = 'green'
                return options, [check, '  Project successfully loaded'], loading_style

            except:

                loading_style['backgroundColor'] = 'red'
                return no_update, [cross, 'Failed to process file'], loading_style

        else:
            loading_style['backgroundColor'] = 'red'
            return no_update, [cross, 'Wrong file format'], loading_style

    def remove_project(value, options, loading_style):
        try:
            if value:
                options.remove(value)
                project_connection.pop(value)
                selected_data.pop(value)
                suspect_data.pop(value)

                return options, [check, '  Project successfully removed'], loading_style
            else:
                loading_style['backgroundColor'] = 'red'
                return no_update, [cross, 'No project selected'], loading_style
        except:
            loading_style['backgroundColor'] = 'red'
            return no_update, [cross, 'Failed to remove project'], loading_style

    @app.callback(Output('radiated_table', 'rowData', allow_duplicate=True),
                  Output('conducted_table', 'rowData', allow_duplicate=True),
                  Output('radiated_tab', 'disabled', allow_duplicate=True),
                  Output('conducted_tab', 'disabled', allow_duplicate=True),
                  Output('tabs', 'value', allow_duplicate=True),
                  Input('Project-list', 'value'),
                  prevent_initial_call=True)
    def project(project):

        if project:
            conn = project_connection[project]

            test_info = pd.read_sql_query("SELECT * FROM 'Test Infos'", conn)

            if 'Radiated Electric Emissions' in test_info['Type'].values:
                radiated_table_rowData = test_info[test_info['Type'] == 'Radiated Electric Emissions'].sort_values(
                    by='source_file')
                radiated_table_rowData.rename(columns={"Passed/Failed": "Passed_Failed"}, inplace=True)
                radiated_table_rowData['Show'] = '>>'
                radiated_table_rowData = radiated_table_rowData.to_dict('records')
                radiated_tab = False
            else:
                radiated_table_rowData = []
                radiated_tab = True

            if 'Conducted Electric Emissions' in test_info['Type'].values:
                conducted_table_rowData = test_info[test_info['Type'] == 'Conducted Electric Emissions']
                conducted_table_rowData['Show'] = '>>'
                conducted_table_rowData = conducted_table_rowData.to_dict('records')
                conducted_tab = False
            else:
                conducted_table_rowData = []
                conducted_tab = True

        else:
            radiated_table_rowData = []
            radiated_tab = True
            conducted_table_rowData = []
            conducted_tab = True

        return radiated_table_rowData, conducted_table_rowData, radiated_tab, conducted_tab, None

    @app.callback(Output('radiated_table', 'rowData', allow_duplicate=True),
                  Output('conducted_table', 'rowData', allow_duplicate=True),
                  Output('radiated_table', 'columnDefs', allow_duplicate=True),
                  Output('conducted_table', 'columnDefs', allow_duplicate=True),
                  Output('radiated_table', 'selectedRows', allow_duplicate=True),
                  Output('conducted_table', 'selectedRows', allow_duplicate=True),
                  Output('hide-button', "data", allow_duplicate=True),
                  Input('radiated_table', 'cellRendererData'),
                  Input('conducted_table', 'cellRendererData'),
                  Input('hide-button', "data"),
                  State('radiated_table', 'columnDefs'),
                  State('conducted_table', 'columnDefs'),
                  State('radiated_table', 'rowData'),
                  State('conducted_table', 'rowData'),
                  State('Project-list', 'value'),
                  State('tabs', 'value'),
                  prevent_initial_call=True)
    def display_scans(radiated_table_cellRendererData, conducted_table_cellRendererData, hide_button,
                      radiated_table_columnDefs, conducted_table_columnDefs, radiated_table_rowData,
                      conducted_table_rowData, project, tab):
        triggered_id = ctx.triggered_id

        if radiated_table_cellRendererData or conducted_table_cellRendererData:
            conn = project_connection[project]

            if triggered_id == 'radiated_table':
                # if radiated_table_columnDefs == columnDefs_tests:
                radiated_table_columnDefs = columnDefs_scans
                source_file = radiated_table_rowData[radiated_table_cellRendererData['rowIndex']]['source_file']

                if source_file not in selected_data[project]['radiated']:
                    selected_data[project]['radiated'][source_file] = {"ids": []}

                scan_settings = pd.read_sql_query(f"SELECT * FROM 'Scan settings' WHERE source_file = '{source_file}'",
                                                  conn)
                new_rows = []

                for index, scan in scan_settings.iterrows():
                    if ',' in scan['Detectors']:
                        new_row = scan.copy()
                        new_row['Detectors'] = scan['Detectors'].split(',')[1]
                        scan['Detectors'] = scan['Detectors'].split(',')[0]
                        new_rows.append(scan)
                        new_rows.append(new_row)
                    else:
                        new_rows.append(scan)

                radiated_table_rowData = pd.DataFrame(new_rows).reset_index(drop=True).rename(
                    columns={'index': 'id'}).to_dict('records')

                radiated_table_selectedRows = selected_data[project]['radiated'][source_file]

                # else:
                #     radiated_table_columnDefs = columnDefs_tests
                #     test_info = pd.read_sql_query("SELECT * FROM 'Test Infos'", conn)
                #     radiated_table_rowData = test_info[test_info['Type'] == 'Radiated Electric Emissions'].to_dict('records')

                return radiated_table_rowData, no_update, radiated_table_columnDefs, no_update, radiated_table_selectedRows, no_update, False

            elif triggered_id == 'conducted_table':
                # if conducted_table_columnDefs == columnDefs_tests:
                conducted_table_columnDefs = columnDefs_scans
                source_file = conducted_table_rowData[conducted_table_cellRendererData['rowIndex']]['source_file']

                if source_file not in selected_data[project]['conducted']:
                    selected_data[project]['conducted'][source_file] = {"ids": []}

                scan_settings = pd.read_sql_query(f"SELECT * FROM 'Scan settings' WHERE source_file = '{source_file}'",
                                                  conn)
                new_rows = []

                for index, scan in scan_settings.iterrows():
                    if ',' in scan['Detectors']:
                        new_row = scan.copy()
                        new_row['Detectors'] = scan['Detectors'].split(',')[1]
                        scan['Detectors'] = scan['Detectors'].split(',')[0]
                        new_rows.append(scan)
                        new_rows.append(new_row)
                    else:
                        new_rows.append(scan)

                conducted_table_rowData = pd.DataFrame(new_rows).reset_index(drop=True).to_dict('records')

                conducted_table_selectedRows = selected_data[project]['conducted'][source_file]

                # else:
                #     conducted_table_columnDefs = columnDefs_tests
                #     test_info = pd.read_sql_query("SELECT * FROM 'Test Infos'", conn)
                #     conducted_table_rowData = test_info[test_info['Type'] == 'Conducted Electric Emissions'].to_dict('records')

                return no_update, conducted_table_rowData, no_update, conducted_table_columnDefs, no_update, conducted_table_selectedRows, False

            elif triggered_id == 'hide-button':

                test_info = pd.read_sql_query("SELECT * FROM 'Test Infos'", conn).sort_values(by='source_file')

                if tab == 'tab-1':
                    radiated_table_rowData = test_info[test_info['Type'] == 'Radiated Electric Emissions']
                    radiated_table_rowData.rename(columns={"Passed/Failed": "Passed_Failed"}, inplace=True)
                    radiated_table_rowData['Show'] = '>>'
                    radiated_table_rowData = radiated_table_rowData.to_dict('records')

                    radiated_table_columnDefs = columnDefs_tests

                    return radiated_table_rowData, no_update, radiated_table_columnDefs, no_update, {"ids": []}, {
                        "ids": []}, True

                elif tab == 'tab-2':
                    conducted_table_rowData = test_info[test_info['Type'] == 'Conducted Electric Emissions']
                    conducted_table_rowData['Show'] = '>>'
                    conducted_table_rowData = radiated_table_rowData.to_dict('records').to_dict('records')

                    conducted_table_columnDefs = columnDefs_tests

                    return no_update, conducted_table_rowData, no_update, conducted_table_columnDefs, {"ids": []}, {
                        "ids": []}, True

        else:
            raise PreventUpdate

    @app.callback(Output('action_radiated', 'data', allow_duplicate=True),
                  Output('action_conducted', 'data', allow_duplicate=True),
                  Input('radiated_table', 'selectedRows'),
                  Input('conducted_table', 'selectedRows'),
                  State('radiated_table', 'columnDefs'),
                  State('conducted_table', 'columnDefs'),
                  State('radiated_table', 'rowData'),
                  State('conducted_table', 'rowData'),
                  State('radiated_table', 'cellRendererData'),
                  State('conducted_table', 'cellRendererData'),
                  State('Project-list', 'value'),
                  State('hide-button', "data"),
                  prevent_initial_call=True)
    def selected_data_fct(radiated_table_selectedRows, conducted_table_selectedRows, radiated_table_columnDefs,
                          conducted_table_columnDefs, radiated_table_rowData, conducted_table_rowData,
                          radiated_table_cellRendererData, conducted_table_cellRendererData, project, hide_button):
        triggered_id = ctx.triggered_id

        if hide_button == False:

            if triggered_id == 'radiated_table':
                selectedRows = radiated_table_selectedRows
                rowData = radiated_table_rowData
                cellRendererData = radiated_table_cellRendererData
                selected = selected_data[project]['radiated']
            else:
                selectedRows = conducted_table_selectedRows
                rowData = conducted_table_rowData
                cellRendererData = conducted_table_cellRendererData
                selected = selected_data[project]['conducted']
            # if 'ids' in selectedRows and selectedRows != {'ids': []} or 'ids' not in selectedRows and selectedRows != []:

            source_file = rowData[0]['source_file']

            ids = []
            for row in selectedRows['ids'] if 'ids' in selectedRows else selectedRows:
                index = rowData.index(row)
                ids.append(str(index))

            if selected[source_file]['ids'] != ids:

                conn = project_connection[project]

                if triggered_id == 'radiated_table' and radiated_table_columnDefs == columnDefs_scans:

                    action_radiated, action_conducted = 'suspect', no_update

                    suspect_data[project]['radiated'] = pd.DataFrame()
                    selected_data[project]['radiated'][source_file]['ids'] = []

                    for row in radiated_table_selectedRows:
                        # rows = pd.read_sql_query(f"SELECT * FROM 'Scan Settings' WHERE source_file = '{source_file}' AND Scan={row['Scan']} AND Detectors LIKE '%{row['Detectors']}%'", conn)
                        row_index = radiated_table_rowData.index(row)

                        suspects = pd.read_sql_query(
                            f"SELECT * FROM 'Suspects Table' WHERE source_file = '{source_file}' AND Scan={row['Scan']} AND Polarization='{row['Polarization']}' AND Detector = '{row['Detectors']}'",
                            conn)
                        suspects.rename(columns={"Pass/Fail": "Pass_Fail"}, inplace=True)
                        # if suspects not in suspect_data['radiated']:
                        selected_data[project]['radiated'][source_file]['ids'].append(str(row_index))
                        suspect_data[project]['radiated'] = pd.concat([suspect_data[project]['radiated'], suspects],
                                                                      ignore_index=True)

                    # selected_data[project]['radiated'] = selected_data[project]['radiated'].to_json()
                    suspect_data[project]['radiated'] = suspect_data[project]['radiated']

                elif triggered_id == 'conducted_table' and conducted_table_columnDefs == columnDefs_scans:

                    action_radiated, action_conducted = no_update, 'suspect'

                    source_file = conducted_table_rowData[radiated_table_cellRendererData['rowIndex']]['source_file']

                    suspect_data[project]['conducted'] = pd.DataFrame()
                    selected_data[project]['conducted'][source_file]['ids'] = []

                    for row in conducted_table_selectedRows:
                        row_index = conducted_table_rowData.index(row)
                        suspects = pd.read_sql_query(
                            f"SELECT * FROM 'Suspects Table' WHERE source_file = '{source_file}' AND Scan={row['Scan']} AND Detector='{row['Detectors']}'",
                            conn)
                        suspects.rename(columns={"Pass/Fail": "Pass_Fail"}, inplace=True)

                        # if suspects not in suspect_data['conducted']:
                        selected_data[project]['conducted'][source_file]['ids'].append(str(row_index))
                        suspect_data[project]['conducted'] = pd.concat([suspect_data[project]['conducted'], suspects])

                    suspect_data[project]['conducted'] = suspect_data[project]['conducted']

                return action_radiated, action_conducted

        raise PreventUpdate

    @app.callback(Output('emission_radiated_horizontal', 'figure', allow_duplicate=True),
                  Output('emission_radiated_vertical', 'figure', allow_duplicate=True),
                  Output('emission_radiated_horizontal', 'style', allow_duplicate=True),
                  Output('emission_radiated_vertical', 'style', allow_duplicate=True),
                  Output('action_radiated', 'data', allow_duplicate=True),
                  Output('Div_axes_param_h', 'style', allow_duplicate=True),
                  Output('Div_axes_param_v', 'style', allow_duplicate=True),
                  Output('trace_cursor_left_radiated_h', 'options', allow_duplicate=True),
                  Output('trace_cursor_right_radiated_h', 'options', allow_duplicate=True),
                  Output('trace_cursor_left_radiated_h', 'value', allow_duplicate=True),
                  Output('trace_cursor_right_radiated_h', 'value', allow_duplicate=True),
                  Output('trace_cursor_left_radiated_v', 'options', allow_duplicate=True),
                  Output('trace_cursor_right_radiated_v', 'options', allow_duplicate=True),
                  Output('trace_cursor_left_radiated_v', 'value', allow_duplicate=True),
                  Output('trace_cursor_right_radiated_v', 'value', allow_duplicate=True),
                  Output("limits-table-h", 'rowData'),
                  Output("line-table-h", 'rowData'),
                  Output("limits-table-h", 'selectedRows'),
                  Output("limits-table-v", 'rowData'),
                  Output("line-table-v", 'rowData'),
                  Output("limits-table-v", 'selectedRows'),
                  Output('input_x_min-emission_h', 'value'),
                  Output('input_x_max-emission_h', 'value'),
                  Output('input_y_min-emission_h', 'value'),
                  Output('input_y_max-emission_h', 'value'),
                  Output('input_x_min-emission_v', 'value'),
                  Output('input_x_max-emission_v', 'value'),
                  Output('input_y_min-emission_v', 'value'),
                  Output('input_y_max-emission_v', 'value'),
                  Output("suspectsTable-radiated", 'rowData', allow_duplicate=True),
                  Output("suspectsTable-radiated", 'selectedRows', allow_duplicate=True),
                  Output("loading-emission_horizontal", 'display', allow_duplicate=True),
                  Output("loading-emission_vertical", 'display', allow_duplicate=True),
                  Input('action_radiated', 'data'),
                  State('radiated_table', 'selectedRows'),
                  State('hide-button', "data"),
                  State('radiated_table', 'cellRendererData'),
                  State('radiated_table', 'rowData'),
                  State('Project-list', 'value'),
                  State('emission_radiated_horizontal', 'figure'),
                  State('emission_radiated_vertical', 'figure'),
                  State('tabs', 'value'),
                  State("suspectsTable-radiated", 'selectedRows'),
                  State('emission_radiated_horizontal', 'style'),
                  State('emission_radiated_vertical', 'style'),
                  State('Div_axes_param_h', 'style'),
                  State('Div_axes_param_v', 'style'),
                  State("limits-table-h", 'rowData'),
                  State("line-table-h", 'rowData'),
                  State("limits-table-v", 'rowData'),
                  State("line-table-v", 'rowData'),
                  State("suspectsTable-radiated", 'rowData'),
                  prevent_initial_call=True)
    def create_graph_radiated(action, table_selectedRows, hide_data, table_cellRendererData, table_rowData, project,
                              figure_1, figure_2, type, suspectsTable_selectedRows, horizontal_style, vertical_style,
                              Div_axes_param_1, Div_axes_param_2, limit_rowData_1, line_rowData_1, limit_rowData_2,
                              line_rowData_2, suspectsTable_rowData):

        if hide_data == False and action == 'suspect':

            suspectsTable_rowData, suspectsTable_selectedRows = suspect_table(suspectsTable_selectedRows,
                                                                              suspectsTable_rowData, project,
                                                                              'radiated')

            figure_1, figure_2, figure_1_style, figure_2_style, action, Div_axes_param_1, Div_axes_param_2, trace_cursor_left_1, trace_cursor_right_1, trace_cursor_left_1_value, trace_cursor_right_1_value, trace_cursor_left_2, trace_cursor_right_2, trace_cursor_left_2_value, trace_cursor_right_2_value, limit_rowData_1, line_rowData_1, limit_rowData_1, limit_rowData_2, line_rowData_2, limit_rowData_2, x_min_1, x_max_1, y_min_1, y_max_1, x_min_2, x_max_2, y_min_2, y_max_2, loading_1, loading_2 = graphs(
                table_selectedRows, table_cellRendererData, table_rowData, project, figure_1, figure_2, type,
                suspectsTable_selectedRows, horizontal_style, vertical_style, Div_axes_param_1, Div_axes_param_2,
                limit_rowData_1, line_rowData_1, limit_rowData_2, line_rowData_2)

            return figure_1, figure_2, figure_1_style, figure_2_style, action, Div_axes_param_1, Div_axes_param_2, trace_cursor_left_1, trace_cursor_right_1, trace_cursor_left_1_value, trace_cursor_right_1_value, trace_cursor_left_2, trace_cursor_right_2, trace_cursor_left_2_value, trace_cursor_right_2_value, limit_rowData_1, line_rowData_1, limit_rowData_1, limit_rowData_2, line_rowData_2, limit_rowData_2, x_min_1, x_max_1, y_min_1, y_max_1, x_min_2, x_max_2, y_min_2, y_max_2, suspectsTable_rowData, suspectsTable_selectedRows, loading_1, loading_2

        else:
            raise PreventUpdate

    @app.callback(Output('conducted_ground', 'figure', allow_duplicate=True),
                  Output('conducted_supply', 'figure', allow_duplicate=True),
                  Output('conducted_ground', 'style', allow_duplicate=True),
                  Output('conducted_supply', 'style', allow_duplicate=True),
                  Output('action_conducted', 'data', allow_duplicate=True),
                  Output('Div_axes_param_ground', 'style', allow_duplicate=True),
                  Output('Div_axes_param_supply', 'style', allow_duplicate=True),
                  Output('trace_cursor_left_conducted_ground', 'options', allow_duplicate=True),
                  Output('trace_cursor_right_conducted_ground', 'options', allow_duplicate=True),
                  Output('trace_cursor_left_conducted_ground', 'value', allow_duplicate=True),
                  Output('trace_cursor_right_conducted_ground', 'value', allow_duplicate=True),
                  Output('trace_cursor_left_conducted_supply', 'options', allow_duplicate=True),
                  Output('trace_cursor_right_conducted_supply', 'options', allow_duplicate=True),
                  Output('trace_cursor_left_conducted_supply', 'value', allow_duplicate=True),
                  Output('trace_cursor_right_conducted_supply', 'value', allow_duplicate=True),
                  Output("limits-table-ground", 'rowData'),
                  Output("line-table-ground", 'rowData'),
                  Output("limits-table-ground", 'selectedRows'),
                  Output("limits-table-supply", 'rowData'),
                  Output("line-table-supply", 'rowData'),
                  Output("limits-table-supply", 'selectedRows'),
                  Output('input_x_min-emission_ground', 'value'),
                  Output('input_x_max-emission_ground', 'value'),
                  Output('input_y_min-emission_ground', 'value'),
                  Output('input_y_max-emission_ground', 'value'),
                  Output('input_x_min-emission_supply', 'value'),
                  Output('input_x_max-emission_supply', 'value'),
                  Output('input_y_min-emission_supply', 'value'),
                  Output('input_y_max-emission_supply', 'value'),
                  Output("suspectsTable-conducted", 'rowData', allow_duplicate=True),
                  Output("suspectsTable-conducted", 'selectedRows', allow_duplicate=True),
                  Output("loading-ground", 'display', allow_duplicate=True),
                  Output("loading-supply", 'display', allow_duplicate=True),
                  Input('action_conducted', 'data'),
                  State('conducted_table', 'selectedRows'),
                  State('hide-button', "data"),
                  State('conducted_table', 'cellRendererData'),
                  State('conducted_table', 'rowData'),
                  State('Project-list', 'value'),
                  State('conducted_ground', 'figure'),
                  State('conducted_supply', 'figure'),
                  State('tabs', 'value'),
                  State("suspectsTable-conducted", 'selectedRows'),
                  State('conducted_ground', 'style'),
                  State('conducted_supply', 'style'),
                  State('Div_axes_param_ground', 'style'),
                  State('Div_axes_param_supply', 'style'),
                  State("limits-table-ground", 'rowData'),
                  State("line-table-ground", 'rowData'),
                  State("limits-table-supply", 'rowData'),
                  State("line-table-supply", 'rowData'),
                  State("suspectsTable-conducted", 'rowData'),
                  prevent_initial_call=True)
    def create_graph_conducted(action, table_selectedRows, hide_data, table_cellRendererData, table_rowData, project,
                               figure_1, figure_2, type, suspectsTable_selectedRows, horizontal_style, vertical_style,
                               Div_axes_param_1, Div_axes_param_2, limit_rowData_1, line_rowData_1, limit_rowData_2,
                               line_rowData_2, suspectsTable_rowData):

        if hide_data == False and action == 'suspect':
            suspectsTable_rowData, suspectsTable_selectedRows = suspect_table(suspectsTable_selectedRows,
                                                                              suspectsTable_rowData, project,
                                                                              'conducted')

            figure_1, figure_2, figure_1_style, figure_2_style, action, Div_axes_param_1, Div_axes_param_2, trace_cursor_left_1, trace_cursor_right_1, trace_cursor_left_1_value, trace_cursor_right_1_value, trace_cursor_left_2, trace_cursor_right_2, trace_cursor_left_2_value, trace_cursor_right_2_value, limit_rowData_1, line_rowData_1, limit_rowData_1, limit_rowData_2, line_rowData_2, limit_rowData_2, x_min_1, x_max_1, y_min_1, y_max_1, x_min_2, x_max_2, y_min_2, y_max_2, loading_1, loading_2 = graphs(
                table_selectedRows, table_cellRendererData, table_rowData, project, figure_1, figure_2, type,
                suspectsTable_selectedRows, horizontal_style, vertical_style, Div_axes_param_1, Div_axes_param_2,
                limit_rowData_1, line_rowData_1, limit_rowData_2, line_rowData_2)

            return figure_1, figure_2, figure_1_style, figure_2_style, action, Div_axes_param_1, Div_axes_param_2, trace_cursor_left_1, trace_cursor_right_1, trace_cursor_left_1, trace_cursor_right_1, trace_cursor_left_2, trace_cursor_right_2, trace_cursor_left_2, trace_cursor_right_2, limit_rowData_1, line_rowData_1, limit_rowData_1, limit_rowData_2, line_rowData_2, limit_rowData_2, x_min_1, x_max_1, y_min_1, y_max_1, x_min_2, x_max_2, y_min_2, y_max_2, suspectsTable_rowData, suspectsTable_selectedRows, loading_1, loading_2

        else:
            raise PreventUpdate

    def suspect_table(suspectsTable_selectedRows, suspectsTable_rowData, project, type):
        suspects = suspect_data[project][type]
        suspects['disabled'] = 'False'
        suspectsTable_rowData = suspects.to_dict('records')
        not_selectedRows = [str(index) for index, row in enumerate(suspectsTable_selectedRows) if
                            row not in suspectsTable_rowData] if suspectsTable_selectedRows else []
        suspectsTable_selectedRows = []

        for i, row in enumerate(suspectsTable_rowData.copy()):
            if i not in not_selectedRows:
                suspectsTable_selectedRows.append(row)

        return suspectsTable_rowData, suspectsTable_selectedRows

    def graphs(table_selectedRows, table_cellRendererData, table_rowData, project, figure_1, figure_2, type,
               suspectsTable_selectedRows, figure_1_style, figure_2_style, Div_axes_param_1, Div_axes_param_2,
               limit_rowData_1, line_rowData_1, limit_rowData_2, line_rowData_2):

        conn = project_connection[project].connect()

        figure_1 = go.Figure(figure_1)
        figure_2 = go.Figure(figure_2)

        chart_list1 = [item['meta']['name'] for item in figure_1['data'] if item['meta']['type'] == 'line']
        chart_list2 = [item['meta']['name'] for item in figure_2['data'] if item['meta']['type'] == 'line']

        trace_cursor_left_1 = []
        trace_cursor_right_1 = []
        trace_cursor_left_2 = []
        trace_cursor_right_2 = []

        for row in table_rowData:

            if row['Polarization'] == 'Horizontal' or row['Polarization'] == 'Ground':
                figure = figure_1
                chart_list = chart_list1
                line_rowData = line_rowData_1
                limit_rowData = limit_rowData_1

            elif row['Polarization'] == 'Vertical' or row['Polarization'] == 'Supply':
                figure = figure_2
                chart_list = chart_list2
                line_rowData = line_rowData_2
                limit_rowData = limit_rowData_2

            source_file = table_rowData[0]['source_file']
            name_meta = source_file + '-' + str(row["Scan"]) + '-' + row["RBW"] + '-' + row['Detectors']

            name = source_file + '-' + row["Bands"] + '-' + row["RBW"] + '-' + row['Detectors']

            if name_meta not in chart_list and row in table_selectedRows:

                sql = f"SELECT ` Frequency (MHz)` FROM `Data` WHERE source_file = '{source_file}' AND Scan={row['Scan']}"
                x = pd.read_sql_query(sql, conn)[' Frequency (MHz)'].tolist()

                sql = f"SELECT `Meas.{row['Detectors']} (dBµV/m)` FROM `Data` WHERE source_file = '{source_file}' AND Scan={row['Scan']}"
                y = pd.read_sql_query(sql, conn)[f'Meas.{row['Detectors']} (dBµV/m)'].tolist()

                color = detector_to_color_gradient[row['Detectors']][row['RBW']]

                meta = {'name': name_meta, 'project': project, 'source_file': source_file, 'scan': row['Scan'],
                        'Detector': row['Detectors'], 'Bands': row["Bands"].split(','), 'RBW': row["RBW"],
                        'type': 'line', 'Color': color, 'suspects': [], 'limits': [], 'cursors': []}

                figure, meta = plot_suspects(figure, suspectsTable_selectedRows, meta, name_meta)

                limit = \
                pd.read_sql_query(f"SELECT Limits FROM 'Test Infos' WHERE source_file='{source_file}'", conn).iat[0, 0]

                figure, data, limit_rowData = plot_limits(figure, meta, limit, color, name_meta, limit_rowData)

                line_rowData.append({'Name': name, 'Color': 'Green' if row['Detectors'] == 'CAVG' else 'Blue' if row[
                                                                                                                     'Detectors'] == 'Peak' else 'Red',
                                     'Width': 1, 'Type': 'solid'})

                trace = go.Scatter(x=x, y=y, mode='lines', visible=True, name=name,
                                   line=dict(color=color, dash='solid', width=1),
                                   hovertemplate=f'<b>{source_file} - {row["RBW"]} - {row["Detectors"]}</b><br>' + '<b>Frequency (MHz):</b> %{x:.2f}<br>' + '<b>Level (dBµV/m):</b> %{y:.2f} <extra></extra>',
                                   meta=meta)

                figure.add_trace(trace)

                if row['Polarization'] == 'Horizontal' or row['Polarization'] == 'Ground':
                    figure_1 = figure

                elif row['Polarization'] == 'Vertical' or row['Polarization'] == 'Supply':
                    figure_2 = figure

            elif name_meta in chart_list and row not in table_selectedRows:
                figure['data'] = tuple(trace for trace in figure['data'] if
                                       (trace['meta']['type'] == 'line' and trace['meta']['name'] != name_meta) or (
                                                   trace['meta']['type'] == 'suspect' and trace['meta'][
                                               'line'] != name_meta) or (
                                                   trace['meta']['type'] == 'limit' and trace['meta'][
                                               'line'] != name_meta))

                for row in line_rowData.copy():
                    if row['Name'] == name:
                        line_rowData.remove(row)

                for row in limit_rowData.copy():
                    if row['chart'] == name_meta:
                        limit_rowData.remove(row)

        if figure_1['data'] == ():
            figure_1_style['display'] = 'none'
            Div_axes_param_1['display'] = 'none'
            x_min_1, x_max_1, y_min_1, y_max_1 = None, None, None, None

            trace_cursor_left_1_value = None
            trace_cursor_right_1_value = None

            loading_1 = 'hide'

        else:
            figure_1, x_min_1, x_max_1, y_min_1, y_max_1 = set_x_range(figure_1)
            figure_1_style['display'] = 'block'
            Div_axes_param_1['display'] = 'block'

            for row in line_rowData_1:
                trace_cursor_left_1.append(row['Name'])
                trace_cursor_right_1.append(row['Name'])

            trace_cursor_left_1_value = trace_cursor_left_1[0]
            trace_cursor_right_1_value = trace_cursor_right_1[0]

            loading_1 = 'auto'

        if figure_2['data'] == ():
            figure_2_style['display'] = 'none'
            Div_axes_param_2['display'] = 'none'
            x_min_2, x_max_2, y_min_2, y_max_2 = None, None, None, None

            trace_cursor_left_2_value = None
            trace_cursor_right_2_value = None

            loading_2 = 'hide'

        else:
            figure_2, x_min_2, x_max_2, y_min_2, y_max_2 = set_x_range(figure_2)
            figure_2_style['display'] = 'block'
            Div_axes_param_2['display'] = 'block'

            for row in line_rowData_2:
                trace_cursor_left_2.append(row['Name'])
                trace_cursor_right_2.append(row['Name'])

            trace_cursor_left_2_value = trace_cursor_left_2[0]
            trace_cursor_right_2_value = trace_cursor_right_2[0]

            loading_2 = 'auto'
        print(trace_cursor_left_1, trace_cursor_right_1)
        print(trace_cursor_left_1_value, trace_cursor_right_1_value)
        return figure_1, figure_2, figure_1_style, figure_2_style, 'standby', Div_axes_param_1, Div_axes_param_2, trace_cursor_left_1, trace_cursor_right_1, trace_cursor_left_1_value, trace_cursor_right_1_value, trace_cursor_left_2, trace_cursor_right_2, trace_cursor_left_2_value, trace_cursor_right_2_value, limit_rowData_1, line_rowData_1, limit_rowData_1, limit_rowData_2, line_rowData_2, limit_rowData_2, x_min_1, x_max_1, y_min_1, y_max_1, x_min_2, x_max_2, y_min_2, y_max_2, loading_1, loading_2

    def plot_suspects(figure, suspectsTable, meta, name_meta):

        for row in suspectsTable:

            if row['source_file'] == meta['source_file'] and row['Scan'] == meta['scan'] and row['Detector'] == meta[
                'Detector']:

                meta_suspect = {'project': meta['project'], 'source_file': row['source_file'], 'scan': row['Scan'],
                                'Detector': row['Detector'], 'Bands': row["Band"].split(','), 'RBW': row["RBW"],
                                'type': 'suspect', 'line': name_meta}

                name = 'Suspect ' + row['source_file'] + '-' + row["Band"] + '-' + row["RBW"] + '-' + row['Detector']

                meta['suspects'].append(name)

                freq = row["Frequency (MHz)"].replace(',', '.')
                if freq.split(' ')[1] == 'kHz':
                    freq = (float(freq.split(' ')[0])) / (10 ** 3)
                else:
                    freq = float(freq.split(' ')[0])

                trace = go.Scatter(
                    name='Suspect ' + row['source_file'] + '-' + row["Band"] + '-' + row["RBW"] + '-' + row['Detector'],
                    x=[freq], y=[float(row["Meas.Value (dBµV/m)"])],
                    mode='markers', showlegend=False, visible=True, meta=meta_suspect,
                    marker=dict(color='orange', size=10, symbol="x"),
                    hovertemplate=f'<b>Suspect {row["source_file"]}</b><br>' + '<b>Frequency (MHz):</b> %{x:.2f}<br>' + '<b>Level (dBµV/m):</b> %{y:.2f} <extra></extra>')

                figure.add_trace(trace)

        return figure, meta

    def plot_limits(figure, meta, limit, color, chart_name, limit_rowData):

        limit = get_limit_data(limit)

        detector = meta['Detector']

        if detector == 'Peak':
            L_detector = ['Peak']
        elif detector == 'QPeak':
            L_detector = ['QPeak']
        else:
            L_detector = ['CISPR_Avg', 'Average']

        for index, row in limit.iterrows():
            if row['band_name'] in meta['Bands'] and row['detector'] in L_detector:
                freq_start = float(row['f_start'])
                freq_stop = float(row['f_stop'])
                level_start = float(row['level_start'])
                level_stop = float(row['level_stop'])

                meta_lim = {'name': meta["source_file"], 'type': 'limit', 'line': chart_name}

                name = 'Limit ' + row['limit_name'] + '-' + meta["source_file"] + '-' + row['band_name'] + '-' + str(
                    row['rbw']) + '-' + detector

                meta['limits'].append(name)

                limit_rowData.append({'Name': name, 'chart': chart_name, 'disabled': 'False'})

                trace = go.Scatter(x=[freq_start, freq_start, freq_stop, freq_stop],
                                   y=[level_start - 0.15, level_start + 0.15, level_stop + 0.15, level_stop - 0.15],
                                   name=name, showlegend=False,
                                   visible=True, fill="toself", mode='text', fillcolor=color,
                                   hovertemplate='', hoverinfo='text', text=None, meta=meta_lim)

                figure.add_trace(trace)

        return figure, meta, limit_rowData

    def set_x_range(figure):
        x_mins = []
        x_maxs = []
        y_mins = []
        y_maxs = []

        for trace in figure['data']:
            if trace['visible'] == True:
                x_mins.append(min(trace['x']))
                x_maxs.append(max(trace['x']))

                y_mins.append(min(trace['y']))
                y_maxs.append(max(trace['y']))

        x_min, x_max = min(x_mins), max(x_maxs)
        y_min, y_max = min(y_mins), max(y_maxs)
        y_min, y_max = y_min * 0.8 if y_min > 0 else y_min * 1.2, y_max * 1.05

        figure['layout']['autosize'] = False
        figure['layout']['xaxis']['autorange'] = False
        figure['layout']['xaxis']['range'] = [math.log(x_min, 10), math.log(x_max, 10)] if figure['layout']['xaxis'][
                                                                                               'type'] == 'log' else [
            x_min, x_max]

        figure['layout']['yaxis']['autorange'] = False
        figure['layout']['yaxis']['range'] = [y_min, y_max]

        return figure, round(x_min, 2), round(x_max, 2), round(y_min, 2), round(y_max, 2)

    @app.callback(Output('emission_radiated_horizontal', 'figure', allow_duplicate=True),
                  Output('emission_radiated_vertical', 'figure', allow_duplicate=True),
                  Input("suspectsTable-radiated", 'selectedRows'),
                  State('emission_radiated_horizontal', 'figure'),
                  State('emission_radiated_vertical', 'figure'),
                  State('action_radiated', 'data'),
                  prevent_initial_call=True)
    def display_suspects_radiated(suspectsTable_selectedRows, figure_1, figure_2, action):
        if action == 'standby':
            return display_suspects(suspectsTable_selectedRows, figure_1, figure_2)

        else:
            raise PreventUpdate

    @app.callback(Output('conducted_ground', 'figure', allow_duplicate=True),
                  Output('conducted_supply', 'figure', allow_duplicate=True),
                  Input("suspectsTable-conducted", 'selectedRows'),
                  State('conducted_ground', 'figure'),
                  State('conducted_supply', 'figure'),
                  State('action_conducted', 'data'),
                  prevent_initial_call=True)
    def display_suspects_conducted(suspectsTable_selectedRows, figure_1, figure_2, action):
        if action == 'standby':
            return display_suspects(suspectsTable_selectedRows, figure_1, figure_2)

        else:
            raise PreventUpdate

    def display_suspects(suspectsTable_selectedRows, figure_1, figure_2):

        figure_1, figure_2 = go.Figure(figure_1), go.Figure(figure_2)

        suspect_list = [
            'Suspect ' + suspect['source_file'] + '-' + suspect["Band"] + '-' + suspect["RBW"] + '-' + suspect[
                'Detector'] for suspect in suspectsTable_selectedRows]

        for trace in figure_1['data']:

            if trace['meta']['type'] == 'suspect':

                if trace['name'] in suspect_list:
                    trace['visible'] = True
                else:
                    trace['visible'] = False

        for trace in figure_2['data']:
            if trace['meta']['type'] == 'suspect':

                if trace['name'] in suspect_list:
                    trace['visible'] = True
                else:
                    trace['visible'] = False

        return figure_1, figure_2

    @app.callback(Output('emission_radiated_horizontal', 'figure', allow_duplicate=True),
                  Output('suspectsTable-radiated', 'rowData', allow_duplicate=True),
                  Output('suspectsTable-radiated', 'selectedRows', allow_duplicate=True),
                  Output('limits-table-h', 'rowData', allow_duplicate=True),
                  Output('limits-table-h', 'selectedRows', allow_duplicate=True),
                  Input("emission_radiated_horizontal", 'restyleData'),
                  Input('xaxis-emission_h', 'value'),
                  Input("limits-table-h", 'selectedRows'),
                  Input('line-table-h', 'cellValueChanged'),
                  State('emission_radiated_horizontal', 'figure'),
                  State('action_radiated', 'data'),
                  State('suspectsTable-radiated', 'rowData'),
                  State('limits-table-h', 'rowData'),
                  prevent_initial_call=True)
    def update_radiated_horizontal(restyleData, scale, limitsTable_selectedRows, cell, figure, action,
                                   suspectsTable_radiated, limitsTable_rowData):
        return update_graph(restyleData, scale, figure, action, cell, suspectsTable_radiated, limitsTable_rowData,
                            limitsTable_selectedRows)

    @app.callback(Output('emission_radiated_vertical', 'figure', allow_duplicate=True),
                  Output('suspectsTable-radiated', 'rowData', allow_duplicate=True),
                  Output('suspectsTable-radiated', 'selectedRows', allow_duplicate=True),
                  Output('limits-table-v', 'rowData', allow_duplicate=True),
                  Output('limits-table-v', 'selectedRows', allow_duplicate=True),
                  Input("emission_radiated_vertical", 'restyleData'),
                  Input('xaxis-emission_v', 'value'),
                  Input("limits-table-v", 'selectedRows'),
                  Input('line-table-v', 'cellValueChanged'),
                  State('emission_radiated_vertical', 'figure'),
                  State('action_radiated', 'data'),
                  State('suspectsTable-radiated', 'rowData'),
                  State('limits-table-v', 'rowData'),
                  prevent_initial_call=True)
    def update_radiated_vertical(restyleData, scale, limitsTable_selectedRows, cell, figure, action,
                                 suspectsTable_radiated, limitsTable_rowData):
        return update_graph(restyleData, scale, figure, action, cell, suspectsTable_radiated, limitsTable_rowData,
                            limitsTable_selectedRows)

    @app.callback(Output('conducted_ground', 'figure', allow_duplicate=True),
                  Output('suspectsTable-conducted', 'rowData', allow_duplicate=True),
                  Output('suspectsTable-conducted', 'selectedRows', allow_duplicate=True),
                  Output('limits-table-ground', 'rowData', allow_duplicate=True),
                  Output('limits-table-ground', 'selectedRows', allow_duplicate=True),
                  Input('conducted_ground', 'restyleData'),
                  Input('xaxis-emission_ground', 'value'),
                  Input("limits-table-ground", 'selectedRows'),
                  Input('line-table-ground', 'cellValueChanged'),
                  State('conducted_ground', 'figure'),
                  State('action_conducted', 'data'),
                  State('suspectsTable-conducted', 'rowData'),
                  State('limits-table-ground', 'rowData'),
                  prevent_initial_call=True)
    def update_conducted_ground(restyleData, scale, limitsTable_selectedRows, cell, figure, action,
                                suspectsTable_radiated, limitsTable_rowData):
        return update_graph(restyleData, scale, figure, action, cell, suspectsTable_radiated, limitsTable_rowData,
                            limitsTable_selectedRows)

    @app.callback(Output('conducted_supply', 'figure', allow_duplicate=True),
                  Output('suspectsTable-conducted', 'rowData', allow_duplicate=True),
                  Output('suspectsTable-conducted', 'selectedRows', allow_duplicate=True),
                  Output('limits-table-supply', 'rowData', allow_duplicate=True),
                  Output('limits-table-supply', 'selectedRows', allow_duplicate=True),
                  Input("conducted_supply", 'restyleData'),
                  Input('xaxis-emission_supply', 'value'),
                  Input("limits-table-supply", 'selectedRows'),
                  Input('line-table-supply', 'cellValueChanged'),
                  State('conducted_supply', 'figure'),
                  State('action_conducted', 'data'),
                  State('suspectsTable-conducted', 'rowData'),
                  State('limits-table-supply', 'rowData'),
                  prevent_initial_call=True)
    def update_conducted_supply(restyleData, scale, limitsTable_selectedRows, cell, figure, action,
                                suspectsTable_radiated, limitsTable_rowData):
        return update_graph(restyleData, scale, figure, action, cell, suspectsTable_radiated, limitsTable_rowData,
                            limitsTable_selectedRows)

    def update_graph(restyleData, scale, figure, action, cell, suspectsTable_rowData, limitsTable_rowData,
                     limitsTable_selectedRows):
        if action == 'standby':
            triggered_id = ctx.triggered_id

            select_suspect = no_update
            select_limit = no_update

            if triggered_id == 'emission_radiated_horizontal' or triggered_id == 'emission_radiated_vertical' or triggered_id == 'conducted_ground' or triggered_id == 'conducted_supply':

                if restyleData != []:
                    legend_index = restyleData[1][0]
                    meta = figure['data'][legend_index]['meta']
                    visible = restyleData[0]['visible'][0]
                    print(visible)

                    select_suspect = []
                    for suspect in suspectsTable_rowData:
                        if suspect["source_file"] == meta['source_file'] and suspect["Band"] in meta["Bands"] and \
                                suspect['Detector'] == meta['Detector'] and suspect['RBW'] == meta['RBW']:
                            if suspect['disabled'] == 'False':
                                suspect['disabled'] = 'True'
                            else:
                                suspect['disabled'] = 'False'
                                select_suspect.append(suspect)
                        else:
                            select_suspect.append(suspect)

                    select_limit = []
                    for limit in limitsTable_rowData:
                        if limit['Name'] in meta['limits']:
                            if limit['disabled'] == 'False':
                                limit['disabled'] = 'True'
                            else:
                                limit['disabled'] = 'False'
                                select_limit.append(limit)
                        else:
                            select_limit.append(limit)

                    figure = toggle_limit(select_limit, figure)

                    for shape in figure['layout']['shapes']:
                        if shape['name'] == 'Cursor left' or shape['name'] == 'Cursor right':
                            shape['visible'] = visible

                    for annotation in figure['layout']['annotations']:
                        if annotation['name'] == 'Cursor left' or annotation['name'] == 'Cursor right':
                            annotation['visible'] = False if visible == 'legendonly' else True

            elif triggered_id == 'xaxis-emission_h' or triggered_id == 'xaxis-emission_v' or triggered_id == 'xaxis-emission_ground' or triggered_id == 'xaxis-emission_supply':

                range = figure['layout']['xaxis']['range']

                if scale == 'linear':
                    figure['layout']['xaxis']['type'] = scale

                    x_min, x_max = 10 ** range[0], 10 ** range[1]
                    figure['layout']['xaxis']['range'] = [x_min, x_max]

                    if 'annotations' in figure['layout']:
                        for i in range(len(figure['layout']['annotations'])):
                            figure['layout']['annotations'][i]['x'] = 10 ** figure['layout']['annotations'][i]['x']
                else:
                    figure['layout']['xaxis']['type'] = scale

                    x_min, x_max = math.log(range[0], 10), math.log(range[1], 10)
                    figure['layout']['xaxis']['range'] = [x_min, x_max]

                    if 'annotations' in figure['layout']:
                        for i in range(len(figure['layout']['annotations'])):
                            figure['layout']['annotations'][i]['x'] = math.log(figure['layout']['annotations'][i]['x'],
                                                                               10)

            elif triggered_id == 'limits-table-h' or triggered_id == 'limits-table-v' or triggered_id == 'limits-table-ground' or triggered_id == 'limits-table-supply':

                limits_list = [limit['Name'] for limit in limitsTable_selectedRows]

                for trace in figure['data']:
                    if trace['meta']['type'] == 'limit':
                        if trace['name'] in limits_list:
                            trace['visible'] = True
                        else:
                            trace['visible'] = False

            elif triggered_id == 'line-table-h' or triggered_id == 'line-table-v' or triggered_id == 'line-table-ground' or triggered_id == 'line-table-supply':
                row = cell[0]['data']

                for trace in figure['data']:
                    if trace['name'] == row['Name']:
                        Color = trace['line']['color']

                        color_list = generate_gradient(3, Gradient[row['Color']])
                        trace['line']['color'] = color_list[0] if trace['meta']['RBW'] == '9 kHz' else color_list[1] if \
                            trace['meta']['RBW'] == '120 kHz' or trace['meta']['RBW'] == '200 kHz' else color_list[2] if \
                            trace['meta']['RBW'] == '1 MHz' else None
                        trace['meta']['Color'] = [trace['line']['color'], row['Color']]
                        trace['line']['width'] = row['Width']
                        trace['line']['dash'] = row['Type']

                        for trace_2 in figure['data']:
                            if trace_2['meta']['type'] == 'limit' and trace_2['name'] in trace['meta']['limits']:
                                trace_2['fillcolor'] = trace['line']['color']

                        if 'shapes' in figure['layout'] and 'annotations' in figure['layout']:
                            for shape in figure['layout']['shapes']:
                                if shape['line']['color'] == Color:
                                    shape['line']['color'] = trace['line']['color']
                                    for annotation in figure['layout']['annotations']:
                                        if annotation['name'] == annotation['name']:
                                            annotation['font']['color'] = trace['line']['color']

            return figure, suspectsTable_rowData, select_suspect, limitsTable_rowData, select_limit
        else:
            raise PreventUpdate

    def generate_gradient(n, color):
        from matplotlib import cm
        color = cm.get_cmap(color)
        return [f'rgb({r * 255:.0f},{g * 255:.0f},{b * 255:.0f})' for r, g, b, a in color(np.linspace(0.5, 0.9, n))]

    def toggle_limit(limitsTable_selectedRows, figure):

        limit_list = [limit['Name'] for limit in limitsTable_selectedRows]

        for trace in figure['data']:
            if trace['meta']['type'] == 'limit':
                if trace['name'] in limit_list:

                    trace['visible'] = True

                else:
                    trace['visible'] = False

        return figure

    @app.callback(Output('emission_radiated_horizontal', 'figure', allow_duplicate=True),
                  Output('emission_radiated_horizontal', 'relayoutData', allow_duplicate=True),
                  Output('input_x_min-emission_h', 'value', allow_duplicate=True),
                  Output('input_x_max-emission_h', 'value', allow_duplicate=True),
                  Output('input_y_min-emission_h', 'value', allow_duplicate=True),
                  Output('input_y_max-emission_h', 'value', allow_duplicate=True),
                  Input("emission_radiated_horizontal", 'relayoutData'),
                  Input('input_x_min-emission_h', 'value'),
                  Input('input_x_max-emission_h', 'value'),
                  Input('input_y_min-emission_h', 'value'),
                  Input('input_y_max-emission_h', 'value'),
                  State('emission_radiated_horizontal', 'figure'),
                  State('action_radiated', 'data'),
                  prevent_initial_call=True)
    def x_axis_radiated_h(relayoutData, x_min, x_max, y_min, y_max, figure, data):
        return x_axis(relayoutData, x_min, x_max, y_min, y_max, figure, data)

    @app.callback(Output('emission_radiated_vertical', 'figure', allow_duplicate=True),
                  Output('emission_radiated_vertical', 'relayoutData', allow_duplicate=True),
                  Output('input_x_min-emission_v', 'value', allow_duplicate=True),
                  Output('input_x_max-emission_v', 'value', allow_duplicate=True),
                  Output('input_y_min-emission_v', 'value', allow_duplicate=True),
                  Output('input_y_max-emission_v', 'value', allow_duplicate=True),
                  Input("emission_radiated_vertical", 'relayoutData'),
                  Input('input_x_min-emission_v', 'value'),
                  Input('input_x_max-emission_v', 'value'),
                  Input('input_y_min-emission_v', 'value'),
                  Input('input_y_max-emission_v', 'value'),
                  State('emission_radiated_vertical', 'figure'),
                  State('action_radiated', 'data'),
                  prevent_initial_call=True)
    def x_axis_radiated_v(relayoutData, x_min, x_max, y_min, y_max, figure, data):
        return x_axis(relayoutData, x_min, x_max, y_min, y_max, figure, data)

    @app.callback(Output('conducted_ground', 'figure', allow_duplicate=True),
                  Output('conducted_ground', 'relayoutData', allow_duplicate=True),
                  Output('input_x_min-emission_ground', 'value', allow_duplicate=True),
                  Output('input_x_max-emission_ground', 'value', allow_duplicate=True),
                  Output('input_y_min-emission_ground', 'value', allow_duplicate=True),
                  Output('input_y_max-emission_ground', 'value', allow_duplicate=True),
                  Input("conducted_ground", 'relayoutData'),
                  Input('input_x_min-emission_ground', 'value'),
                  Input('input_x_max-emission_ground', 'value'),
                  Input('input_y_min-emission_ground', 'value'),
                  Input('input_y_max-emission_ground', 'value'),
                  State('conducted_ground', 'figure'),
                  State('action_conducted', 'data'),
                  prevent_initial_call=True)
    def x_axis_conducted_ground(relayoutData, x_min, x_max, y_min, y_max, figure, data):
        return x_axis(relayoutData, x_min, x_max, y_min, y_max, figure, data)

    @app.callback(Output('conducted_supply', 'figure', allow_duplicate=True),
                  Output('conducted_supply', 'relayoutData', allow_duplicate=True),
                  Output('input_x_min-emission_supply', 'value', allow_duplicate=True),
                  Output('input_x_max-emission_supply', 'value', allow_duplicate=True),
                  Output('input_y_min-emission_supply', 'value', allow_duplicate=True),
                  Output('input_y_max-emission_supply', 'value', allow_duplicate=True),
                  Input("conducted_supply", 'relayoutData'),
                  Input('input_x_min-emission_supply', 'value'),
                  Input('input_x_max-emission_supply', 'value'),
                  Input('input_y_min-emission_supply', 'value'),
                  Input('input_y_max-emission_supply', 'value'),
                  State('conducted_supply', 'figure'),
                  State('action_conducted', 'data'),
                  prevent_initial_call=True)
    def x_axis_conducted_supply(relayoutData, x_min, x_max, y_min, y_max, figure, data):
        return x_axis(relayoutData, x_min, x_max, y_min, y_max, figure, data)

    def x_axis(relayoutData, x_min, x_max, y_min, y_max, figure, data):
        if data == 'standby' and figure['data'] != []:
            triggered_id = ctx.triggered_id

            if triggered_id == 'input_x_min-emission_v' or triggered_id == 'input_x_max-emission_v' or triggered_id == 'input_y_min-emission_v' or triggered_id == 'input_y_max-emission_v' or triggered_id == 'input_x_min-emission_h' or triggered_id == 'input_x_max-emission_h' or triggered_id == 'input_y_min-emission_h' or triggered_id == 'input_y_max-emission_h' or triggered_id == 'input_x_min-emission_ground' or triggered_id == 'input_x_max-emission_ground' or triggered_id == 'input_y_min-emission_ground' or triggered_id == 'input_y_max-emission_ground' or triggered_id == 'input_x_min-emission_supply' or triggered_id == 'input_x_max-emission_supply' or triggered_id == 'input_y_min-emission_supply' or triggered_id == 'input_y_max-emission_supply':

                figure['layout']['xaxis']['range'] = [math.log(x_min, 10), math.log(x_max, 10)] if \
                figure['layout']['xaxis']['type'] == 'log' else [x_min, x_max]
                figure['layout']['yaxis']['range'] = [y_min, y_max]

                x_min, x_max, y_min, y_max = no_update, no_update, no_update, no_update

            elif (relayoutData == {'xaxis.autorange': True, 'yaxis.autorange': True} or relayoutData == {
                'autosize': True}) and (
                    triggered_id == 'emission_radiated_vertical' or triggered_id == 'emission_radiated_horizontal' or triggered_id == 'conducted_ground' or triggered_id == 'conducted_supply'):

                figure, x_min, x_max, y_min, y_max = set_x_range(figure)
                relayoutData = {'autosize': False}

                y_min, y_max = figure['layout']['yaxis']['range']

                x_min, x_max, y_min, y_max = round(x_min, 2), round(x_max, 2), round(
                    y_min * 0.8 if y_min > 0 else y_min * 1.2, 2), round(y_max * 1.05)

            else:
                x_min, x_max = figure['layout']['xaxis']['range']
                x_min, x_max = (10 ** x_min, 10 ** x_max) if figure['layout']['xaxis']['type'] == 'log' else (
                x_min, x_max)

                y_min, y_max = figure['layout']['yaxis']['range']

                x_min, x_max, y_min, y_max = round(x_min, 2), round(x_max, 2), round(
                    y_min * 0.8 if y_min > 0 else y_min * 1.2, 2), round(y_max * 1.05)

                figure = no_update
                relayoutData = no_update

        return figure, relayoutData, x_min, x_max, y_min, y_max

    @app.callback(
        Output("sidebar", "style", allow_duplicate=True),
        Output("toggle-button", "style", allow_duplicate=True),
        Output('toggle-button', 'disabled', allow_duplicate=True),
        Output('radiated-btn', 'disabled', allow_duplicate=True),
        Output('conducted-btn', 'disabled', allow_duplicate=True),
        Output('line-table-container-ground', 'style', allow_duplicate=True),
        Output('line-table-btn-ground', 'children', allow_duplicate=True),
        Output('line-table-container-supply', 'style', allow_duplicate=True),
        Output('line-table-btn-supply', 'children', allow_duplicate=True),
        Output('line-table-container-h', 'style', allow_duplicate=True),
        Output('line-table-btn-h', 'children', allow_duplicate=True),
        Output('line-table-container-v', 'style', allow_duplicate=True),
        Output('line-table-btn-v', 'children', allow_duplicate=True),
        Input("toggle-button", "n_clicks"),
        Input('action_radiated', "data"),
        Input('action_conducted', "data"),
        State("sidebar", "style"),
        State("toggle-button", "style"),
        State('toggle-button', 'disabled'),
        State('radiated-btn', 'disabled'),
        State('conducted-btn', 'disabled'),
        State('line-table-container-ground', 'style'),
        State('line-table-btn-ground', 'children'),
        State('line-table-container-supply', 'style'),
        State('line-table-btn-supply', 'children'),
        State('line-table-container-h', 'style'),
        State('line-table-btn-h', 'children'),
        State('line-table-container-v', 'style'),
        State('line-table-btn-v', 'children'),
        State('emission_radiated_horizontal', 'style'),
        State('emission_radiated_vertical', 'style'),
        State('conducted_ground', 'style'),
        State('conducted_supply', 'style'),
        prevent_initial_call=True)
    def toggle_sidebar(n_clicks, action_radiated, action_conducted, style_sidebar, style_toggle_button, sidebar_btn,
                       radiated_btn, conducted_btn, line_param_ground, btn_txt_ground, line_param_supply,
                       btn_txt_supply, line_param_h, btn_txt_h, line_param_v, btn_txt_v, radiated_horizontal_style,
                       radiated_vertical_style, conducted_ground_style, conducted_supply_style):
        triggered_id = ctx.triggered_id

        if (
                triggered_id == 'action_radiated' and action_radiated == 'standby') or triggered_id == 'action_conducted' and action_conducted == 'standby':
            if radiated_horizontal_style['display'] == 'none' and radiated_vertical_style['display'] == 'none' and \
                    conducted_ground_style['display'] == 'none' and conducted_supply_style['display'] == 'none':
                sidebar_btn = True
                style_sidebar["transform"] = "translateX(100%)"
                style_toggle_button["transform"] = "translateX(0%)"
                btn_txt_ground, btn_txt_supply, btn_txt_h, btn_txt_v = 'Show Line Display Parameters', 'Show Line Display Parameters', 'Show Line Display Parameters', 'Show Line Display Parameters'
                line_param_ground['display'], line_param_supply['display'], line_param_h['display'], line_param_v[
                    'display'] = 'none', 'none', 'none', 'none'
            else:
                sidebar_btn = False

                if radiated_horizontal_style['display'] == 'block' or radiated_vertical_style['display'] == 'block':
                    radiated_btn = False
                elif radiated_horizontal_style['display'] == 'none' and radiated_vertical_style['display'] == 'none':
                    radiated_btn = True

                if conducted_ground_style['display'] == 'block' or conducted_supply_style['display'] == 'block':
                    conducted_btn = False
                elif conducted_ground_style['display'] == 'none' and conducted_supply_style['display'] == 'none':
                    conducted_btn = True

        elif triggered_id == "toggle-button":
            if n_clicks % 2 == 1:  # Show the sidebar
                style_sidebar["transform"] = "translateX(0%)"
                style_toggle_button["transform"] = "translateX(-310%)"
            else:
                style_sidebar["transform"] = "translateX(100%)"
                style_toggle_button["transform"] = "translateX(0%)"
                btn_txt_ground, btn_txt_supply, btn_txt_h, btn_txt_v = 'Show Line Display Parameters', 'Show Line Display Parameters', 'Show Line Display Parameters', 'Show Line Display Parameters'
                line_param_ground['display'], line_param_supply['display'], line_param_h['display'], line_param_v[
                    'display'] = 'none', 'none', 'none', 'none'

        return style_sidebar, style_toggle_button, sidebar_btn, radiated_btn, conducted_btn, line_param_ground, btn_txt_ground, line_param_supply, btn_txt_supply, line_param_h, btn_txt_h, line_param_v, btn_txt_v

    # Callback to show/hide the emission submenu
    @app.callback(Output("radiated-electric-submenu", "style", allow_duplicate=True),
                  Output("conducted-voltage-submenu", "style", allow_duplicate=True),
                  Output("radiated-btn", "n_clicks", allow_duplicate=True),
                  Output("conducted-btn", "n_clicks", allow_duplicate=True),
                  Output('line-table-container-h', 'style', allow_duplicate=True),
                  Output('line-table-btn-h', 'children', allow_duplicate=True),
                  Output('line-table-container-v', 'style', allow_duplicate=True),
                  Output('line-table-btn-v', 'children', allow_duplicate=True),
                  Input("radiated-btn", "n_clicks"),
                  Input("conducted-btn", "n_clicks"),
                  State('line-table-container-h', 'style'),
                  State('line-table-btn-h', 'children'),
                  State('line-table-container-v', 'style'),
                  State('line-table-btn-v', 'children'),
                  prevent_initial_call=True
                  )
    def toggle_submenus(emission_clicks, immunity_clicks, line_param_h, btn_txt_h, line_param_v, btn_txt_v):
        ctx = dash.callback_context

        # Check which button was clicked
        if ctx.triggered:
            clicked_button = ctx.triggered[0]["prop_id"].split(".")[0]  # get the button ID

            # Initially set both submenus to hidden
            emission_style = submenu_style
            immunity_style = submenu_style

            # Logic to show/hide the appropriate submenu
            if clicked_button == "radiated-btn":
                if emission_clicks % 2 == 1:  # Emission button clicked an odd number of times
                    emission_style = submenu_active_style
                    immunity_clicks = 0
                else:  # Emission button clicked an even number of times
                    emission_style = submenu_style
                    immunity_style = submenu_style  # Hide Immunity submenu

            elif clicked_button == "conducted-btn":
                if immunity_clicks % 2 == 1:  # Immunity button clicked an odd number of times
                    immunity_style = submenu_active_style
                    emission_clicks = 0
                else:  # Immunity button clicked an even number of times
                    immunity_style = submenu_style
                    emission_style = submenu_style  # Hide Emission submenu
                    btn_txt_h, btn_txt_v = 'Show Line Display Parameters', 'Show Line Display Parameters'
                    line_param_h['display'], line_param_v['display'] = 'none', 'none'

            return emission_style, immunity_style, emission_clicks, immunity_clicks, line_param_h, btn_txt_h, line_param_v, btn_txt_v
        return submenu_style, submenu_style, 0, 0, line_param_h, btn_txt_h, line_param_v, btn_txt_v

    @app.callback(Output('suspectsTable-conducted', 'style', allow_duplicate=True),
                  Output('minimize_suspectTable_conducted_btn', "children", allow_duplicate=True),
                  Input('minimize_suspectTable_conducted_btn', "n_clicks"),
                  State('suspectsTable-conducted', 'style'),
                  prevent_initial_call=True)
    def minimize_suspectTable_conducted(n_clicks, style):
        return minimize_suspectTable(n_clicks, style)

    @app.callback(Output('suspectsTable-radiated', 'style', allow_duplicate=True),
                  Output('minimize_suspectTable_radiated_btn', "children", allow_duplicate=True),
                  Input('minimize_suspectTable_radiated_btn', "n_clicks"),
                  State('suspectsTable-radiated', 'style'),
                  prevent_initial_call=True)
    def minimize_suspectTable_radiated(n_clicks, style):
        return minimize_suspectTable(n_clicks, style)

    def minimize_suspectTable(n_clicks, style):
        if n_clicks % 2 == 1:
            style['display'], children = 'block', 'Hide Suspect Table'
        else:
            style['display'], children = 'none', 'Show Suspect Table'
        return style, children

    @app.callback(
        Output('emission_radiated_horizontal', 'figure', allow_duplicate=True),
        Output('cursor_data', 'data', allow_duplicate=True),
        Output('cursor_menu_radiated_h', 'style', allow_duplicate=True),
        Output('position_cursor_left_radiated_h', 'value', allow_duplicate=True),
        Output('position_cursor_right_radiated_h', 'value', allow_duplicate=True),
        Input('activate_cursors_radiated_h', 'on'),
        Input('cursors_direction_radiated_h', 'value'),
        State('emission_radiated_horizontal', 'figure'),
        State('cursor_data', 'data'),
        State('cursor_menu_radiated_h', 'style'),
        prevent_initial_call=True,
    )
    def activate_cursors_radiated_h(activate_cursors, cursors_direction, figure, cursor_data, cursor_menu_style):
        return activate_cursor(activate_cursors, cursors_direction, figure, cursor_data, cursor_menu_style,
                               'radiated horizontal')

    @app.callback(
        Output('emission_radiated_vertical', 'figure', allow_duplicate=True),
        Output('cursor_data', 'data', allow_duplicate=True),
        Output('cursor_menu_radiated_v', 'style', allow_duplicate=True),
        Output('position_cursor_left_radiated_v', 'value', allow_duplicate=True),
        Output('position_cursor_right_radiated_v', 'value', allow_duplicate=True),
        Input('activate_cursors_radiated_v', 'on'),
        Input('cursors_direction_radiated_v', 'value'),
        State('emission_radiated_vertical', 'figure'),
        State('cursor_data', 'data'),
        State('cursor_menu_radiated_v', 'style'),
        prevent_initial_call=True,
    )
    def activate_cursors_radiated_v(activate_cursors, cursors_direction, figure, cursor_data, cursor_menu_style):
        return activate_cursor(activate_cursors, cursors_direction, figure, cursor_data, cursor_menu_style,
                               'radiated vertical')

    @app.callback(
        Output('conducted_ground', 'figure', allow_duplicate=True),
        Output('cursor_data', 'data', allow_duplicate=True),
        Output('cursor_menu_conducted_ground', 'style', allow_duplicate=True),
        Output('position_cursor_left_conducted_ground', 'value', allow_duplicate=True),
        Output('position_cursor_right_conducted_ground', 'value', allow_duplicate=True),
        Input('activate_cursors_conducted_ground', 'on'),
        Input('cursors_direction_conducted_ground', 'value'),
        State('conducted_ground', 'figure'),
        State('cursor_data', 'data'),
        State('cursor_menu_conducted_ground', 'style'),
        prevent_initial_call=True,
    )
    def activate_cursors_conducted_ground(activate_cursors, cursors_direction, figure, cursor_data, cursor_menu_style):
        return activate_cursor(activate_cursors, cursors_direction, figure, cursor_data, cursor_menu_style,
                               'conducted ground')

    @app.callback(
        Output('conducted_supply', 'figure', allow_duplicate=True),
        Output('cursor_data', 'data', allow_duplicate=True),
        Output('cursor_menu_conducted_supply', 'style', allow_duplicate=True),
        Output('position_cursor_left_conducted_supply', 'value', allow_duplicate=True),
        Output('position_cursor_right_conducted_supply', 'value', allow_duplicate=True),
        Input('activate_cursors_conducted_supply', 'on'),
        Input('cursors_direction_conducted_supply', 'value'),
        State('conducted_supply', 'figure'),
        State('cursor_data', 'data'),
        State('cursor_menu_conducted_supply', 'style'),
        prevent_initial_call=True,
    )
    def activate_cursors_conducted_supply(activate_cursors, cursors_direction, figure, cursor_data, cursor_menu_style):

        return activate_cursor(activate_cursors, cursors_direction, figure, cursor_data, cursor_menu_style,
                               'conducted supply')

    def activate_cursor(activate_cursors, cursors_direction, figure, cursor_data, cursor_menu_style, type):
        triggered_id = ctx.triggered_id

        if 'cursors_direction' in triggered_id and cursor_data[type]['left'] != {}:
            cursor_data[type] = {'left': {}, 'right': {}}

            for shape in figure['layout']['shapes'].copy():
                if shape['name'] == 'Cursor left' or shape['name'] == 'Cursor right':
                    figure['layout']['shapes'].remove(shape)

            for annotation in figure['layout']['annotations'].copy():
                if annotation['name'] == 'Cursor left' or annotation['name'] == 'Cursor right':
                    figure['layout']['annotations'].remove(annotation)

            position_cursor_left, position_cursor_right = None, None

        else:

            position_cursor_left, position_cursor_right = no_update, no_update

        figure = go.Figure(figure)

        if activate_cursors:
            cursor_menu_style['display'] = 'block'

            if cursors_direction == 'Vertical':
                figure.update_layout(hovermode="x unified")

            elif cursors_direction == 'Horizontal':
                figure.update_layout(hovermode="y unified")

        else:
            figure.update_layout(hovermode="closest")

            cursor_menu_style['display'] = 'none'

        if 'activate_cursors' in triggered_id:

            for shape in figure['layout']['shapes']:
                if shape['name'] == 'Cursor left' or shape['name'] == 'Cursor right':
                    shape['visible'] = activate_cursors

            for annotation in figure['layout']['annotations']:
                if annotation['name'] == 'Cursor left' or annotation['name'] == 'Cursor right':
                    annotation['visible'] = activate_cursors

        return figure, cursor_data, cursor_menu_style, position_cursor_left, position_cursor_right

    @app.callback(
        Output('emission_radiated_horizontal', 'figure', allow_duplicate=True),
        Output('cursor_data', 'data', allow_duplicate=True),
        Output('Δx_radiated_h', 'children', allow_duplicate=True),
        Output('Δy_radiated_h', 'children', allow_duplicate=True),
        Output('1/Δx_radiated_h', 'children', allow_duplicate=True),
        Output('Δy/Δx_radiated_h', 'children', allow_duplicate=True),
        Output('position_cursor_left_radiated_h', 'value', allow_duplicate=True),
        Output('position_cursor_right_radiated_h', 'value', allow_duplicate=True),
        Output('emission_radiated_horizontal', 'clickData', allow_duplicate=True),
        Input('emission_radiated_horizontal', 'clickData'),
        State('trace_cursor_left_radiated_h', 'value'),
        State('trace_cursor_right_radiated_h', 'value'),
        State('activate_cursors_radiated_h', 'on'),
        State('cursors_direction_radiated_h', 'value'),
        State('emission_radiated_horizontal', 'figure'),
        State('cursor_data', 'data'),
        State('xaxis-emission_h', 'value'),
        prevent_initial_call=True,
    )
    def cursor_radiated_horizontal(clickData, trace_cursor_left, trace_cursor_right, activate_cursors,
                                   cursors_direction, figure, cursor_data, xaxis_scale):
        return cursor_fct(clickData, trace_cursor_left, trace_cursor_right, activate_cursors, cursors_direction, figure,
                          cursor_data, xaxis_scale, 'radiated horizontal')

    @app.callback(
        Output('emission_radiated_vertical', 'figure', allow_duplicate=True),
        Output('cursor_data', 'data', allow_duplicate=True),
        Output('Δx_radiated_v', 'children', allow_duplicate=True),
        Output('Δy_radiated_v', 'children', allow_duplicate=True),
        Output('1/Δx_radiated_v', 'children', allow_duplicate=True),
        Output('Δy/Δx_radiated_v', 'children', allow_duplicate=True),
        Output('position_cursor_left_radiated_v', 'value', allow_duplicate=True),
        Output('position_cursor_right_radiated_v', 'value', allow_duplicate=True),
        Output('emission_radiated_vertical', 'clickData', allow_duplicate=True),
        Input('emission_radiated_vertical', 'clickData'),
        State('trace_cursor_left_radiated_v', 'value'),
        State('trace_cursor_right_radiated_v', 'value'),
        State('activate_cursors_radiated_v', 'on'),
        State('cursors_direction_radiated_v', 'value'),
        State('emission_radiated_vertical', 'figure'),
        State('cursor_data', 'data'),
        State('xaxis-emission_v', 'value'),
        prevent_initial_call=True,
    )
    def cursor_radiated_vertical(clickData, trace_cursor_left, trace_cursor_right, activate_cursors, cursors_direction,
                                 figure, cursor_data, xaxis_scale):
        return cursor_fct(clickData, trace_cursor_left, trace_cursor_right, activate_cursors, cursors_direction, figure,
                          cursor_data, xaxis_scale, 'radiated vertical')

    @app.callback(
        Output('conducted_ground', 'figure', allow_duplicate=True),
        Output('cursor_data', 'data', allow_duplicate=True),
        Output('Δx_conducted_ground', 'children', allow_duplicate=True),
        Output('Δy_conducted_ground', 'children', allow_duplicate=True),
        Output('1/Δx_conducted_ground', 'children', allow_duplicate=True),
        Output('Δy/Δx_conducted_ground', 'children', allow_duplicate=True),
        Output('position_cursor_left_conducted_ground', 'value', allow_duplicate=True),
        Output('position_cursor_right_conducted_ground', 'value', allow_duplicate=True),
        Output('conducted_ground', 'clickData', allow_duplicate=True),
        Input('conducted_ground', 'clickData'),
        State('trace_cursor_left_conducted_ground', 'value'),
        State('trace_cursor_right_conducted_ground', 'value'),
        State('activate_cursors_conducted_ground', 'on'),
        State('cursors_direction_conducted_ground', 'value'),
        State('conducted_ground', 'figure'),
        State('cursor_data', 'data'),
        State('xaxis-emission_ground', 'value'),
        prevent_initial_call=True,
    )
    def cursor_conducted_ground(clickData, trace_cursor_left, trace_cursor_right, activate_cursors, cursors_direction,
                                figure, cursor_data, xaxis_scale):
        return cursor_fct(clickData, trace_cursor_left, trace_cursor_right, activate_cursors, cursors_direction, figure,
                          cursor_data, xaxis_scale, 'conducted ground')

    @app.callback(
        Output('conducted_supply', 'figure', allow_duplicate=True),
        Output('cursor_data', 'data', allow_duplicate=True),
        Output('Δx_conducted_supply', 'children', allow_duplicate=True),
        Output('Δy_conducted_supply', 'children', allow_duplicate=True),
        Output('1/Δx_conducted_supply', 'children', allow_duplicate=True),
        Output('Δy/Δx_conducted_supply', 'children', allow_duplicate=True),
        Output('position_cursor_left_conducted_supply', 'value', allow_duplicate=True),
        Output('position_cursor_right_conducted_supply', 'value', allow_duplicate=True),
        Output('conducted_supply', 'clickData', allow_duplicate=True),
        Input('conducted_supply', 'clickData'),
        State('trace_cursor_left_conducted_supply', 'value'),
        State('trace_cursor_right_conducted_supply', 'value'),
        State('activate_cursors_conducted_supply', 'on'),
        State('cursors_direction_conducted_supply', 'value'),
        State('conducted_supply', 'figure'),
        State('cursor_data', 'data'),
        State('xaxis-emission_supply', 'value'),
        prevent_initial_call=True,
    )
    def cursor_conducted_supply(clickData, trace_cursor_left, trace_cursor_right, activate_cursors, cursors_direction,
                                figure, cursor_data, xaxis_scale):
        return cursor_fct(clickData, trace_cursor_left, trace_cursor_right, activate_cursors, cursors_direction, figure,
                          cursor_data, xaxis_scale, 'conducted supply')

    def cursor_fct(clickData, trace_cursor_left, trace_cursor_right, activate_cursors, cursors_direction, figure,
                   cursor_data, xaxis_scale, type):
        if activate_cursors:

            dx = 'Δx: '
            dy = 'Δy: '
            dx_inv = '1/Δx: '
            dydx = 'Δy/Δx: '

            if cursors_direction == 'Vertical':

                if cursor_data[type]['left'] == {}:

                    for point in clickData['points']:
                        if figure['data'][point['curveNumber']]['name'] == trace_cursor_left:
                            cursor_data[type]['left'] = {'name': figure['data'][point['curveNumber']]['name'],
                                                         'x': point['x'], 'y': point['y']}
                            name = 'Cursor left'
                            trace = trace_cursor_left
                            x = point['x']
                            y = point['y']
                            color = figure['data'][point['curveNumber']]['line']['color']
                            xaxis = 'Frequency (MHz)'
                            yaxis = 'Level (dBμ V/m)'
                            break

                elif cursor_data[type]['right'] == {}:

                    if clickData['points'][0]['x'] >= cursor_data[type]['left']['x']:
                        for point in clickData['points']:
                            if figure['data'][point['curveNumber']]['name'] == trace_cursor_right:
                                cursor_data[type]['right'] = {'name': figure['data'][point['curveNumber']]['name'],
                                                              'x': point['x'], 'y': point['y']}
                                name = 'Cursor right'
                                trace = trace_cursor_right
                                x = point['x']
                                y = point['y']
                                color = figure['data'][point['curveNumber']]['line']['color']
                                xaxis = 'Frequency (MHz)'
                                yaxis = 'Level (dBμ V/m)'

                                dx = f'Δx: {round(cursor_data[type]['right']['x'] - cursor_data[type]['left']['x'], 2)}'
                                dy = f'Δy: {round(cursor_data[type]['right']['y'] - cursor_data[type]['left']['y'], 2)}'
                                dx_inv = f'1/Δx: {round(1 / (cursor_data[type]['right']['x'] - cursor_data[type]['left']['x']), 2)}' if (
                                                                                                                                                    cursor_data[
                                                                                                                                                        type][
                                                                                                                                                        'right'][
                                                                                                                                                        'x'] -
                                                                                                                                                    cursor_data[
                                                                                                                                                        type][
                                                                                                                                                        'left'][
                                                                                                                                                        'x']) != 0 else '1/Δx: '
                                dydx = f'Δy/Δx: {round((cursor_data[type]['right']['y'] - cursor_data[type]['left']['y']) / (cursor_data[type]['right']['x'] - cursor_data[type]['left']['x']), 2)}' if (
                                                                                                                                                                                                                    cursor_data[
                                                                                                                                                                                                                        type][
                                                                                                                                                                                                                        'right'][
                                                                                                                                                                                                                        'x'] -
                                                                                                                                                                                                                    cursor_data[
                                                                                                                                                                                                                        type][
                                                                                                                                                                                                                        'left'][
                                                                                                                                                                                                                        'x']) != 0 else 'Δy/Δx: '

                                break

                    else:

                        for shape in figure['layout']['shapes'].copy():
                            if shape['name'] == 'Cursor left':
                                figure['layout']['shapes'].remove(shape)
                                break

                        for annotation in figure['layout']['annotations'].copy():
                            if annotation['name'] == 'Cursor left':
                                figure['layout']['annotations'].remove(annotation)
                                break

                        for point in clickData['points']:
                            if figure['data'][point['curveNumber']]['name'] == trace_cursor_left:
                                cursor_data[type]['left'] = {'name': figure['data'][point['curveNumber']]['name'],
                                                             'x': point['x'], 'y': point['y']}
                                name = 'Cursor left'
                                trace = trace_cursor_left
                                x = point['x']
                                y = point['y']
                                color = figure['data'][point['curveNumber']]['line']['color']
                                xaxis = 'Frequency (MHz)'
                                yaxis = 'Level (dBμ V/m)'
                                break

                else:

                    cursor_data[type]['right'] = {}

                    for shape in figure['layout']['shapes'].copy():
                        if shape['name'] == 'Cursor left' or shape['name'] == 'Cursor right':
                            figure['layout']['shapes'].remove(shape)

                    for annotation in figure['layout']['annotations'].copy():
                        if annotation['name'] == 'Cursor left' or annotation['name'] == 'Cursor right':
                            figure['layout']['annotations'].remove(annotation)

                    for point in clickData['points']:
                        if figure['data'][point['curveNumber']]['name'] == trace_cursor_left:
                            cursor_data[type]['left'] = {'name': figure['data'][point['curveNumber']]['name'],
                                                         'x': point['x'], 'y': point['y']}
                            name = 'Cursor left'
                            trace = trace_cursor_left
                            x = point['x']
                            y = point['y']
                            color = figure['data'][point['curveNumber']]['line']['color']
                            xaxis = 'Frequency (MHz)'
                            yaxis = 'Level (dBμ V/m)'
                            break

                position_cursor_left = cursor_data[type]['left']['x'] if cursor_data[type]['left'] != {} else None
                position_cursor_right = cursor_data[type]['right']['x'] if cursor_data[type]['right'] != {} else None

                figure = go.Figure(figure)

                if xaxis_scale == 'log':
                    x_annot = math.log(x, 10)
                else:
                    x_annot = x

                figure.add_vline(
                    name=name, x=x,
                    line=dict(
                        color=color,
                        width=4,
                        dash="dash",
                    ),
                    annotation=dict(
                        name=name,
                        x=x_annot,
                        text=f"<b> {trace}<br> {xaxis}:</b> {x:.2f}<br> <b>{yaxis}:</b> {y:.2f}",
                        align='left',
                        font_size=16,
                        font_color=color
                    )
                )

            else:

                if cursor_data[type]['left'] == {}:

                    for point in clickData['points']:
                        if figure['data'][point['curveNumber']]['name'] == trace_cursor_left:
                            cursor_data[type]['left'] = {'name': figure['data'][point['curveNumber']]['name'],
                                                         'x': point['x'], 'y': point['y']}
                            name = 'Cursor left'
                            trace = trace_cursor_left
                            x = point['x']
                            y = point['y']
                            color = figure['data'][point['curveNumber']]['line']['color']
                            xaxis = 'Frequency (MHz)'
                            yaxis = 'Level (dBμ V/m)'
                            break

                elif cursor_data[type]['right'] == {}:

                    if clickData['points'][0]['y'] >= cursor_data[type]['left']['y']:
                        for point in clickData['points']:
                            if figure['data'][point['curveNumber']]['name'] == trace_cursor_right:
                                cursor_data[type]['right'] = {'name': figure['data'][point['curveNumber']]['name'],
                                                              'x': point['x'], 'y': point['y']}
                                name = 'Cursor right'
                                trace = trace_cursor_left
                                x = point['x']
                                y = point['y']
                                color = figure['data'][point['curveNumber']]['line']['color']
                                xaxis = 'Frequency (MHz)'
                                yaxis = 'Level (dBμ V/m)'

                                dx = f'Δx: {round(cursor_data[type]['right']['x'] - cursor_data[type]['left']['x'], 2)}'
                                dy = f'Δy: {round(cursor_data[type]['right']['y'] - cursor_data[type]['left']['y'], 2)}'
                                dx_inv = f'1/Δx: {round(1 / (cursor_data[type]['right']['x'] - cursor_data[type]['left']['x']), 2)}' if (
                                                                                                                                                    cursor_data[
                                                                                                                                                        type][
                                                                                                                                                        'right'][
                                                                                                                                                        'x'] -
                                                                                                                                                    cursor_data[
                                                                                                                                                        type][
                                                                                                                                                        'left'][
                                                                                                                                                        'x']) != 0 else '1/Δx: '
                                dydx = f'Δy/Δx: {round((cursor_data[type]['right']['y'] - cursor_data[type]['left']['y']) / (cursor_data[type]['right']['x'] - cursor_data[type]['left']['x']), 2)}' if (
                                                                                                                                                                                                                    cursor_data[
                                                                                                                                                                                                                        type][
                                                                                                                                                                                                                        'right'][
                                                                                                                                                                                                                        'x'] -
                                                                                                                                                                                                                    cursor_data[
                                                                                                                                                                                                                        type][
                                                                                                                                                                                                                        'left'][
                                                                                                                                                                                                                        'x']) != 0 else 'Δy/Δx: '

                                break

                    else:

                        for shape in figure['layout']['shapes'].copy():
                            if shape['name'] == 'Cursor left':
                                figure['layout']['shapes'].remove(shape)
                                break

                        for annotation in figure['layout']['annotations'].copy():
                            if annotation['name'] == 'Cursor left':
                                figure['layout']['annotations'].remove(annotation)
                                break

                        for point in clickData['points']:
                            if figure['data'][point['curveNumber']]['name'] == trace_cursor_left:
                                cursor_data[type]['left'] = {'name': figure['data'][point['curveNumber']]['name'],
                                                             'x': point['x'], 'y': point['y']}
                                name = 'Cursor left'
                                trace = trace_cursor_left
                                x = point['x']
                                y = point['y']
                                color = figure['data'][point['curveNumber']]['line']['color']
                                xaxis = 'Frequency (MHz)'
                                yaxis = 'Level (dBμ V/m)'
                                break

                else:

                    cursor_data[type]['right'] = {}

                    for shape in figure['layout']['shapes'].copy():
                        if shape['name'] == 'Cursor left' or shape['name'] == 'Cursor right':
                            figure['layout']['shapes'].remove(shape)

                    for annotation in figure['layout']['annotations'].copy():
                        if annotation['name'] == 'Cursor left' or annotation['name'] == 'Cursor right':
                            figure['layout']['annotations'].remove(annotation)

                    for point in clickData['points']:
                        if figure['data'][point['curveNumber']]['name'] == trace_cursor_left:
                            cursor_data[type]['left'] = {'name': figure['data'][point['curveNumber']]['name'],
                                                         'x': point['x'], 'y': point['y']}
                            name = 'Cursor left'
                            trace = trace_cursor_left
                            x = point['x']
                            y = point['y']
                            color = figure['data'][point['curveNumber']]['line']['color']
                            xaxis = 'Frequency (MHz)'
                            yaxis = 'Level (dBμ V/m)'
                            break

                position_cursor_left = cursor_data[type]['left']['y'] if cursor_data[type]['left'] != {} else None
                position_cursor_right = cursor_data[type]['right']['y'] if cursor_data[type]['right'] != {} else None

                figure = go.Figure(figure)

                figure.add_hline(
                    name=name, y=y,
                    line=dict(
                        color=color,
                        width=4,
                        dash="dash",
                    ),
                    annotation=dict(
                        name=name,
                        text=f"<b> {trace}<br> {xaxis}:</b> {x:.2f}<br> <b>{yaxis}:</b> {y:.2f}",
                        align='left',
                        font_size=16,
                        font_color=color
                    )
                )

            return figure, cursor_data, dx, dy, dx_inv, dydx, position_cursor_left, position_cursor_right, None

        else:
            raise PreventUpdate

    @app.callback(Output('line-table-container-ground', 'style', allow_duplicate=True),
                  Output('line-table-container-supply', 'style', allow_duplicate=True),
                  Output('line-table-btn-ground', 'children', allow_duplicate=True),
                  Output('line-table-btn-supply', 'children', allow_duplicate=True),
                  Input('line-table-btn-ground', 'n_clicks'),
                  State('line-table-container-ground', 'style'),
                  State('line-table-container-supply', 'style'),
                  State('line-table-btn-supply', 'children'),
                  prevent_initial_call=True)
    def toggle_line_param_ground(btn_click, line_param_ground, line_param_supply, btn_txt_2):
        return toggle_line_param(line_param_ground, line_param_supply, btn_txt_2)

    @app.callback(Output('line-table-container-supply', 'style', allow_duplicate=True),
                  Output('line-table-container-ground', 'style', allow_duplicate=True),
                  Output('line-table-btn-supply', 'children', allow_duplicate=True),
                  Output('line-table-btn-ground', 'children', allow_duplicate=True),
                  Input('line-table-btn-supply', 'n_clicks'),
                  State('line-table-container-ground', 'style'),
                  State('line-table-container-supply', 'style'),
                  State('line-table-btn-ground', 'children'),
                  prevent_initial_call=True)
    def toggle_line_param_supply(btn_click, line_param_ground, line_param_supply, btn_txt_2):
        return toggle_line_param(line_param_supply, line_param_ground, btn_txt_2)

    @app.callback(Output('line-table-container-h', 'style', allow_duplicate=True),
                  Output('line-table-container-v', 'style', allow_duplicate=True),
                  Output('line-table-btn-h', 'children', allow_duplicate=True),
                  Output('line-table-btn-v', 'children', allow_duplicate=True),
                  Input('line-table-btn-h', 'n_clicks'),
                  State('line-table-container-h', 'style'),
                  State('line-table-container-v', 'style'),
                  State('line-table-btn-v', 'children'),
                  prevent_initial_call=True)
    def toggle_line_param_h(btn_click, line_param_horizontal, line_param_vertical, btn_txt_2):
        return toggle_line_param(line_param_horizontal, line_param_vertical, btn_txt_2)

    @app.callback(Output('line-table-container-v', 'style', allow_duplicate=True),
                  Output('line-table-container-h', 'style', allow_duplicate=True),
                  Output('line-table-btn-v', 'children', allow_duplicate=True),
                  Output('line-table-btn-h', 'children', allow_duplicate=True),
                  Input('line-table-btn-v', 'n_clicks'),
                  State('line-table-container-h', 'style'),
                  State('line-table-container-v', 'style'),
                  State('line-table-btn-h', 'children'),
                  prevent_initial_call=True)
    def toggle_line_param_v(btn_click, line_param_horizontal, line_param_vertical, btn_txt_2):
        return toggle_line_param(line_param_vertical, line_param_horizontal, btn_txt_2)

    def toggle_line_param(line_param_1, line_param_2, btn_txt_2):
        btn_txt_1 = 'Show Line Display Parameters'
        if line_param_1['display'] == 'none':
            line_param_1['display'] = 'flex'
            btn_txt_1 = 'Hide Line Display Parameters'
            if line_param_2['display'] == 'flex':
                line_param_2['display'] = 'none'
                btn_txt_2 = 'Show Line Display Parameters'
        else:
            line_param_1['display'] = 'none'
        return line_param_1, line_param_2, btn_txt_1, btn_txt_2

    return app.server

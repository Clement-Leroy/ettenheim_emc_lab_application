import dash
from dash import dcc, ctx, html, Input, Output, State, no_update, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

import pandas as pd
import pymysql

import base64
import datetime
from datetime import date
import plotly.graph_objects as go
import plotly.express as px
import math
import numpy as np
import time
import io

from sqlalchemy import create_engine, text

from application.dash_apps.assets.layout_emc_project_dashboard import *


def init_app(server):

    app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets, external_scripts=external_scripts, routes_pathname_prefix='/emc_project_dashboard/')

    app.layout = serve_layout
    cursor = connection.cursor()

    @app.callback(
        Output("loading-screen", 'children'),
        Output("loading-screen", 'style'),
        Input("interval", 'n_intervals'),
        State("loading-screen", 'style'),
        prevent_initial_call=True
    )

    def reset_loading(interval, loading_screen_style):

        if interval == 1:
            loading_screen_children, loading_screen_style['backgroundColor'] = ["No action selected"], '#119DFF'

        else:
            loading_screen_children, loading_screen_style = no_update, no_update

        return loading_screen_children, loading_screen_style

    @app.callback(
        Output("status_input", 'value', allow_duplicate=True),
        Output("status_description_input", 'value', allow_duplicate=True),
        Input("date_input", 'start_date'),
        Input("date_input", 'end_date'),
        Input("date_description_input", 'start_date'),
        Input("date_description_input", 'end_date'),
        State('project_window', 'is_open'),
        State('project_description', 'is_open'),
        prevent_initial_call=True
    )

    def update_project_status(date_input_start_date, date_input_end_date, date_description_input_start_date, date_description_input_end_date, project_window, project_description_is_open):

        if project_description_is_open is True or project_window is True:

            triggered_id = ctx.triggered_id

            date_today = datetime.datetime.today().date()

            if triggered_id == "date_input":

                date_input_start_date = date_input_start_date.split('T')[0]
                date_input_end_date = date_input_end_date.split('T')[0]

                start_date = date_input_start_date
                end_date = date_input_end_date

                status_input_value = compare_date(start_date, end_date, date_today)

                status_description_input_value = no_update

            else:

                date_description_input_start_date = date_description_input_start_date.split('T')[0]
                date_description_input_end_date = date_description_input_end_date.split('T')[0]

                start_date = date_description_input_start_date
                end_date = date_description_input_end_date

                status_input_value = no_update

                status_description_input_value = compare_date(start_date, end_date, date_today)

        else:
            raise PreventUpdate

        return status_input_value, status_description_input_value

    def compare_date(start_date, end_date, date_today):
        status = ''

        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

        if start_date <= date_today <= end_date:
            status = 'Ongoing'

        elif start_date > date_today:
            status = 'Upcoming'

        elif end_date < date_today:
            status = 'Completed'

        return status

    @app.callback(Output('project_description', 'is_open'),
              Output('project_description_label', 'children'),
              Output("project_list_table", 'rowData'),
              Output("project_table", 'rowData', allow_duplicate=True),

              Output("date_description_input", 'start_date'),
              Output("date_description_input", 'end_date'),
              Output("project_description_input", 'value'),
              Output("project_id_description_input", 'value'),
              Output("location_description_input", 'value'),
              Output("project_manager_description_input", 'value'),
              Output("category_description_input", 'value'),
              Output("type_description_input", 'value'),
              Output("client_description_input", 'value'),
              Output("PL_description_input", 'value'),
              Output("contact_input", 'value'),
              Output("quote_input", 'value'),
              Output("PO_input", 'value'),
              Output("draft_input", 'value'),
              Output("report_input", 'value'),
              Output("time_input", 'value'),
              Output("invoice_input", 'value'),
              Output("status_description_input", 'value'),
              Output("project_number", 'data'),

              Output("loading-screen", 'children', allow_duplicate=True),
              Output("loading-screen", 'style', allow_duplicate=True),
              Output("interval", 'n_intervals', allow_duplicate=True),

              Input("project_list_table", "cellRendererData"),
              Input("close_project_description_btn", "n_clicks"),
              Input("add_test_service_btn", "n_clicks"),
              Input("remove_test_service_btn", "n_clicks"),
              Input('cancel_project_description_btn', "n_clicks"),

              Input("project_table", 'cellValueChanged'),

              Input("type_description_input", 'value'),
              Input("client_description_input", 'value'),

              State('project_description', 'is_open'),
              State("project_list_table", 'rowData'),
              State("project_table", 'rowData'),

              State("date_description_input", 'start_date'),
              State("date_description_input", 'end_date'),
              State("project_description_input", 'value'),
              State("project_id_description_input", 'value'),
              State("location_description_input", 'value'),
              State("project_manager_description_input", 'value'),
              State("category_description_input", 'value'),
              State("PL_description_input", 'value'),
              State("contact_input", 'value'),
              State("quote_input", 'value'),
              State("PO_input", 'value'),
              State("draft_input", 'value'),
              State("report_input", 'value'),
              State("time_input", 'value'),
              State("invoice_input", 'value'),
              State("status_description_input", 'value'),

              State("loading-screen", 'children'),
              State("loading-screen", 'style'),
              State("project_number", 'data'),

              State('tabs', 'active_tab'),

              prevent_initial_call=True
              )
    def show_project(project_btn, ok_project_description_btn, add_test_service_btn, remove_test_service_btn,
                     cancel_project_description_btn, project_table_cellValueChanged, type_input, client_input,
                     project_description_isopen, project_list_table_rowData, project_table_rowData, start_date_input,
                     stop_date_input, project_input, project_id_input, location_input, project_manager_input,
                     category_input, PL_input, contact_input, quote_input, PO_input, draft_input,
                     report_input, time_input, invoice_input, status_input, loading_screen_children,
                     loading_screen_style, project_number, active_tab):

        project_description_label_children = no_update
        triggered_id = ctx.triggered_id

        if project_btn and triggered_id == 'project_list_table' and active_tab == 'project_list':
            data_project_tracker = pd.read_json(read_database("project_tracker"))
            data_project_description = pd.read_json(read_database("project_description"))

            selectedRow = data_project_tracker.iloc[int(project_btn['rowId'])]

            start_date_input, stop_date_input = selectedRow["Start Date"], selectedRow["End Date"]
            project_number = project_list_table_rowData[int(project_btn['rowId'])]['Number']
            project_input = selectedRow["Project"]
            project_id_input = selectedRow["Project ID"]
            location_input = selectedRow["Location"]
            project_manager_input = selectedRow["PM"]
            category_input = selectedRow["Category"]
            type_input = selectedRow["Typ"]
            client_input = selectedRow["Client"]
            PL_input = selectedRow["PL"]
            contact_input = selectedRow["Contact"]
            quote_input = selectedRow["Quote"]
            PO_input = selectedRow["PO"]
            draft_input = selectedRow["DRAFT"]
            report_input = selectedRow["Report"]
            invoice_input = selectedRow["Invoice"]
            status_input = selectedRow["Status"]

            n_intervals = 1

            project_description_label_children = "Project: " + project_list_table_rowData[int(project_btn['rowId'])][
                'Project'] if project_list_table_rowData[int(project_btn['rowId'])]['Project'] is not None else ''

            data_project_description = data_project_description[data_project_description['Number'] == project_number]

            data_project_description['Start Date'] = pd.to_datetime(data_project_description['Start Date']).dt.strftime(
                "%Y/%m/%d")

            data_project_description['End Date'] = pd.to_datetime(data_project_description['End Date']).dt.strftime(
                "%Y/%m/%d")

            data_project_description = data_project_description.to_dict('records')
            time = 0
            project_table_rowData = []

            for project_description in data_project_description:
                project_table_rowData.append(
                    {'Test_Service': project_description['Test Service'],
                     'Tester': project_description['Tester'],
                     'Location': project_description['Location2'],
                     'Start_Date': datetime.datetime.strptime(project_description['Start Date'],
                                                              '%Y/%m/%d').date() if type(
                         project_description['Start Date']) is str or math.isnan(
                         project_description['Start Date']) is not True else None,
                     'Stop_Date': datetime.datetime.strptime(project_description['End Date'],
                                                             '%Y/%m/%d').date() if type(
                         project_description['End Date']) is str or math.isnan(
                         project_description['End Date']) is not True else None,
                     'Hours': project_description['Hours'],
                     'Status': project_description['Notes']}
                )
                time = time + project_description['Hours']

            time_input = time

            project_description_isopen = True

        elif triggered_id == 'close_project_description_btn':

            try:
                project_description_isopen = False
                for index, project in enumerate(project_list_table_rowData):
                    if project['Number'] == project_number:
                        project = {
                            'Show': '>>',
                            'Start Date': datetime.datetime.fromisoformat(start_date_input).date(),
                            'End Date': datetime.datetime.fromisoformat(stop_date_input).date(),
                            'Location': location_input,
                            'Number': project_number,
                            'Project': project_input,
                            'Project ID': project_id_input,
                            'PM': project_manager_input,
                            'Category': category_input,
                            'Typ': type_input,
                            'Client': client_input,
                            'PL': PL_input,
                            'Work [hours]': time_input,
                            'Status': status_input
                        }

                        project_list_table_rowData[index] = project

                sql = "UPDATE project_tracker SET `Start Date` = %s, `End Date` = %s, Location = %s, Project = %s, `Project ID` = %s, PM = %s, Category = %s, Typ = %s, Client = %s, PL = %s, Contact = %s, Quote = %s, PO = %s, DRAFT = %s, Report = %s, `Work [hours]` = %s, Invoice = %s, Status = %s WHERE Number = %s"
                connection.ping(reconnect=True)
                cursor.execute(sql, (start_date_input, stop_date_input, location_input, project_input, project_id_input,
                                     project_manager_input, category_input, type_input, client_input, PL_input,
                                     contact_input, quote_input, PO_input, draft_input, report_input,
                                     time_input, invoice_input, status_input, project_number))
                connection.commit()

                data_project_description = pd.read_json(read_database("project_description"))
                data_project_description = data_project_description.to_dict('list')

                if project_number in data_project_description['Number']:
                    sql = "DELETE FROM project_description WHERE NUMBER = %s"
                    cursor.execute(sql, (project_number))
                    connection.commit()

                for test in project_table_rowData:
                    sql = "INSERT INTO `project_description` (Number, Project, `Test Service`, Tester, Location2, `Start Date`, `End Date`, Hours, Notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"

                    cursor.execute(sql, (
                        project_number, project_input, test['Test_Service'], test['Tester'], test['Location'],
                        test['Start_Date'], test['Stop_Date'], test['Hours'], test['Status']))

                # sql = "INSERT INTO `project_description` (Number, Project, `Test Service`, Tester, Location2, `Start Date`, `End Date`, Hours, Notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                # print(project_list_table_rowData[project_number - 1])
                # print(list(pd.DataFrame.from_records(project_list_table_rowData[project_number - 1]).itertuples(index=False, name=None)))
                # cursor.executemany(sql, list(pd.DataFrame.from_records(data_project_description).itertuples(index=False, name=None)))
                connection.commit()

            except:
                loading_screen_children, loading_screen_style['backgroundColor'] = [cross,
                                                                                    " Project failed to update"], 'red'

                raise PreventUpdate

            project_input = None
            project_id_input = None
            location_input = None
            project_manager_input = None
            category_input = None
            type_input = None
            client_input = None
            PL_input = None
            contact_input = ''
            quote_input = ''
            PO_input = None
            draft_input = None
            report_input = None
            time_input = 0
            invoice_input = None
            status_input = 'Ongoing'
            start_date_input, stop_date_input = None, None

            n_intervals = 0

            loading_screen_children, loading_screen_style['backgroundColor'] = [check,
                                                                                " Project successfully updated"], 'green'

        elif triggered_id == 'cancel_project_description_btn':

            project_input = None
            project_id_input = None
            location_input = None
            project_manager_input = None
            category_input = None
            type_input = None
            client_input = None
            PL_input = None
            contact_input = ''
            quote_input = ''
            PO_input = None
            draft_input = None
            report_input = None
            time_input = 0
            invoice_input = None
            status_input = 'Ongoing'
            start_date_input = stop_date_input = None

            project_description_isopen = False

            project_list_table_rowData = no_update

            n_intervals = 1

        elif triggered_id == 'type_description_input' or triggered_id == 'client_description_input':
            quote_input = add_quote(type_input, client_input)
            n_intervals = 1

        else:
            raise PreventUpdate

        return project_description_isopen, project_description_label_children, project_list_table_rowData, project_table_rowData, start_date_input, stop_date_input, project_input, project_id_input, location_input, project_manager_input, category_input, type_input, client_input, PL_input, contact_input, quote_input, PO_input, draft_input, report_input, time_input, invoice_input, status_input, project_number, loading_screen_children, loading_screen_style, n_intervals

    def add_quote(type_input, client_input):
        if type_input == 'Paid' and client_input == 'EXT':
            data_project_tracker = pd.read_json(read_database("project_tracker"))
            data_project_tracker = data_project_tracker[
                (data_project_tracker['Quote'].notnull()) & (data_project_tracker['Typ'] == 'Paid') & (
                        data_project_tracker['Client'] == 'EXT')]

            quote_number = data_project_tracker['Quote'].str[-3:].astype(int).max() + 1
            quote_input = "GER25EMC00" + str(quote_number) if quote_number < 10 else "GER25EMC0" + str(
                quote_number) if quote_number < 100 else "GER25EMC" + str(quote_number)
        else:
            quote_input = ''

        return quote_input

    @app.callback(
        Output('download_backup', 'data'),
        Output("loading-screen", 'children', allow_duplicate=True),
        Output("loading-screen", 'style', allow_duplicate=True),
        Output("interval", 'n_intervals', allow_duplicate=True),
        Input("save_backup", "n_clicks"),
        State("loading-screen", 'style'),
        prevent_initial_call=True)
    def save_backup(n_clicks, loading_screen_style):
        trigger_id = ctx.triggered_id
        if trigger_id == "save_backup":
            try:

                data_project_tracker = pd.read_json(read_database("project_tracker"))
                data_project_description = pd.read_json(read_database("project_description"))

                data_project_tracker['Start Date'] = pd.to_datetime(data_project_tracker['Start Date'])
                data_project_tracker['End Date'] = pd.to_datetime(data_project_tracker['End Date'])
                data_project_description['Start Date'] = pd.to_datetime(data_project_description['Start Date'])
                data_project_description['End Date'] = pd.to_datetime(data_project_description['End Date'])

                data_project_tracker['Start Date'] = data_project_tracker['Start Date'].astype(str)
                data_project_tracker['End Date'] = data_project_tracker['End Date'].astype(str)
                data_project_description['Start Date'] = data_project_description['Start Date'].astype(str)
                data_project_description['End Date'] = data_project_description['End Date'].astype(str)

                output = io.BytesIO()

                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:

                    data_project_tracker.to_excel(writer, sheet_name="Project Tracker", index=False, startrow=1,
                                                  header=False)
                    data_project_description.to_excel(writer, sheet_name="Project Description", index=False, startrow=1,
                                                      header=False)

                    wb = writer.book
                    ws1 = writer.sheets["Project Tracker"]
                    ws2 = writer.sheets["Project Description"]
                    header_format = wb.add_format({'bold': True})

                    def write_headers_autowidth(ws, df):
                        for i, col in enumerate(df.columns):
                            ws.write(0, i, col, header_format)
                            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                            ws.set_column(i, i, max_len)

                    write_headers_autowidth(ws1, data_project_tracker)
                    write_headers_autowidth(ws2, data_project_description)

                    for col_num, value in enumerate(data_project_description.columns.values):
                        ws2.write(0, col_num, value, header_format)

                    ws1.add_table(0, 0, len(data_project_tracker), len(data_project_tracker.columns) - 1, {
                        'name': "project_tracker",
                        'columns': [{'header': col} for col in data_project_tracker.columns],
                        'style': 'Table Style Medium 9'
                    })

                    ws2.add_table(0, 0, len(data_project_description), len(data_project_description.columns) - 1, {
                        'name': "project_description",
                        'columns': [{'header': col} for col in data_project_description.columns],
                        'style': 'Table Style Medium 9'
                    })

                output.seek(0)

                loading_screen_children, loading_screen_style['backgroundColor'] = [check,
                                                                                    " Backup successfully created"], 'green'

                return dcc.send_bytes(output.read(),
                                      'EMC_projects_backup.xlsx'), loading_screen_children, loading_screen_style, 0

            except:
                loading_screen_children, loading_screen_style['backgroundColor'] = [cross,
                                                                                    " Backup failed to create"], 'red'
                return None, loading_screen_children, loading_screen_style, 0
        else:
            raise PreventUpdate

    @app.callback(
        Output("loading-screen", 'children', allow_duplicate=True),
        Output("loading-screen", 'style', allow_duplicate=True),
        Output("interval", 'n_intervals', allow_duplicate=True),
        Input('upload-backup', "contents"),
        State("loading-screen", 'style'),
        prevent_initial_call=True)
    def load_backup(contents, loading_screen_style):

        trigger_id = ctx.triggered_id

        if trigger_id == 'upload-backup':

            try:

                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string)
                excel_file = io.BytesIO(decoded)

                df_dict = pd.read_excel(excel_file, sheet_name=None)
                sheet_names = list(df_dict.keys())
                data_project_tracker = df_dict[sheet_names[0]]
                data_project_description = df_dict[sheet_names[1]]

                data_project_tracker = data_project_tracker.map(lambda x: None if pd.isnull(x) else x)
                data_project_description = data_project_description.map(lambda x: None if pd.isnull(x) else x)

                connection.ping(reconnect=True)

                sql = ("DELETE FROM project_tracker")
                cursor.execute(sql)

                sql = ("DELETE FROM project_description")
                cursor.execute(sql)

                data_project_tracker = [tuple(row) for row in data_project_tracker.to_numpy()]

                sql = (
                    "INSERT INTO project_tracker (`Start Date`, `End Date`, Location, Number, Project, `Project ID`, PM, Category, Typ, Client, PL, Contact, Quote, Quote2, PO, DRAFT, Report, `Work [hours]`, Invoice, Status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
                cursor.executemany(sql, data_project_tracker)

                data_project_description = [tuple(row) for row in data_project_description.to_numpy()]

                sql = (
                    "INSERT INTO project_description (Number, Project, `Test Service`, Tester, Location2, `Start Date`, `End Date`, Hours, Notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)")
                cursor.executemany(sql, data_project_description)

                connection.commit()

                loading_screen_children, loading_screen_style['backgroundColor'] = [check,
                                                                                    " Backup successfully loaded"], 'green'

                return loading_screen_children, loading_screen_style, 0

            except:

                loading_screen_children, loading_screen_style['backgroundColor'] = [cross,
                                                                                    " Backup failed to load"], 'red'
                return loading_screen_children, loading_screen_style, 0
        else:
            raise PreventUpdate

    @app.callback(
        Output("project_table", 'rowData', allow_duplicate=True),
        Output("time_input", 'value', allow_duplicate=True),
        Input("add_test_service_btn", "n_clicks"),
        Input("remove_test_service_btn", "n_clicks"),
        Input("project_table", 'cellValueChanged'),
        State("project_table", 'rowData'),
        State("project_table", 'selectedRows'),
        prevent_initial_call=True)
    def update_project_description_table(add_test_service_btn, remove_test_service_btn, project_table_cellValueChanged,
                                         project_table_rowData, project_table_selectedRows):
        triggered_id = ctx.triggered_id
        time_input = no_update
        if triggered_id == 'add_test_service_btn':
            project_table_rowData.append(
                {'Test_Service': None,
                 'Tester': None,
                 'Location': None,
                 'Start_Date': date.today(),
                 'Stop_Date': date.today(),
                 'Hours': 0,
                 'Status': 'ONGOING'}
            )
        elif triggered_id == 'remove_test_service_btn' and project_table_selectedRows is not None and project_table_selectedRows != []:
            for test_service in project_table_selectedRows:
                project_table_rowData.remove(test_service)
            time_input = 0
            for project_description in project_table_rowData:
                time_input = time_input + project_description['Hours']

        elif triggered_id == 'project_table' and project_table_cellValueChanged is not None and (
                project_table_cellValueChanged[0]['colId'] == 'Start_Date' or project_table_cellValueChanged[0][
            'colId'] == 'Stop_Date'):
            start_date = datetime.datetime.strptime(project_table_cellValueChanged[0]['data']['Start_Date'],
                                                    '%Y-%m-%d').date() if project_table_cellValueChanged[0]['data'][
                                                                              'Start_Date'] is not None else None
            stop_date = datetime.datetime.strptime(project_table_cellValueChanged[0]['data']['Stop_Date'],
                                                   '%Y-%m-%d').date() if project_table_cellValueChanged[0]['data'][
                                                                             'Stop_Date'] is not None else None
            if start_date is not None and stop_date is not None:
                if start_date > date.today():
                    project_table_rowData[project_table_cellValueChanged[0]['rowIndex']]['Status'] = 'UPCOMING'
                elif stop_date < date.today():
                    project_table_rowData[project_table_cellValueChanged[0]['rowIndex']]['Status'] = 'COMPLETED'
                else:
                    project_table_rowData[project_table_cellValueChanged[0]['rowIndex']]['Status'] = 'ONGOING'
            else:
                project_table_rowData[project_table_cellValueChanged[0]['rowIndex']]['Status'] = ''

        elif triggered_id == 'project_table' and project_table_cellValueChanged[0]['colId'] == 'Hours':
            time_input = 0
            for project_description in project_table_rowData:
                time_input = time_input + project_description['Hours']

        else:
            raise PreventUpdate
        return project_table_rowData, time_input

    # @callback(Output('project_list_tab', 'style', allow_duplicate=True),
    #               Output('project_timeline_tab', 'style', allow_duplicate=True),
    #               Output('graph_tab', 'style', allow_duplicate=True),
    #               Output("btn-project-list", 'className'),
    #               Output("btn-staff-timeline", 'className'),
    #               Output("btn_graph_report", 'className'),
    #               Input("btn-project-list", 'n_clicks'),
    #               Input("btn-staff-timeline", 'n_clicks'),
    #               Input("btn_graph_report", 'n_clicks'),
    #               State('project_list_tab', 'style'),
    #               State('project_timeline_tab', 'style'),
    #               State('graph_tab', 'style'),
    #               prevent_initial_call=True)
    #
    # def show_table(btn_project_list, btn_staff_timeline, btn_graph_tab, project_list_tab_style,
    #                project_timeline_tab_style, graph_tab_style):
    #     project_list_tab_className, project_timeline_tab_className, graph_tab_className = "menu_btn", "menu_btn", "menu_btn"
    #     triggered_id = ctx.triggered_id
    #     if triggered_id == 'btn-project-list':
    #         project_list_tab_style['display'] = 'block'
    #         project_timeline_tab_style['display'] = 'none'
    #         graph_tab_style['display'] = 'none'
    #         project_list_tab_className = "active_menu_btn"
    #     elif triggered_id == 'btn-staff-timeline':
    #         project_list_tab_style['display'] = 'none'
    #         project_timeline_tab_style['display'] = 'block'
    #         graph_tab_style['display'] = 'none'
    #         project_timeline_tab_className = "active_menu_btn"
    #     elif triggered_id == 'btn_graph_report':
    #         project_list_tab_style['display'] = 'none'
    #         project_timeline_tab_style['display'] = 'none'
    #         graph_tab_style['display'] = 'block'
    #         graph_tab_className = "active_menu_btn"
    #     else:
    #         raise PreventUpdate
    #     return project_list_tab_style, project_timeline_tab_style, graph_tab_style, project_list_tab_className, project_timeline_tab_className, graph_tab_className

    @app.callback(Output('project_window', 'is_open', allow_duplicate=True),
              Output("loading-screen", 'children', allow_duplicate=True),
              Output("loading-screen", 'style', allow_duplicate=True),
              Output("project_input", 'value', allow_duplicate=True),
              Output("project_id_input", 'value', allow_duplicate=True),
              Output("location_input", 'value', allow_duplicate=True),
              Output("project_manager_input", 'value', allow_duplicate=True),
              Output("category_input", 'value', allow_duplicate=True),
              Output("type_input", 'value', allow_duplicate=True),
              Output("client_input", 'value', allow_duplicate=True),
              Output("PL_input", 'value', allow_duplicate=True),
              Output("contact_input", 'value', allow_duplicate=True),
              Output("quote_input", 'value', allow_duplicate=True),
              Output("PO_input", 'value', allow_duplicate=True),
              Output("draft_input", 'value', allow_duplicate=True),
              Output("report_input", 'value', allow_duplicate=True),
              Output("time_input", 'value', allow_duplicate=True),
              Output("invoice_input", 'value', allow_duplicate=True),
              Output("date_input", 'start_date', allow_duplicate=True),
              Output("date_input", 'end_date', allow_duplicate=True),
              Output("project_input", "invalid"),
              Output("status_input", 'value'),
              Input('add_project', 'n_clicks'),
              Input('ok_project_btn', 'n_clicks'),
              Input('cancel_btn', 'n_clicks'),
              State("loading-screen", 'style'),
              State("project_input", 'value'),
              prevent_initial_call=True)
    def display_project_window(add_project_btn, ok_btn, cancel_btn, loading_screen_style, project_input):
        triggered_id = ctx.triggered_id

        if triggered_id == 'add_project':
            project_window_isopen = True
            project_input, project_id_input, location_input, project_manager_input, category_input, type_input, client_input, PL_input, contact_input, quote_input, PO_input, draft_input, report_input, time_input, invoice_input, start_date_input, stop_date_input, project_input_invalid, status_input = '', '', '', 'JS', 'Internal', 'Paid', 'EXT', 'C1 AC/DC - Lighting', '', '', '', '', '', None, '', today.strftime('%Y-%m-%d'), tomorrow.strftime('%Y-%m-%d'), None, 'Ongoing'
            loading_screen_children, loading_screen_style['backgroundColor'] = ["No action selected"], '#119DFF'

        elif triggered_id == 'ok_project_btn':
            if project_input == '':
                project_window_isopen = True
                project_input_invalid = True
                project_input = project_id_input = location_input = project_manager_input = category_input = type_input = client_input = PL_input = contact_input = quote_input = PO_input = draft_input = report_input = time_input = invoice_input = start_date_input = stop_date_input = status_input = no_update

            else:
                project_window_isopen = False
                project_input_invalid = False
                project_input, project_id_input, location_input, project_manager_input, category_input, type_input, client_input, PL_input, contact_input, quote_input, PO_input, draft_input, report_input, time_input, invoice_input, start_date_input, stop_date_input, status_input = '', '', '', None, None, None, None, None, '', '', '', '', '', None, '', today.strftime('%Y-%m-%d'), tomorrow.strftime('%Y-%m-%d'), 'Ongoing'

            loading_screen_children, loading_screen_style['backgroundColor'] = no_update, no_update

        elif triggered_id == 'cancel_btn':
            project_window_isopen = False
            project_input, project_id_input, location_input, project_manager_input, category_input, type_input, client_input, PL_input, contact_input, quote_input, PO_input, draft_input, report_input, time_input, invoice_input, start_date_input, stop_date_input, project_input_invalid, status_input = '', '', '', None, None, None, None, None, '', '', '', '', '', None, '', today.strftime('%Y-%m-%d'), tomorrow.strftime('%Y-%m-%d'), None, 'Ongoing'
            loading_screen_children, loading_screen_style['backgroundColor'] = no_update, no_update

        else:
            raise PreventUpdate

        return project_window_isopen, loading_screen_children, loading_screen_style, project_input, project_id_input, location_input, project_manager_input, category_input, type_input, client_input, PL_input, contact_input, quote_input, PO_input, draft_input, report_input, time_input, invoice_input, start_date_input, stop_date_input, project_input_invalid, status_input

    @app.callback(Output("project_list_table", 'rowData', allow_duplicate=True),
              Output('add_project', 'n_clicks'),
              Output("loading-screen", 'children', allow_duplicate=True),
              Output("loading-screen", 'style', allow_duplicate=True),
              Output("interval", 'n_intervals', allow_duplicate=True),
              Input('ok_project_btn', 'n_clicks'),
              State('add_project', 'n_clicks'),
              State("project_list_table", 'rowData'),
              State("project_list_table", 'selectedRows'),
              State("loading-screen", 'style'),
              State("project_input", 'value'),
              State("project_id_input", 'value'),
              State("location_input", 'value'),
              State("project_manager_input", 'value'),
              State("category_input", 'value'),
              State("type_input", 'value'),
              State("client_input", 'value'),
              State("PL_input", 'value'),
              State("contact_input", 'value'),
              State("quote_input", 'value'),
              State("PO_input", 'value'),
              State("draft_input", 'value'),
              State("report_input", 'value'),
              State("time_input", 'value'),
              State("invoice_input", 'value'),
              State("status_input", 'value'),
              State("date_input", 'start_date'),
              State("date_input", 'end_date'),
              prevent_initial_call=True)
    def add_project(submit_btn, add_project, project_list_table_rowData, project_list_table_selectedRows,
                    loading_screen_style, project_input, project_id_input, location_input, project_manager_input,
                    category_input, type_input, client_input, PL_input, contact_input, quote_input, PO_input,
                    draft_input, report_input, time_input, invoice_input, status_input, start_date_input,
                    stop_date_input):

        if submit_btn and project_input != '':
            # try:
            if start_date_input is None:
                start_date_input = date.today()
            if stop_date_input is None:
                stop_date_input = date.today()

            if add_project == 1:

                number = len(project_list_table_rowData) + 1
                new_project = {
                    'Show': '>>',
                    'Start Date': start_date_input,
                    'End Date': stop_date_input,
                    'Location': location_input,
                    'Number': number,
                    'Project': project_input,
                    'Porject ID': project_id_input,
                    'PM': project_manager_input,
                    'Category': category_input,
                    'Typ': type_input,
                    'Client': client_input,
                    'PL': PL_input,
                    "Work [hours]": 0,
                    "Status": status_input
                }
                project_list_table_rowData.append(new_project)

                quote_input = add_quote(type_input, client_input)

                # start_date_input = start_date_input.isoformat() if type(start_date_input) is not str else start_date_input
                # stop_date_input = stop_date_input.isoformat() if type(stop_date_input) is not str else stop_date_input

                sql = (
                    "INSERT INTO project_tracker (`Start Date`, `End Date`, Location, Number, Project, `Project ID`, PM, Category, Typ, Client, PL, Contact, Quote, PO, DRAFT, Report, `Work [hours]`, Invoice, Status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
                connection.ping(reconnect=True)
                cursor.execute(sql, (
                    str(start_date_input), str(stop_date_input), location_input, number, project_input,
                    project_id_input, project_manager_input, category_input, type_input, client_input, PL_input,
                    contact_input, quote_input, PO_input, draft_input, report_input, time_input, invoice_input, status_input))
                connection.commit()

            if add_project == 1:
                loading_screen_children, loading_screen_style['backgroundColor'] = [check,
                                                                                    " Project successfully added"], 'green'
            else:
                loading_screen_children, loading_screen_style['backgroundColor'] = [check,
                                                                                    " Project successfully modified"], 'green'

            # except:
            #     project_list_table_rowData = no_update
            #
            #     if add_project == 1:
            #         loading_screen_children, loading_screen_style['backgroundColor'] = [cross,
            #                                                                             " Project failed to add"], 'red'
            #     else:
            #         loading_screen_children, loading_screen_style['backgroundColor'] = [cross,
            #                                                                             " Project failed to modify"], 'red'

            return project_list_table_rowData, 0, loading_screen_children, loading_screen_style, 0

        raise PreventUpdate

    @app.callback(Output('remove_window', 'is_open', allow_duplicate=True),
              Output('project_description', 'is_open', allow_duplicate=True),
              Output("loading-screen", 'children', allow_duplicate=True),
              Input('remove_project', 'n_clicks'),
              Input('yes_remove_btn', 'n_clicks'),
              Input('no_remove_btn', 'n_clicks'),
              prevent_initial_call=True)

    def confirm_remove_window(remove_project, yes_remove_btn, no_remove_btn):
        triggered_id = ctx.triggered_id

        if triggered_id == 'remove_project':
            remove_window_isopen = True
            project_description_isopen = False
            loading_screen_children = no_update

        elif triggered_id == 'yes_remove_btn':
            remove_window_isopen = False
            project_description_isopen = False
            loading_screen_children = no_update

        elif triggered_id == 'no_remove_btn':
            remove_window_isopen = False
            project_description_isopen = True
            loading_screen_children = no_update

        else:
            raise PreventUpdate

        return remove_window_isopen, project_description_isopen, loading_screen_children

    @app.callback(Output("project_list_table", 'rowData', allow_duplicate=True),
              Output("loading-screen", 'children', allow_duplicate=True),
              Output("loading-screen", 'style', allow_duplicate=True),
              Output('project_description', 'style', allow_duplicate=True),
              Output("interval", 'n_intervals', allow_duplicate=True),
              Input('yes_remove_btn', 'n_clicks'),
              State("project_list_table", 'rowData'),
              State("loading-screen", 'style'),
              State("project_number", 'data'),
              State('project_description', 'is_open'),
              prevent_initial_call=True)
    def remove_project(remove_project, project_list_table_rowData, loading_screen_style, project_number,
                       project_description_isopen):
        if remove_project != 0:
            try:
                for project in project_list_table_rowData:
                    if project['Number'] == project_number:
                        project_list_table_rowData.remove(project)
                        break

                connection.ping(reconnect=True)
                sql = "DELETE FROM project_tracker WHERE Number = %s"
                cursor.execute(sql, (project_number))
                sql = "DELETE FROM project_description WHERE Number = %s"
                cursor.execute(sql, (project_number))
                connection.commit()

                # for row_index in range(index, len(project_list_table_rowData)):
                #     project_list_table_rowData[row_index]['Number'] = row_index + 1
                #
                #     sql = "UPDATE project_tracker SET Number = %s WHERE Number = %s"
                #     cursor.execute(sql, (row_index + 1, row_index + 2))
                #     sql = "UPDATE project_description SET Number = %s WHERE Number = %s"
                #     cursor.execute(sql, (row_index + 1, row_index + 2))
                #     connection.commit()

                project_description_isopen = False

                loading_screen_children, loading_screen_style['backgroundColor'] = [check,
                                                                                    " Project successfully removed"], 'green'

            except:
                loading_screen_children, loading_screen_style['backgroundColor'] = [cross,
                                                                                    " Project remove failed"], 'red'

        else:
            raise PreventUpdate

        return project_list_table_rowData, loading_screen_children, loading_screen_style, project_description_isopen, 0


    @app.callback(Output("project_timeline", 'figure', allow_duplicate=True),
              Output('start_stop_date_timeline_input', 'start_date'),
              Output('start_stop_date_timeline_input', 'end_date'),
              Input('start_stop_date_timeline_input', 'start_date'),
              Input('start_stop_date_timeline_input', 'end_date'),
              Input("project_timeline", 'relayoutData'),
              Input('timeline_checklist', 'value'),
              State("project_timeline", 'figure'),
              prevent_initial_call=True)
    def update_timeline(start_date_timeline_input, stop_date_timeline_input, project_timeline_relayoutData,
                        timeline_checklist_value, project_timeline_figure):

        triggered_id = ctx.triggered_id

        if triggered_id == 'start_stop_date_timeline_input':

            start_date_timeline_input, stop_date_timeline_input = start_date_timeline_input.split('T')[0], stop_date_timeline_input.split('T')[0]

            if len(start_date_timeline_input.split('-')[0]) != 4:
                start_date_timeline_input = f"{start_date_timeline_input.split('-')[2]}-{start_date_timeline_input.split('-')[1]}-{start_date_timeline_input.split('-')[0]}"
            if len(stop_date_timeline_input.split('-')[0]) != 4:
                stop_date_timeline_input = f"{stop_date_timeline_input.split('-')[2]}-{stop_date_timeline_input.split('-')[1]}-{stop_date_timeline_input.split('-')[0]}"

            start_date_timeline_input, stop_date_timeline_input = datetime.datetime.strptime(start_date_timeline_input,'%Y-%m-%d'), datetime.datetime.strptime(
                stop_date_timeline_input, '%Y-%m-%d')
            lab_member_list = lab_member_list_fct(read_database("project_tracker"))

            l = [item[0] + item.split(' ')[-1][0] for item in timeline_checklist_value]
            d = lab_member_list.copy()

            for k in d:
                if k not in l:
                    del lab_member_list[k]

            project_timeline_figure = create_project_timeline(lab_member_list, start_date_timeline_input,
                                                              stop_date_timeline_input)

            project_timeline_figure['layout']['xaxis']['range'] = [start_date_timeline_input, stop_date_timeline_input]

        elif triggered_id == 'project_timeline':
            start_date_timeline_input, stop_date_timeline_input = project_timeline_figure['layout']['xaxis']['range']
            start_date_timeline_input, stop_date_timeline_input = start_date_timeline_input.split(' ')[0], \
                stop_date_timeline_input.split(' ')[0]

        elif triggered_id == 'timeline_checklist' or triggered_id == 'project_list_table':
            for index, value in enumerate(timeline_checklist_value):
                timeline_checklist_value[index] = value.split(' ')[0][0] + value.split(' ')[1][0]

            lab_member_list = lab_member_list_fct(read_database("project_tracker"))
            for lab_member in list(lab_member_list.keys()):
                if lab_member not in timeline_checklist_value:
                    del lab_member_list[lab_member]

            project_timeline_figure = create_project_timeline(lab_member_list, start_date_timeline_input, stop_date_timeline_input)
            project_timeline_figure['layout']['xaxis']['range'] = [start_date_timeline_input, stop_date_timeline_input]

        else:
            raise PreventUpdate

        return project_timeline_figure, start_date_timeline_input, stop_date_timeline_input

    @app.callback(Output('chart', 'figure'),
              Input("type_chart_input", 'value'),
              Input("label_chart_input_1", 'value'),
              Input("label_chart_input_2", 'value'),
              Input("value_chart_input", 'value'),
              Input("chart_date", 'start_date'),
              Input("chart_date", 'end_date'),
              prevent_initial_call=True)
    def update_chart(type_chart_input_value, label_pie_chart_input_value_1, label_pie_chart_input_value_2,
                     value_pie_chart_input_value, chart_start_date, chart_end_date):

        time.sleep(0.5)
        chart_start_date, chart_end_date = np.datetime64(chart_start_date), np.datetime64(chart_end_date)
        chart_figure = create_chart_figure(type_chart_input_value, label_pie_chart_input_value_1,
                                           label_pie_chart_input_value_2, value_pie_chart_input_value, chart_start_date,
                                           chart_end_date)

        if type_chart_input_value == 'Pie chart':
            chart_figure['layout']['legend']['x'] = 0.9
            chart_figure['layout']['title']['x'] = 0.6
        else:
            chart_figure['layout']['legend']['x'] = 1
            chart_figure['layout']['title']['x'] = 0.5
        return chart_figure

    return app.server
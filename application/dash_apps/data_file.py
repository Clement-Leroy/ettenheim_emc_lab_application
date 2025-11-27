import dash
from dash.exceptions import PreventUpdate
import os
import io
from application.celery_task import *

from application.dash_apps.assets.layout_data_file import *


external_scripts = ["https://cdnjs.cloudflare.com/ajax/libs/jquery/1.12.1/jquery.min.js",
                    "https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.1/jquery-ui.min.js",
                    'https://trentrichardson.com/examples/timepicker/jquery-ui-timepicker-addon.js']

external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://code.jquery.com/ui/1.13.3/themes/base/jquery-ui.css', 'https://use.fontawesome.com/releases/v5.15.4/css/all.css']

def init_app(server):
    app = dash.Dash(server=server, url_base_pathname='/data_file/', assets_folder='asset', external_stylesheets=[dbc.themes.BOOTSTRAP], prevent_initial_callbacks=True)

    app.layout = html.Div(form, style={'padding': '20px 20px'}), dcc.Store(id='input-contents', data={}), dcc.Download(id="download"), dcc.Store(id='task-id', data=None), dcc.Interval(id='check-task', interval=5000, disabled=True)

    result_path = "/tmp/processed_file"

    @app.callback(Output('file-table', 'rowData'),
                  Output('input-contents', 'data'),
                  Input('upload_file', 'filename'),
                  Input('upload_file', 'contents'),
                  State('file-table', 'rowData'),
                  State('input-contents', 'data'))
    def file_list(filenames, contents, rowdata, input_content):

        for i, filename in enumerate(filenames):
            if filename.endswith(('.xls', '.xlsx', '.csv', '.parquet', '.db')):
                content_type, content_string = contents[i].split(',')
                input_content[filename.split('/')[-1]] = content_string

            elif filename.endswith(('.zip')):
                content_type, content_string = contents[i].split(',')
                uploaded_content = io.BytesIO()
                uploaded_content.write(io.BytesIO(base64.b64decode(content_string)).getvalue())
                uploaded_content.seek(0)
                with zipfile.ZipFile(uploaded_content, 'r') as z:
                    filenames = filenames + z.namelist()
                    for file_name in z.namelist():
                        if file_name.lower().endswith(('.xls', '.xlsx', '.csv', '.parquet', '.db')):
                            with z.open(file_name) as f:
                                file_name = file_name.split('/')[-1]
                                input_content[file_name] = base64.b64encode(f.read()).decode('utf-8')

        for filename in filenames:
            if filename.endswith(('.xls', '.xlsx', '.csv', '.parquet', '.db')):

                _, extension = os.path.splitext(filename)

                if extension == '.xlsx' or extension == '.xlsm':
                    type = 'Excel'
                elif extension == '.csv':
                    type = 'CSV'
                elif extension == '.parquet':
                    type = 'Parquet'
                elif extension == '.db':
                    type = 'DB'

                new_file = {
                    'name': filename.split('/')[-1],
                    'type': type
                }

                rowdata.append(new_file)

        return rowdata, input_content

    @app.callback(Output('file-table', 'rowData', allow_duplicate=True),
                  Output('input-contents', 'data', allow_duplicate=True),
                  Input('remove-btn', 'n_clicks'),
                  State('file-table', 'rowData'),
                  State('file-table', 'selectedRows'),
                  State('input-contents', 'data'))
    def remove_file(remove_btn, rowData, selectedRows, input_contents):

        if selectedRows:
            for row in selectedRows:

                rowData.remove(row)
                input_contents.pop(row['name'])

            return rowData, input_contents

        else:
            raise PreventUpdate

    @app.callback(Output('task-id', 'data'),
                  Output('check-task', 'disabled'),
                  Output('file-table', 'rowData', allow_duplicate=True),
                  Output('input-contents', 'data', allow_duplicate=True),
                  Output('convert-btn', 'children', allow_duplicate=True),
                  Output('convert-btn', 'disabled', allow_duplicate=True),
                  Input('convert-btn', 'n_clicks'),
                  State('new-type', 'value'),
                  State('input-contents', 'data'))
    def convert(convert_btn, type, input_contents):

        if input_contents != {}:
            type = '.db' if type == 'SQLite' else '.' + type.lower()
            print(type)
            task = process_multiprocessing.delay(input_contents, result_path, type)
            print(task.id)
            return task.id, False, [], {}, [dbc.Spinner(color='light', size='md'), '   Processing data, it can take a few minutes...'], True
        else:
            raise PreventUpdate

    @app.callback(Output('download', 'data'),
                  Output('check-task', 'disabled', allow_duplicate=True),
                  Output('task-id', 'data', allow_duplicate=True),
                  Output('convert-btn', 'children', allow_duplicate=True),
                  Output('convert-btn', 'disabled', allow_duplicate=True),
                  Input('check-task', 'n_intervals'),
                  State('task-id', 'data'),
                  State('check-task', 'disabled'),
                  State('new-type', 'value'),
                  prevent_initial_call=True)
    def poll_status(n_intervals, task_id, disabled, type):
        print(task_id, disabled)
        try:

            task = process_multiprocessing.AsyncResult(task_id)
            print(task.state)
            print(task.state == 'SUCCESS')

            if task.state == 'PENDING' or task.state == 'STARTED':
                print('check')
                return None, False, no_update, no_update, no_update

            elif task.state == 'SUCCESS':
                print('download')
                print(result_path)
                print(type)
                if type =='SQLite':
                    download_path = result_path + '.db'
                    filename = 'processed_data.db'
                else:
                    download_path = result_path + '.zip'
                    filename = 'processed_data.zip'
                print(download_path, filename)
                return dcc.send_file(path=download_path, filename=filename), True, None, ['Convert'], False
            # else:
            #     raise PreventUpdate
        except Exception as e:
            print(e)
            return None, True, None, ['Convert'], False

    return app.server
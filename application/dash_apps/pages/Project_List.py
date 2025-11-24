from application.dash_apps.emc_projects_dashboard import *

dash.register_page(__name__, path='/', name='Project List')

def get_layout():

    layout = html.Div(
        [project_list_btn, project_list, project_description, project_window, remove_window], id='project_list_tab',
        style={'display': 'block', 'margin-left': 20, 'margin-right': 20})
    return layout

layout = get_layout

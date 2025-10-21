from application.dash_apps.emc_projects_dashboard import *

dash.register_page(__name__, path='/graphs')

def get_layout():

    layout = html.Div(
        [chart_graph], id='graph_tab',
        style={'display': 'block', 'margin-left': 20, 'margin-right': 20})

    return layout

layout = get_layout
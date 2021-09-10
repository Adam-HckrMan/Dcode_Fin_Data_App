import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
import plotly.express as px

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

const PORT = process.env.PORT || '8080'
app = express();
app.set("port", PORT);


# This server line allows Heroku to deploy it online instead of it being generated on a local host
server = app.server

egx_df = pd.read_excel('C:\Users\Adam\Desktop\Dcode App\EGX100_financial_statements/Annual_FS-07092021234959.xlsx')
egx_df[['ticker','index','sector','statement','period']] = egx_df[['ticker','index','sector','statement','period']].fillna(method="pad")
egx_df.set_index('item',inplace=True)

available_indicators = egx_df.index.unique()
available_indices = egx_df['index'].unique()

sectors_list = egx_df['sector'].unique()
available_sectors = [{'label': i, 'value': i} for i in sorted(sectors_list)]
select_all = [{'label' : '(Select All)', 'value' : 'All'}]
available_sectors = select_all + available_sectors

app.layout = html.Div([

    html.Div([

        html.Div([
            dcc.Checklist(
                id = 'crossfilter-index-column',
                options = [{"label":i,"value":i} for i in available_indices],
                value = ['EGX 100'],
            )],
            style={'width': '11%', 'display': 'inline-block', 'border': '1px solid lightgrey'}),
        html.Div([
            dcc.Dropdown(
                id = 'crossfilter-sector-column',
                options = available_sectors,
                multi = True,
                value = [''],
                placeholder = "Select Sectors (leave blank to include all)"
            )],
            style={'width': '87%', 'display': 'inline-block'}) 
            ], style={
                'padding': '10px 5px'}),

    html.Div([

        html.Div([
            dcc.Dropdown(
                id='crossfilter-xaxis-column',
                options=[{'label': i, 'value': i} for i in available_indicators],
                value='Net Profit Margin',
                placeholder = "Select Financial Metric"
            ),
            dcc.RadioItems(
                id='crossfilter-xaxis-type',
                options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                value='Linear',
                labelStyle={'display': 'inline-block', 'marginTop': '5px'}
            )
        ],
        style={'width': '49%', 'display': 'inline-block'}),

        html.Div([
            dcc.Dropdown(
                id='crossfilter-yaxis-column',
                options=[{'label': i, 'value': i} for i in available_indicators],
                value='Total Revenue',
                placeholder = "Select Financial Metric"
            ),
            dcc.RadioItems(
                id='crossfilter-yaxis-type',
                options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                value='Linear',
                labelStyle={'display': 'inline-block', 'marginTop': '5px'}
            )
        ], style={'width': '49%', 'float': 'right', 'display': 'inline-block'})
    ], style={
        'padding': '10px 5px'
    }),

    html.Div([
        dcc.Graph(
            id='crossfilter-indicator-scatter',
            hoverData={'points': [{'customdata': 'FWRY.CA'}]}
        )
    ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
    html.Div([
        dcc.Graph(id='x-time-series'),
        dcc.Graph(id='y-time-series'),
    ], style={'display': 'inline-block', 'width': '49%'}),

    html.Div(dcc.Slider(
        id='crossfilter-year--slider',
        # below is very inefficient since after december passes
        # [-2] will refer to 2020 while last will be 2021. 
        min=egx_df.columns[-6],
        max=egx_df.columns[-2],
        value=egx_df.columns[-2],
        marks={str(year): str(year) for year in egx_df.columns[-6:-1]},
        step=None
    ), style={'width': '49%', 'padding': '0px 20px 20px 20px'})
])


@app.callback(
    dash.dependencies.Output('crossfilter-indicator-scatter', 'figure'),
    [dash.dependencies.Input('crossfilter-xaxis-column', 'value'),
    dash.dependencies.Input('crossfilter-yaxis-column', 'value'),
    dash.dependencies.Input('crossfilter-xaxis-type', 'value'),
    dash.dependencies.Input('crossfilter-yaxis-type', 'value'),
    dash.dependencies.Input('crossfilter-year--slider', 'value'),
    dash.dependencies.Input('crossfilter-sector-column','value'),
    dash.dependencies.Input('crossfilter-index-column','value')])
def update_graph(xaxis_column_name, yaxis_column_name, 
            xaxis_type, yaxis_type, 
            year_value, selected_sectors,selected_indices):

    # print(xaxis_column_name, yaxis_column_name, 
    #         xaxis_type, yaxis_type, 
    #         year_value, selected_sectors,sep="\n\n")
 
    if selected_indices == ['EGX 30']:
        egx_index_df = egx_df.loc[egx_df['index'].isin(selected_indices)]
    else:
        egx_index_df = egx_df.copy()

    if selected_sectors == [] or any(sector in selected_sectors for sector in ["All","",None]):
        egx_sector_df = egx_index_df.copy()
    else:
        egx_sector_df = egx_index_df.loc[egx_df['sector'].isin(selected_sectors)]

    dff = egx_sector_df[['ticker',year_value]]

    if len(dff['ticker'].unique()) > 1:
        x = dff.loc[xaxis_column_name, year_value].reset_index(drop=True)
        y = dff.loc[yaxis_column_name, year_value].reset_index(drop=True)
        hover_name = dff.loc[yaxis_column_name,'ticker'].reset_index(drop=True)
    else:
        x = pd.Series(dff.loc[xaxis_column_name, year_value])
        y = pd.Series(dff.loc[yaxis_column_name, year_value])
        hover_name = pd.Series(dff.loc[yaxis_column_name,'ticker'])
    
    # print(x,y,hover_name,sep="\n\n")

    df = pd.concat([x,y,hover_name],axis=1)
    df.columns = [xaxis_column_name,yaxis_column_name,'ticker']

    fig = px.scatter(df,
            x=xaxis_column_name,
            y=yaxis_column_name,
            hover_name='ticker'
            )

    fig.update_traces(customdata=hover_name)

    fig.update_xaxes(title=xaxis_column_name, type='linear' if xaxis_type == 'Linear' else 'log')

    fig.update_yaxes(title=yaxis_column_name, type='linear' if yaxis_type == 'Linear' else 'log')

    fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    return fig


def create_time_series(dff, axis_type, title):

    fig = px.scatter(dff, x='Year', y='Value')

    fig.update_traces(mode='lines+markers')

    fig.update_xaxes(showgrid=False)

    fig.update_yaxes(type='linear' if axis_type == 'Linear' else 'log')

    fig.add_annotation(x=0, y=0.85, xanchor='left', yanchor='bottom',
                    xref='paper', yref='paper', showarrow=False, align='left',
                    text=title)

    fig.update_layout(height=225, margin={'l': 20, 'b': 30, 'r': 10, 't': 10})

    return fig


@app.callback(
    dash.dependencies.Output('x-time-series', 'figure'),
    [dash.dependencies.Input('crossfilter-indicator-scatter', 'hoverData'),
    dash.dependencies.Input('crossfilter-xaxis-column', 'value'),
    dash.dependencies.Input('crossfilter-xaxis-type', 'value')])
def update_x_timeseries(hoverData, xaxis_column_name, axis_type):
    axis_type = "Linear"
    ticker_name = hoverData['points'][0]['customdata']
    dff = egx_df[egx_df['ticker'] == ticker_name]
    dff = dff.loc[xaxis_column_name].tail(6)
    dff = dff.to_frame().reset_index()
    dff.columns = ['Year','Value']
    title = '<b>{}</b><br>{}'.format(ticker_name, xaxis_column_name)
    return create_time_series(dff, axis_type, title)


@app.callback(
    dash.dependencies.Output('y-time-series', 'figure'),
    [dash.dependencies.Input('crossfilter-indicator-scatter', 'hoverData'),
    dash.dependencies.Input('crossfilter-yaxis-column', 'value'),
    dash.dependencies.Input('crossfilter-yaxis-type', 'value')])
def update_y_timeseries(hoverData, yaxis_column_name, axis_type):
    axis_type = "Linear"
    ticker_name = hoverData['points'][0]['customdata']
    dff = egx_df[egx_df['ticker'] == ticker_name]
    dff = dff.loc[yaxis_column_name].tail(6)
    dff = dff.to_frame().reset_index()
    dff.columns = ['Year','Value']
    return create_time_series(dff, axis_type, yaxis_column_name)


if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)

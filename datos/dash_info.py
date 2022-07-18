import numpy as np
import pandas as pd
from datetime import date
from plotly.offline import plot
import plotly.express as px
import plotly.graph_objects as go
import json
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash
from .models import Geojson, Parcelas


app = DjangoDash(name='dash_info')

# Importar datos
parcelas = Parcelas.objects.all()
df = pd.DataFrame.from_records(parcelas.values())
df = df[~df.finca.isin(['LH', 'ZG'])]

geojson = Geojson.objects.all().values('geojson').first().get('geojson')
geojson = json.loads(geojson)

# Definir argumentos
parcelas = df['parcela'].count()
area_finca = df['area'].sum()
df['edad'] = date.today().year - df['parcela'].str[-4:].astype(int)
edad_finca = np.average(df['edad'], weights=df['area'])
altitud_finca = np.average(df['altitud'], weights=df['area'])


app.layout = html.Div([
    # ************ Encabezado ************
    html.Div([
        html.Div([], className="one-third column",),

        html.Div([
            html.Div([
                html.H3("Finca La Hilda", style={"margin-bottom": "0px", 'color': 'white'}),
                html.H5("Información General", style={"margin-top": "0px", 'color': 'white'}),
            ])
        ], className="one-half column", id="title"),

        html.Div([], className="one-third column", id='title1'),

    ], id="header", className="row flex-display", style={"margin-bottom": "25px"}),

    # ************ Div Tarjetas ************
    html.Div([
        html.Div([
            html.H6(children='Parcelas',
                    style={
                        'textAlign': 'center',
                        'color': 'white'}
                    ),

            html.P(parcelas,
                   style={
                       'textAlign': 'center',
                       'color': '#1f77b4',
                       'fontSize': 40}
                   ),
            ], className="card_container three columns",
        ),

        html.Div([
            html.H6(children='Area Cultivada',
                    style={
                        'textAlign': 'center',
                        'color': 'white'}
                    ),

            html.P(f"{area_finca:,.0f}",
                   style={
                       'textAlign': 'center',
                       'color': 'orange',
                       'fontSize': 40}
                   ),

            html.P('hectáreas',
                   style={
                       'textAlign': 'center',
                       'color': 'orange',
                       'fontSize': 15,
                       'margin-top': '-18px'}
                   )
            ], className="card_container three columns",
        ),

        html.Div([
            html.H6(children='Altitud Media',
                    style={
                        'textAlign': 'center',
                        'color': 'white'}
                    ),

            html.P(f"{altitud_finca:,.0f}",
                   style={
                       'textAlign': 'center',
                       'color': '#dd1e35',
                       'fontSize': 40}
                   ),

            html.P('msnm',
                   style={
                       'textAlign': 'center',
                       'color': '#dd1e35',
                       'fontSize': 15,
                       'margin-top': '-18px'}
                   )], className="card_container three columns",
        ),

        html.Div([
            html.H6(children='Edad Promedio',
                    style={
                        'textAlign': 'center',
                        'color': 'white'}
                    ),

            html.P(f"{edad_finca:,.0f}",
                   style={
                       'textAlign': 'center',
                       'color': '#e55467',
                       'fontSize': 40}
                   ),

            html.P('años',
                   style={
                       'textAlign': 'center',
                       'color': '#e55467',
                       'fontSize': 15,
                       'margin-top': '-18px'}
                   )], className="card_container three columns")

    ], className="row flex-display"),

    # ************ Div Graficos ************
    html.Div([
        html.Div([

                    html.P('Seleccionar Parcela:', className='fix_label',  style={'color': 'white'}),

                    dcc.Dropdown(id='drop_parcelas',
                              multi=False,
                              clearable=True,
                              value='Todas',
                              placeholder='Seleccione Parcela',
                              options=[{'label': c, 'value': c}
                                       for c in np.append('Todas', (np.sort(df['parcela'].unique())))], className='dcc_compon'),

                     dcc.Graph(id='area', config={'displayModeBar': False}, className='dcc_compon',
                     style={'margin-top': '20px', 'width': '30vh', 'height': '7vh'},
                     ),

                     dcc.Graph(id='altitud', config={'displayModeBar': False}, className='dcc_compon',
                     style={'margin-top': '20px', 'width': '30vh', 'height': '7vh'},
                     ),

                     dcc.Graph(id='edad', config={'displayModeBar': False}, className='dcc_compon',
                     style={'margin-top': '20px', 'width': '30vh', 'height': '7vh'},
                     ),

                    html.Div([
                        html.H6(children='Variedad',
                                style={
                                    'textAlign': 'center',
                                    'color': 'green',
                                    'height': '2vh'}),
                        html.H6(id='variedad',
                               style={
                                   'textAlign': 'center',
                                   'color': 'green',
                                   'height': '2vh',
                                   'fontSize': 25,
                                   'margin-bottom': '40px'}),
                               ])

        ], className="create_container three columns", id="cross-filter-options"),

            html.Div([
                    dcc.Graph(id='choro_datos',
                            config={'displayModeBar': False}),
                            ], className="create_container five columns"),

            html.Div([
                    dcc.Graph(
                            id='choro_variedad',
                            config={'displayModeBar': False})

                    ], className="create_container four columns"),

        ], className="row flex-display"),


    ], id="mainContainer",
    style={"display": "flex", "flex-direction": "column"}
    )

@app.callback(
    Output('area', 'figure'),
    [Input('drop_parcelas', 'value')])
def update_area(drop_parcelas):
    if drop_parcelas == 'Todas':
        area_parcela = area_finca
    else:
        area_parcela = df[df['parcela'] == drop_parcelas].iloc[0,3]

    return {
            'data': [go.Indicator(
                    mode='number',
                    value=area_parcela,
                    number={'valueformat': '.1f',
                            'font': {'size': 20},},
                    domain={'y': [0, 1], 'x': [0, 1]})],
            'layout': go.Layout(
                title={'text': 'Area (Ha)',
                       'y': 1,
                       'x': 0.5,
                       'xanchor': 'center',
                       'yanchor': 'top'},
                font=dict(color='orange'),
                paper_bgcolor='#1f2c56',
                plot_bgcolor='#1f2c56',
                height=50
                ),
            }

@app.callback(
    Output('altitud', 'figure'),
    [Input('drop_parcelas', 'value')])
def update_confirmed(drop_parcelas):
    if drop_parcelas == 'Todas':
        altitud_parcela = altitud_finca
    else:
        altitud_parcela = df[df['parcela'] == drop_parcelas].iloc[0,4]

    return {
            'data': [go.Indicator(
                    mode='number',
                    value=altitud_parcela,
                    number={'valueformat': ',.0f',
                            'font': {'size': 20},},
                    domain={'y': [0, 1], 'x': [0, 1]})],
            'layout': go.Layout(
                title={'text': 'Altitud (msnm)',
                       'y': 1,
                       'x': 0.5,
                       'xanchor': 'center',
                       'yanchor': 'top'},
                font=dict(color='#dd1e35'),
                paper_bgcolor='#1f2c56',
                plot_bgcolor='#1f2c56',
                height=50
                ),
            }

@app.callback(
    Output('edad', 'figure'),
    [Input('drop_parcelas', 'value')])
def update_confirmed(drop_parcelas):
    if drop_parcelas == 'Todas':
        edad_parcela = edad_finca
    else:
        edad_parcela = date.today().year - pd.to_numeric(df[df['parcela'] == drop_parcelas].iloc[0,2][-4:])

    return {
            'data': [go.Indicator(
                    mode='number',
                    value=edad_parcela,
                    number={'valueformat': '.0f',
                            'font': {'size': 20},},
                    domain={'y': [0, 1], 'x': [0, 1]})],
            'layout': go.Layout(
                title={'text': 'Edad (años)',
                       'y': 1,
                       'x': 0.5,
                       'xanchor': 'center',
                       'yanchor': 'top'},
                font=dict(color='#e55467'),
                paper_bgcolor='#1f2c56',
                plot_bgcolor='#1f2c56',
                height=50
                ),
            }

@app.callback(
    Output('variedad', 'children'),
    [Input('drop_parcelas', 'value')])
def update_area(drop_parcelas):
    if drop_parcelas == 'Todas':
        variedad_parcela = 'N/A'
    else:
        variedad_parcela = df[df['parcela'] == drop_parcelas].iloc[0,5]

    return variedad_parcela

# Create choroplet chart (area, altitud y edad)
@app.callback(Output('choro_datos', 'figure'),
              [Input('drop_parcelas', 'value')])

def update_graph(drop_parcelas):
    if drop_parcelas == 'Todas':
        df1 = df.copy()
    else:
        df1 = df[df['parcela'] == drop_parcelas]

    fig = px.choropleth_mapbox(df1, geojson=geojson, color="area",
                               locations="parcela", featureidkey="properties.name",
                               center={'lat': 10.098, 'lon': -84.229},
                               color_continuous_scale='RdYlGn_r',
                               hover_name="parcela",
                               hover_data={"variedad":True, "altitud":True, "parcela":False},
                               mapbox_style='open-street-map', zoom=13.1)
    fig.update_layout(margin={'l': 0, 'b': 0, 't': 50, 'r': 0},
            font=dict(color='white'),
            hovermode='closest',
            clickmode='event+select',
            paper_bgcolor='#1f2c56',
            title={
                'text': 'Datos',
                'y':0.975,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font':{'color':'white', 'size':20}})

    button1 =  dict(method = 'update',
                    args = [{'z': [ df['area'] ] },
                    {'coloraxis.colorbar.title':{'text':'Ha'}}],
                    label = 'Area')
    button2 =  dict(method = 'update',
                    args = [{'z': [ df['altitud'] ] },
                    {'coloraxis.colorbar.title':{'text':'msnm'}}],
                    label = 'Altitud')
    button3 =  dict(method = 'update',
                    args = [{'z': [ df['edad'] ] },
                    {'coloraxis.colorbar.title':{'text':'años'}}],
                    label = 'Edad')

    fig.update_layout(
            updatemenus=[dict(y=0.99,
                                x=0.01,
                                xanchor='left',
                                yanchor='top',
                                active=0,
                                bgcolor='white',
                                font=dict(color='black'),
                                buttons=[button1, button2, button3])])

    return fig


# Create choropleth chart (show variedades)
@app.callback(Output('choro_variedad', 'figure'),
              [Input('drop_parcelas', 'value')])
def update_graph(drop_parcelas):
    if drop_parcelas == 'Todas':
        df1 = df.copy()
    else:
        df1 = df[df['parcela'] == drop_parcelas]

    fig = px.choropleth_mapbox(df1, geojson=geojson, color="variedad",
            locations="parcela", featureidkey="properties.name",
            center={'lat': 10.098, 'lon': -84.23},
            color_continuous_scale='RdYlGn_r',
            hover_name="parcela",
            hover_data={"variedad":True, "altitud":True, "parcela":False},
            mapbox_style='open-street-map', zoom=13.05,
            )
    fig.update_layout(margin={'l': 0, 'b': 0, 't': 50, 'r': 0},
            hovermode='closest',
            clickmode='event+select',
            legend_title={'text':'Variedad'},
            legend={'yanchor':"top", 'y':0.99, 'xanchor':"left", 'x':0.01, 'bgcolor':'white'},
            paper_bgcolor='#1f2c56',
            title={
                'text': 'Variedades',
                'y':0.975,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font':{'color':'white', 'size':20}}
            )

    return fig

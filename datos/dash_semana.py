import numpy as np
import pandas as pd
from datetime import timedelta
from plotly.offline import plot
import plotly.express as px
import plotly.graph_objects as go
import json
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash
from .plotly import plotly_treemap
from .models import Database, Geojson, Parcelas


def fig(value, delta, title, color):
    fig = go.Figure(
                    data=[go.Indicator(
                            mode='number+delta',
                            value=value,
                            delta={'reference': delta,
                                      'position': 'bottom',
                                      'valueformat': ',.0f',
                                      'relative': False,
                                      'font': {'size': 17}},
                            number={'valueformat': ',.0f',
                                    'font': {'size': 25},},
                            domain={'y': [0, 1], 'x': [0, 1]})],
                    layout=go.Layout(
                        title={'text': title,
                               'y': .95,
                               'x': 0.5,
                               'xanchor': 'center',
                               'yanchor': 'top',
                               'font':{'color': 'white', 'size':20},
                               },
                        font=dict(color=color),
                        paper_bgcolor='#1f2c56',
                        plot_bgcolor='#1f2c56',
                        height=50,
                        margin={'l': 0, 'b': 0, 't': 30, 'r': 0},
                        ),
                    )
    return fig


app = DjangoDash(name='dash_semana')

# Importar datos
geojson = Geojson.objects.all().values('geojson').first().get('geojson')
geojson = json.loads(geojson)

parcelas = Parcelas.objects.all()
parcelas = pd.DataFrame.from_records(parcelas.values())
area = parcelas.set_index('parcela')['area']

database = Database.objects.all()
df = pd.DataFrame.from_records(database.values())
df = df[~(df.Familia.isin(['Produccion', 'Cosecha']))]   # Excluir ingresos y costos de cosecha
df = df[~(df.Labor.isin(['0']))]   # Eliminar Costos/Hrs huerfanas de labores

# Definir fechas de corte
last_thu = df.Fecha.max()
last_thu2 = df.Fecha.max() - timedelta(7)

# Definir argumentos
df_wk = df[df.Fecha == last_thu].groupby(['Familia', 'Actividad', 'Labor']).agg(IN_Uds=('IN_Uds', sum), MO_Hrs=('MO_Hrs',
                                sum), MAQ_Hrs=('MAQ_Hrs', sum), Tot_CRC=('Tot_CRC', sum), Fecha=('Fecha', max),
                                Diesel=('Diesel', sum), Gas=('Gas', sum), Area=('Area', sum))
df_wk.reset_index(inplace=True)

df_wk2 = df[df.Fecha == last_thu2].groupby(['Familia', 'Actividad', 'Labor']).agg(IN_Uds=('IN_Uds', sum),
                                MO_Hrs=('MO_Hrs', sum), MAQ_Hrs=('MAQ_Hrs', sum), Tot_CRC=('Tot_CRC', sum),
                                Diesel=('Diesel', sum), Gas=('Gas', sum), Area=('Area', sum))
df_wk2.reset_index(inplace=True)

actividades = ['Todas', 'Atomizo & Drench', 'Fertilizacion', 'Herbicida']

IN_Uds = df_wk[df_wk.Labor.isin(actividades)].IN_Uds.sum()
IN_Uds2 = df_wk2[df_wk2.Labor.isin(actividades)].IN_Uds.sum()

MO_Hrs = df_wk.MO_Hrs.sum()
MO_Hrs2 = df_wk2.MO_Hrs.sum()

MAQ_Hrs = df_wk.MAQ_Hrs.sum()
MAQ_Hrs2 = df_wk2.MAQ_Hrs.sum()

Comb_Uds = df_wk.Diesel.sum() + df_wk.Gas.sum()
Comb_Uds2 = df_wk2.Diesel.sum() + df_wk2.Gas.sum()

Tot_CRC = df_wk.Tot_CRC.sum()
Tot_CRC2 = df_wk2.Tot_CRC.sum()

Atom_Uds = df_wk[df_wk.Actividad == 'Atomizo & Drench'].IN_Uds.sum()
Atom_Uds2 = df_wk2[df_wk2.Actividad == 'Atomizo & Drench'].IN_Uds.sum()

Fert_Uds = df_wk[df_wk.Actividad == 'Fertilizacion'].IN_Uds.sum()
Fert_Uds2 = df_wk2[df_wk2.Actividad == 'Fertilizacion'].IN_Uds.sum()

Herb_Uds = df_wk[df_wk.Actividad == 'Herbicida'].IN_Uds.sum()
Herb_Uds2 = df_wk2[df_wk2.Actividad == 'Herbicida'].IN_Uds.sum()


# Crear figure Indicator
colors = ['#1f77b4', 'orange', '#dd1e35', '#e55467']
mo_hrs_fig = fig(MO_Hrs, MO_Hrs2, 'Mano Obra (Hrs)', colors[0])
maq_hrs_fig = fig(MAQ_Hrs, MAQ_Hrs2, 'Maquinaria (Hrs)', colors[1])
comb_uds_fig = fig(Comb_Uds, Comb_Uds2, 'Combustible (L)', colors[2])
tot_crc_fig = fig(Tot_CRC, Tot_CRC2, 'Total (CRC)', colors[3])
atom_uds_fig = fig(Atom_Uds, Atom_Uds2, 'Atomizo (200L)', colors[1])
fert_uds_fig = fig(Fert_Uds, Fert_Uds2, 'Fertilizante (Sacos)', colors[2])
herb_uds_fig = fig(Herb_Uds, Herb_Uds2, 'Herbicida (L)', colors[3])


app.layout = html.Div([
    # ************ Encabezado ************
    html.Div([
        html.Div([], className="one-third column",),    # Tercio izquierdo vacío

        html.Div([
            html.Div([
                html.H3("Finca La Hilda", style={"margin-bottom": "0px", 'color': 'white'}),
                html.H5("Resumen Semana " + str(last_thu.strftime("%d-%m-%Y")), style={"margin-top": "0px", 'color': 'white'}),
            ])
        ], className="one-half column", id="title"),

        html.Div([], className="one-third column", id='title1'),    # Tercio derecho vacío

    ], id="header", className="row flex-display", style={"margin-bottom": "25px"}),

    # ************ Div Tarjetas ************
    html.Div([
        html.Div([
                 dcc.Graph(id='mo_hrs', figure=mo_hrs_fig, config={'displayModeBar': False}, className='dcc_compon',
                 style={'margin-top': '20px', 'width': '30vh', 'height': '11vh'},
                 ),
            ], className="card_container three columns",
        ),

        html.Div([
                 dcc.Graph(id='maq_hrs', figure=maq_hrs_fig, config={'displayModeBar': False}, className='dcc_compon',
                 style={'margin-top': '20px', 'width': '30vh', 'height': '11vh'},
                 ),
            ], className="card_container three columns",
        ),

        html.Div([
                 dcc.Graph(id='combs_uds', figure=comb_uds_fig, config={'displayModeBar': False}, className='dcc_compon',
                 style={'margin-top': '20px', 'width': '30vh', 'height': '11vh'},
                 ),
            ], className="card_container three columns",
        ),

        html.Div([
                 dcc.Graph(id='tot_crc', figure=tot_crc_fig, config={'displayModeBar': False}, className='dcc_compon',
                 style={'margin-top': '20px', 'width': '30vh', 'height': '11vh'},
                 ),
            ], className="card_container three columns")

    ], className="row flex-display"),


    # ************ Div Graficos ************
    html.Div([
        html.Div([
                    html.P('Seleccionar Actividad:', className='fix_label',  style={'color': 'white'}),

                    dcc.Dropdown(id='drop_actividad',
                              multi=False,
                              clearable=True,
                              value='Todas',
                              placeholder='Seleccione Actividad',
                              options=[{'label': c, 'value': c}
                                       for c in np.append('Todas', (np.sort(df_wk[df_wk.Actividad.isin(actividades)].Actividad.unique())))], className='dcc_compon'),

                    dcc.Graph(id='atom_uds', figure=atom_uds_fig, config={'displayModeBar': False}, className='dcc_compon',
                    style={'margin-top': '20px', 'width': '30vh', 'height': '11vh'},
                    ),

                    dcc.Graph(id='fert_uds', figure=fert_uds_fig, config={'displayModeBar': False}, className='dcc_compon',
                    style={'margin-top': '20px', 'width': '30vh', 'height': '11vh'},
                    ),

                    dcc.Graph(id='herb_uds' ,figure=herb_uds_fig, config={'displayModeBar': False}, className='dcc_compon',
                    style={'margin-top': '20px', 'width': '30vh', 'height': '11vh'},
                    ),


        ], className="create_container three columns", id="cross-filter-options"),

            html.Div([
                    dcc.Graph(id='treemap_costos',
                            config={'displayModeBar': False}),
                            ], className="create_container five columns"),

            html.Div([
                    dcc.Graph(
                            id='choro_actividades',
                            config={'displayModeBar': False})

                    ], className="create_container four columns"),

        ], className="row flex-display"),


    ], id="mainContainer",
    style={"display": "flex", "flex-direction": "column"}
    )



# Create treemap chart
@app.callback(
    Output('treemap_costos', 'figure'),
    [Input('drop_actividad', 'value')])
def update_graph(drop_actividad):
    if drop_actividad == 'Todas':
        df1 = df_wk.copy()
    else:
        df1 = df_wk[df_wk['Actividad'] == drop_actividad]

    fig = plotly_treemap(df1)
    fig.update_layout(margin={'l': 0, 'b': 0, 't': 20, 'r': 0},
                    font=dict(color='white'),
                    updatemenus=[
                        dict(x=.775, y=1.045, bgcolor='white', font=dict(color='#1f2c56') )],
                    annotations=[
                        dict(x=0.765, y=1.03, font=dict(color='white') )],
                    paper_bgcolor='#1f2c56',
                    )

    return fig

# Create chropleth chart
@app.callback(
    Output('choro_actividades', 'figure'),
    [Input('drop_actividad', 'value')])
def update_graph(drop_actividad):
    df1 = df[df.Actividad.isin(actividades)]
    df1 = df1[df1.Fecha == last_thu].groupby(['Parcela', 'Actividad']).agg(MO_Hrs=('MO_Hrs', sum),
                        IN_Uds=('IN_Uds', sum), Tot_CRC=('Tot_CRC', sum), Area=('Area', sum))
    df1.reset_index(inplace=True)
    df1['Area2'] = df1.Parcela.map(area)
    df1 = df1.fillna(value={'Area2': 100})
    df1['Area2'] = df1.apply(lambda x: min(x.Area, x.Area2) if x.Area != 0 else x.Area2, axis=1)
    df1['IN_ha'] = df1.IN_Uds / df1.Area2
    df1['MO_ha'] = df1.MO_Hrs / df1.Area2
    df1['CRC_ha'] = df1.Tot_CRC / df1.Area2

    if drop_actividad == 'Todas':
        df2 = df1.copy()
    else:
        df2 = df1[df1['Actividad'] == drop_actividad]


    fig = px.choropleth_mapbox(df2, geojson=geojson, color="MO_ha",
                               locations="Parcela", featureidkey="properties.name",
                               center={'lat': 10.098, 'lon': -84.229},
                               color_continuous_scale='RdYlGn_r',
                               hover_name="Parcela",
                               hover_data={"Parcela":True, "Actividad":False},
                               mapbox_style='open-street-map', zoom=13.1)
    fig.update_layout(margin={'l': 0, 'b': 0, 't': 44, 'r': 0},
            font=dict(color='white'),
            hovermode='closest',
            clickmode='event+select',
            paper_bgcolor='#1f2c56',
            title={
                'text': 'Actividad: ' + drop_actividad.split()[0],
                'y':0.97,
                'x':0,
                'xanchor': 'left',
                'yanchor': 'top',
                'font':{'color':'white', 'size':15}})

    button1 =  dict(method = 'update',
                    args = [{'z': [ df2['MO_ha'] ] },
                    {'coloraxis.colorbar.title':{'text':'Hrs/ha'}}],
                    label = 'MO_ha')
    button2 =  dict(method = 'update',
                    args = [{'z': [ df2['IN_ha'] ] },
                    {'coloraxis.colorbar.title':{'text':'Uds/ha'}}],
                    label = 'IN_ha')
    button3 =  dict(method = 'update',
                    args = [{'z': [ df2['CRC_ha'] ] },
                    {'coloraxis.colorbar.title':{'text':'CRC/ha'}}],
                    label = 'CRC_ha')

    fig.update_layout(
            coloraxis_colorbar={
                'title':{'font':{'color':'white'}, 'text':'Hrs/ha'},
                'tickfont':{'color':'white'}},
            updatemenus=[
                dict(x=1.26,
                    y=1.11,
                    bgcolor='white',
                    font=dict(color='#1f2c56'),
                    buttons=[button1, button2, button3])],
            annotations=[
                dict(text="Nivel:",
                    showarrow=False,
                    x=0.90,
                    y=1.09,
                    font=dict(color='white'))])

    return fig

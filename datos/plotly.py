import pandas as pd
import datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot
from .models import Database, Parcelas, Geojson


def plotly_gantt(dt):
    dt['Fecha'] = dt['Fecha'].astype('datetime64')

    # Agrupar subciclos por ciclo
    dt['Ciclo'] = dt.Item.str.extract(r'([0-9]+\s[A-Z]+\#[0-9]+)')[0]

    # Agrupar datos por 'Familia','Actividad' y 'Labor' y crear columna de total por 'Familia'
    dt2 = dt.groupby(['OT', 'Ciclo']).agg(Inicio=('Fecha', min), Fin=('Fecha', max), Uds=('IN_Uds', sum))
    dt2.reset_index(inplace=True)

    # Agregar columnas de fechas DDF
    flor = datetime.datetime.strptime('20210428', "%Y%m%d")
    dt2['Ini_DDF'] = dt2.Inicio - flor
    dt2['Fin_DDF'] = dt2.Fin - flor
    dt2['Dias'] = dt2.Fin - dt2.Inicio
    dt2['Ini_DDF'] = dt2['Ini_DDF'].dt.days.astype('int64')
    dt2['Fin_DDF'] = dt2['Fin_DDF'].dt.days.astype('int64')
    dt2['Dias'] = dt2['Dias'].dt.days.astype('int64')

    # Formato final DF
    dt2 = dt2[['OT', 'Ciclo', 'Dias', 'Ini_DDF', 'Fin_DDF', 'Inicio', 'Fin', 'Uds']]
    dt2 = dt2.sort_values(['OT', 'Inicio'])

    colors = {'Atomizo': 'rgb(95,158,160)',
              'Fertilizante': 'rgb(30,144,255)',
              'Herbicida': 'rgb(211,211,210)'}

    fig = px.timeline(dt2,
        x_start='Inicio',
        x_end='Fin',
        y='Ciclo',
        hover_name='Ciclo',
        hover_data={'OT': False, 'Ciclo': False, 'Dias': True, 'Ini_DDF': True,
                'Fin_DDF': True, 'Inicio': False, 'Fin': False, 'Uds': True},
        color_discrete_sequence=px.colors.qualitative.Set1,
        opacity=.7,
        range_x=None,
        range_y=None,
        template='plotly_white',
        height=400,
        width=900,
        color='OT',
        title="<b>Ejecución de ciclos agrícolas</b>")

    fig.update_layout(
            yaxis_categoryorder='category descending',
            yaxis_title='')

    fig.update_layout(
        bargap=0.4,
        bargroupgap=0.1,
        xaxis_range=[dt2.Inicio.min(), dt2.Fin.max()],
        xaxis=dict(
            showgrid=True,
            side='bottom',
            tickmode='linear',
            dtick="M1",
            tickformat="%b %y \n",
            ticklabelmode="period",
            ticks="outside",
            tickson="boundaries",
            tickwidth=.1,
            layer='below traces'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.1,
            title="",
            xanchor="right",
            x=1,
            font=dict(
                family="Arial",
                size=14,
                color="darkgray")
            )
        )

    fig.update_traces(marker_line_color='rgb(8,48,107)',
                      marker_line_width=1.5, opacity=0.95)

    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def plotly_treemap(df):
    # Agrupar datos por 'Familia','Actividad' y 'Labor' y crear columna de total por 'Familia'
    df = df[~(df.Familia.isin(['Produccion', 'Cosecha']))]   # Excluir ingresos y costos de cosecha
    df = df[~(df.Labor.isin(['0']))]   # Eliminar Costos/Hrs huerfanas de labores
    df = df.groupby(['Familia', 'Actividad', 'Labor']).agg(Tot_CRC=('Tot_CRC', sum), MO_Hrs=('MO_Hrs', sum))
    df.reset_index(inplace=True)

    df.Tot_CRC = df.Tot_CRC/1000000
    df['pct_fam'] = df.groupby(['Familia'])['Tot_CRC'].transform('sum')

    # Crear DF de trees y branches
    levels = ['Labor', 'Actividad', 'Familia']
    value_column = 'Tot_CRC'

    def build_hierarchical_dataframe(df, levels, value_column):
        """
        Build a hierarchy of levels for Sunburst or Treemap charts.
        Levels are given starting from the bottom to the top of the hierarchy,
        ie the last level corresponds to the root.
        """
        df_all_trees = pd.DataFrame(columns=['id', 'parent', 'value'])
        for i, level in enumerate(levels):
            df_tree = pd.DataFrame(columns=['id', 'parent', 'value'])
            dfg = df.groupby(levels[i:]).sum()
            dfg = dfg.reset_index()
            df_tree['id'] = dfg[level].copy()
            if i < len(levels) - 1:
                df_tree['parent'] = dfg[levels[i+1]].copy()
            else:
                df_tree['parent'] = 'Total'
            df_tree['value'] = dfg[value_column]
            df_all_trees = df_all_trees.append(df_tree, ignore_index=True)
        total = pd.Series(dict(id='Total', parent='',
                                  value=df[value_column].sum()))
        df_all_trees = df_all_trees.append(total, ignore_index=True)
        return df_all_trees

    df_all_trees = build_hierarchical_dataframe(df, levels, value_column)

    # Crear DF de 'total' por 'Familia' y 'parent' para ponderar porcentajes parciales/totales
    dt3 = df[['Familia', 'pct_fam']].drop_duplicates(subset=['Familia'], keep='first').copy()
    dt3['parent'] = dt3.Familia
    dt4 = df[['Familia', 'Actividad', 'pct_fam']].drop_duplicates(subset=['Actividad'], keep='first').copy()
    dt4.rename(columns={'Actividad': 'parent'}, inplace=True)
    dt5 = dt3.append(dt4, ignore_index=True)
    total = {'Familia': 'Total', 'parent': 'Total', 'pct_fam': df.Tot_CRC.sum()}
    dt5 = dt3.append(dt4, ignore_index=True).append(total, ignore_index=True)

    # Agregar columnas de porcentaje por 'Familia' y 'Total'
    dt6 = pd.merge(df_all_trees, dt5, on='parent', how='left')
    dt6.pct_fam = dt6.value/dt6.pct_fam
    dt6.pct_fam = dt6.apply(lambda x: 1 if (x.parent == 'Total' or x.parent == '') else x.pct_fam, axis=1)
    dt6.Familia = dt6.apply(lambda x: x.parent if x.parent == 'Total' else x.parent, axis=1)
    dt6['pct_tot'] = dt6.value / dt6.value.max()

    # Create Treemap
    fig = go.Figure(go.Treemap(
        labels=dt6['id'],
        parents=dt6['parent'],
        values=dt6['value'],
        branchvalues='total',
        customdata=dt6[['pct_fam', 'pct_tot']],
        hovertemplate='<b>%{label} </b> <br> Monto: %{value:.1f} mm <br> Familia: %{customdata[0]:.0%}\
                        <br> Total: %{customdata[1]:.0%}',
        name='',
        maxdepth=4))

    # Add dropdown button
    button_layer_1_height = 1.07
    fig.update_layout(
        updatemenus=[
            dict(
                buttons=list([
                    dict(
                        args=['maxdepth', 2],
                        label='Familia',
                        method="restyle"),
                    dict(
                        args=['maxdepth', 3],
                        label='Actividad',
                        method="restyle"),
                    dict(
                        args=['maxdepth', 4],
                        label='Labor',
                        method="restyle")]),
                direction="down",
                pad={"r": 0, "t": 0},
                showactive=True,
                x=.81,
                xanchor="left",
                y=button_layer_1_height,
                yanchor="top"),],
        annotations=[
            dict(text="Nivel:", showarrow=False,
                 x=0.80, y=1.05, yref="paper", align="left")])

    return fig


def plotly_treemap_title(df):
    fig = plotly_treemap(df)

    fig.update_layout(
    #     width=1100,
    #     height=700,
        title={
            'text': 'LH: Costos por Familia, Actividad y Labor al {}'.format(
                df.Fecha.astype('datetime64').max().strftime('%d-%m-%Y')),
            'y': 0.9,
            'x': 0.09,
            'xanchor': 'left',
            'yanchor': 'top'})

    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def plotly_choropleth(df, geojson):
    fig = go.Figure()
    fig.add_trace(go.Choroplethmapbox(
                featureidkey='properties.name',
                geojson=geojson,
                locations=df['parcela'],
                z=df['area'],
                colorbar_title='area/Ha',
                colorscale='Viridis',
                customdata=df['parcela'],
                hovertemplate='<b>%{location} </b><extra>%{z:,.3r}</extra>'
        ))

    fig.update_layout(mapbox_style='open-street-map',
            mapbox_zoom=13.5, mapbox_center={'lat': 10.098, 'lon': -84.23}
            )
    fig.update_layout(margin={'l': 40, 'b': 30, 't': 30, 'r': 0},
            height=600,
            width=800,
            hovermode='closest',
            clickmode='event+select'
            )

    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div

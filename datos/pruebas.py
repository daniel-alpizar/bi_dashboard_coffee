import numpy as np
import pandas as pd
import datetime
from datetime import date
from datetime import timedelta


# Util functions
def date_range():
    '''Sets the date for the last Thursday (last_thu) and the Friday before (last_fri)'''
    today = date.today()
    offset = (today.weekday() - 3) % 7
    last_thu = np.datetime64(today - timedelta(days=offset))
    last_thu = last_thu - 7 if last_thu == date.today() else last_thu
    last_fri = last_thu - 6

    return last_fri, last_thu


# Definicion de parametros
# *************** Labores con INS -- Tabla en Admin !!??!! *****************
labores_IN = ['CN.Enmienda Organica', 'CN.Enmienda Quimica', 'CN.Herbicida', 'FS.Atomizo/Drench',
            'FS.Fertilizacion', 'FS.Fertilizacion (Mecanica)', 'FS.Motobomba', 'FS.Spray Boom']

cols_report = ['Fecha', 'Actividad', 'Labor', 'Modo', 'OT', 'Ciclo', 'Item', 'Parcela',
            'IN_Uds', 'IN_CRC', 'MO_Hrs', 'MO_CRC', 'MAQ_Hrs', 'MAQ_CRC', 'Area', 'Diesel', 'Gas']
cols_text = ['Fecha', 'Actividad', 'Labor', 'Modo', 'OT', 'Ciclo', 'Item', 'Parcela']
cols_amount = ['IN_Uds', 'IN_CRC', 'MO_Hrs', 'MO_CRC', 'MAQ_Hrs', 'MAQ_CRC']
cols_datos = ['Area', 'Diesel', 'Gas']

# Reports format properties
# CSS dataframe style
styles = [dict(selector="th", props=[("font-size", "80%"), ("text-align", "center"),
                               ("background-color", "#000086"), ("color", "white")]),
        dict(selector="caption", props=[("caption-side", "top"), ("color", "darkblue"),
                        ("font-size", "120%"), ('font-weight','bold'), ("text-align", "center")]),
        dict(selector="tr:hover", props=[("background-color", "%s" % "#D3D3D3")]),
        dict(selector="td:hover", props=[("background-color", "#ffffb3")])]

# Columns properties
text_props = {'min-width': '90px', 'text-align': 'center', 'font-size': '10pt'}
amount_props = {'min-width': '70px', 'text-align': 'right', 'font-size': '10pt'}
datos_props = {'min-width': '40px', 'text-align': 'right', 'font-size': '10pt'}

# Highlight colors
c1 = 'background-color: lightblue'
c2 = 'background-color: lightgreen'
c3 = 'background-color: lightsteelblue'



# 1. Reporte OTs sin Insumos
def OTsinIN(df_check):
    '''Reporte (dataframe) de OTs (labores_IN) con insumos faltantes'''

    df = df_check[(df_check.Labor.isin(labores_IN)) & (df_check.IN_Uds == 0)]\
            [['Fecha', 'Actividad', 'Parcela']].drop_duplicates(['Fecha', 'Actividad', 'Parcela'])\
            .sort_values(by=['Fecha', 'Parcela', 'Actividad'])

    df = pd.merge(df, df_check, how='left', on=['Fecha', 'Actividad', 'Parcela'])\
            .sort_values(by=['Fecha', 'Parcela', 'Actividad'])[cols_report]

    def highlight_cols(x):
        mask1 = (x['IN_Uds'] == 0)
        mask2 = (x['IN_Uds'] != 0)
        df_high = pd.DataFrame(data='', index=df.index, columns=df.columns)
        df_high.loc[mask1, ['IN_Uds', 'Actividad']] = c2, c1
        df_high.loc[mask2, ['IN_Uds']] = c3

        return df_high

    df = (df.style
                .hide_index()
                .hide_columns(['Area', 'Diesel', 'Gas'])
                .format(precision=0, thousands=",")
                .set_table_styles(styles)
                .apply(highlight_cols, axis=None)
                .set_properties(subset=cols_text, **text_props)
                .set_properties(subset=cols_amount, **amount_props)
                .set_caption('Reporte: OTs sin Insumos'))

    return df


# 2. Reporte Insumos sin Mano de Obra
def INsinMO(df_check):
    '''Reporte (dataframe) de insumos (IN_Uds) sin mano de obra (MO_Hrs)'''

    df = df_check[(df_check.MO_Hrs == 0) & ((df_check.IN_Uds > 0) |
                (df_check.Area > 0) | (df_check.Diesel > 0) | (df_check.Gas > 0))]\
            [['Fecha', 'Actividad', 'Parcela']].drop_duplicates(['Fecha', 'Actividad', 'Parcela'])\
            .sort_values(by=['Fecha', 'Parcela', 'Actividad'])

    df = pd.merge(df, df_check, how='left', on=['Fecha', 'Actividad', 'Parcela'])\
            .sort_values(by=['Fecha', 'Parcela', 'Actividad'])[cols_report]

    def highlight_cols(x):
        mask1 = (x['IN_Uds'] != 0) & (x['MO_Hrs'] == 0)
        mask2 = (x['Area'] != 0) & (x['MO_Hrs'] == 0)
        mask3 = (x['Diesel'] != 0) & (x['MO_Hrs'] == 0)
        mask4 = (x['Gas'] != 0) & (x['MO_Hrs'] == 0)
        mask5 = (x['MO_Hrs'] != 0)
        df_high = pd.DataFrame(data='', index=df.index, columns=df.columns)
        df_high.loc[mask1, ['IN_Uds','MO_Hrs']] = c1, c2
        df_high.loc[mask2, ['Area','MO_Hrs']] = c1, c2
        df_high.loc[mask3, ['Diesel','MO_Hrs']] = c1, c2
        df_high.loc[mask4, ['Gas','MO_Hrs']] = c1, c2
        df_high.loc[mask5, ['MO_Hrs']] = c3

        return df_high

    df = (df.style
                .hide_index()
                .hide_columns([])
                .format(precision=0, thousands=",")
                .set_table_styles(styles)
                .apply(highlight_cols, axis=None)
                .set_properties(subset=cols_text, **text_props)
                .set_properties(subset=cols_amount, **amount_props)
                .set_properties(subset=cols_datos, **datos_props)
                .set_caption('Reporte: Insumos sin Mano de Obra'))

    return df


# 3. Reporte de MAQ_Hrs sin MO_Hrs
def MAQsinMO(df_check):
    '''Reporte (dataframe) de maquinaria (MAQ_Hrs) sin mano de obra (MO_Hrs)'''

    df = df_check[(df_check.MAQ_Hrs != 0) & (df_check.MO_Hrs == 0)]\
            [['Fecha','Actividad','Parcela']].drop_duplicates(['Fecha','Actividad','Parcela'])\
            .sort_values(by=['Fecha'])

    df = pd.merge(df, df_check, how='left', on=['Fecha','Actividad','Parcela'])\
            .sort_values(by=['Fecha', 'Parcela', 'Actividad'])[cols_report]

    def highlight_cols(x):
        mask1 = (x['MAQ_Hrs'] > 0) & (x['MO_Hrs'] == 0)
        mask2 = x['MO_Hrs'] > 0
        df_high = pd.DataFrame(data='', index=df.index, columns=df.columns)
        df_high.loc[mask1, ['MO_Hrs','MAQ_Hrs']] = c1, c2
        df_high.loc[mask2, ['MO_Hrs','MAQ_Hrs']] = c3

        return df_high

    df = (df.style
                .hide_index()
                .hide_columns(['Area', 'Diesel', 'Gas'])
                .format(precision=0, thousands=",")
                .set_table_styles(styles)
                .apply(highlight_cols, axis=None)
                .set_properties(subset=cols_text, **text_props)
                .set_properties(subset=cols_amount, **amount_props)
                .set_caption('Reporte: Maquinaria sin Mano de Obra'))

    return df


# 4. Reporte Mecanizado sin MO_Hrs o MAQ_Hrs
def MECsinMO(df_check):
    '''Reporte (dataframe) de modo mecanizado sin mano de obra (MO_Hrs) o maquinaria (MAQ_Hrs)'''

    mask = df_check[(df_check.Modo == 'Mecanizado') & ((df_check.MAQ_Hrs ==0) |
            (df_check.MO_Hrs ==0))][['Fecha','Actividad','Parcela']]\
            .drop_duplicates(['Fecha','Actividad','Parcela']).sort_values(by=['Fecha'])

    df = pd.merge(mask, df_check, how='left', on=['Fecha','Actividad','Parcela'])\
            .sort_values(by=['Fecha','Parcela','Actividad'])[cols_report]


    def highlight_cols(x):
        mask1 = (x['MO_Hrs'] == 0) & (x['Modo'] == 'Mecanizado')
        mask2 = (x['MAQ_Hrs'] == 0) & (x['Modo'] == 'Mecanizado')
        mask3 = (x['Modo'] != 'Mecanizado') & (x['MO_Hrs'] != 0)
        mask4 = (x['Modo'] != 'Mecanizado') & (x['MAQ_Hrs'] != 0)
        df_high = pd.DataFrame(data='', index=df.index, columns=df.columns)
        df_high.loc[mask1, ['Modo','MO_Hrs']] = c2, c1
        df_high.loc[mask2, ['Modo','MAQ_Hrs']] = c2, c1
        df_high.loc[mask3, ['MO_Hrs']] = c3
        df_high.loc[mask4, ['MAQ_Hrs']] = c3

        return df_high

    df = (df.style
                .hide_index()
                .hide_columns(['Area', 'Diesel', 'Gas'])
                .format(precision=0, thousands=",")
                .set_table_styles(styles)
                .apply(highlight_cols, axis=None)
                .set_properties(subset=cols_text, **text_props)
                .set_properties(subset=cols_amount, **amount_props)
                .set_caption('Reporte: Mecanizado sin MO o MAQ'))

    return df

import numpy as np
import pandas as pd
from datetime import timedelta
from datos.models import Database


def db_process(data_set):
    # Definir encabezados y convertir valores negativos
    df = data_set
    df.set_axis(['Trans', 'Fecha', 'Tipo', 'Cuenta', 'Labor', 'Modo', 'Factor', 'Item', 'Parcela', 'Uds', 'Monto'],
                axis=1, inplace=True)
    df['Uds'] = df['Uds'].abs()
    df['Monto'] = df['Monto'].abs()

    # look for initial and final date
    min_date = df.Fecha.min()
    max_date = df.Fecha.max()

    # Convertir min_date y max_date a jueves (cierre de semana)
    min_date2 = min_date + timedelta((3-min_date.weekday()) % 7)
    max_date2 = max_date + timedelta((3-max_date.weekday()) % 7)

    # Delete database rows included in range date
    Database.objects.filter(Fecha__range=(min_date2, max_date2)).delete()

    # Eliminar duplicados cosecha distribuidos por parcelas (Eliminar ZG:General)
    df = df[~((df['Cuenta'].str.contains('40100')) & (df['Parcela'] == 'ZG:General'))]
    df_rec = df[((df['Cuenta'].str.contains('50502')) & (df['Tipo'] == 'General Journal') & (df['Parcela'] != 'ZG:General'))]
    # df = df[~(df['Cuenta'].str.contains('50501|50502'))]   # Excluye costos de recoleccion
    df = pd.concat([df, df_rec], ignore_index=True, axis=0)

    # Eliminar diferencias de inventario de insumos
    df = df[~((~df['Cuenta'].str.contains('60303')) & (df['Tipo'] == 'Bill'))]

    # Eliminar jornadas de 'Item'
    df.loc[(df.Item.isna()), 'Item'] = ''
    df.loc[(df['Item'].str.contains('Ordinarias|Extras')), 'Item'] = ''

    # Etiquetar datos 'MO', 'MAQ', 'IN', 'COS', 'REC'
    MAQ = 'Camion|Tractor|Back'
    df.loc[(df['Factor'].str.contains(MAQ)), 'Factor'] = 'MAQ'
    df.loc[((df['Tipo'] == 'Paycheck') & ~df['Factor'].str.contains('MAQ')), 'Factor'] = 'MO'
    df.loc[df['Tipo'].isin(['Invoice', 'Bill']), 'Factor'] = 'IN'
    df.loc[(df['Cuenta'].str.contains('40100|40110')), 'Factor'] = 'COS'
    df.loc[(df['Cuenta'].str.contains('50501|50502')), 'Factor'] = 'REC'
    df = df[df['Tipo'].isin(['Invoice', 'Paycheck', 'General Journal', 'Bill'])]

    # +++++++++++ Procesar 'Insumos' por separado +++++++++++
    # Crear df_IN y columnas 'Area', 'Gas', 'Diesel' con valores propagados con base en 'Trans'
    df_IN = df[df['Factor'] == 'IN'].copy()

    area = df_IN[df_IN.Item.str.contains('Area')].drop_duplicates('Trans').set_index('Trans')['Uds']
    gas = df_IN[df_IN.Item.str.contains('Gasolina')].drop_duplicates('Trans').set_index('Trans')['Uds']
    diesel = df_IN[df_IN.Item.str.contains('Diesel')].drop_duplicates('Trans').set_index('Trans')['Uds']

    df_IN['Area'] = df_IN['Trans'].map(area)
    df_IN['Gas'] = df_IN['Trans'].map(gas)
    df_IN['Diesel'] = df_IN['Trans'].map(diesel)

    # Eliminar valores de insumos e info incluidos en mezclas
    cuentas_op = '50101|50102|50103|50201|50202|50203|50204|50205|50303|50304|50306|60303'
    # Mezclas multi-insumo (Atomizo, Herbicida & Fertilizante)
    mix1 = ((df_IN.Cuenta.str.contains('50101|50102|50202')) & (df_IN.Item.str.contains('AT:|HE:|FE:')))
    lista1 = df_IN[(mix1)][['Trans', 'Item']].drop_duplicates('Trans')
    # Mezclas insumo único (Actividades)
    mix2 = ((df_IN.Cuenta.str.contains(cuentas_op)) & (df_IN.Item.str.contains('IN:')) &
            ~(df_IN.Item.str.contains('Agua')))
    lista2 = df_IN[(mix2)][['Trans', 'Item']].drop_duplicates('Trans')
    lista2 = lista2[~lista2['Trans'].isin(lista1.Trans)]
    # Datos (Labores, Area)
    mix3 = ((df_IN.Cuenta.str.contains(cuentas_op)) & (df_IN.Item.str.contains('Datos:')))
    lista3 = df_IN[(mix3)][['Trans', 'Item']].drop_duplicates('Trans')
    lista3 = lista3[(~lista3['Trans'].isin(lista1.Trans)) & (~lista3['Trans'].isin(lista2.Trans))]
    # Combinar listas
    lista4 = pd.concat([lista1, lista2, lista3]).set_index('Trans').iloc[:,0]   #.squeeze() 1 dim obj into scalars!!

    # Crear columna de mezcla/insumo guia
    df_IN['Mix'] = df_IN['Trans'].map(lista4)

    # Eliminar valores de celdas incluidas en mezclas
    conds = ((df_IN.Mix != df_IN.Item) & (df_IN.Mix.notnull()))
    df_IN['Uds'] = np.where((conds), np.nan, df_IN['Uds'])
    df_IN['Area'] = np.where((conds), np.nan, df_IN['Area'])
    df_IN['Gas'] = np.where((conds), np.nan, df_IN['Gas'])
    df_IN['Diesel'] = np.where((conds), np.nan, df_IN['Diesel'])
    df_IN['Item'] = np.where((conds), '', df_IN['Item'])
    df_IN['Cuenta'] = np.where((conds), '', df_IN['Cuenta'])

    # Eliminar valores de celdas de insumo único (DF ins único sin duplicados + DF multi-insumo)
    df_IN2 = df_IN[(df_IN.Mix.isna())].sort_values(['Trans', 'Cuenta']).drop_duplicates('Trans')
    df_IN2.loc[(df_IN2.Mix.isna()), 'Item'] = 'Datos'
    df_IN2.loc[(df_IN2.Mix.isna()), 'Uds'] = np.nan
    df_IN3 = df_IN[(df_IN.Mix.notna())]
    df_IN = pd.concat([df_IN2, df_IN3])

    # Agrupar insumos por trans, fecha, parcela, modo y factor (Elimina filas de insumos indiv., areas y combustibles)
    df_IN = df_IN.groupby(['Trans', 'Fecha', 'Parcela', 'Modo', 'Factor']).agg(Cuenta=('Cuenta', max),
        Item=('Item', max), Uds=('Uds', sum), Monto=('Monto', sum), Area=('Area', sum), Gas=('Gas', sum), Diesel=('Diesel', sum))
    df_IN.reset_index(inplace=True)

    # Agrupar insumos por semana, cuenta, modo, parcela, factor e item
    df_IN = df_IN.groupby([pd.Grouper(key='Fecha', freq='W-THU'), 'Cuenta', 'Modo', 'Parcela', 'Item'])\
        .agg(IN_Uds=('Uds', sum), IN_CRC=('Monto', sum), Area=('Area', sum), Gas=('Gas', sum), Diesel=('Diesel', sum))
    df_IN.reset_index(inplace=True)

    # Crear columna porcentaje semanal de insumos por parcela
    df_IN['Pct'] = df_IN['IN_Uds'] / df_IN.groupby(['Fecha', 'Cuenta', 'Parcela', 'Modo'])['IN_Uds'].transform('sum')


    # +++++++++++ Procesar MO ++++++++++++++
    df_MO = df[df['Factor'] == 'MO'].copy()

    # Agrupar paychecks por semana, cuenta, modo y parcela
    df_MO = df_MO.groupby([pd.Grouper(key='Fecha',freq='W-THU'),'Cuenta','Labor','Modo','Factor','Parcela'])\
        .agg(Item=('Item',max),Uds=('Uds',sum),Monto=('Monto',sum))
    df_MO.reset_index(inplace=True)
    df_MO = df_MO[['Fecha','Cuenta','Labor','Modo','Parcela','Uds','Monto']]\
    .rename(columns={'Uds':'MO_Hrs','Monto':'MO_CRC'}).copy()
    df_MO['Pct_MO'] = df_MO['MO_Hrs'] / df_MO.groupby(['Fecha','Cuenta','Modo','Parcela'])['MO_Hrs'].transform('sum')


    # +++++++++++ Procesar MAQ ++++++++++++++
    df_MAQ = df[df['Factor'] == 'MAQ'].copy()

    # Agrupar paychecks por semana, cuenta, labor, modo y parcela
    df_MAQ = df_MAQ.groupby([pd.Grouper(key='Fecha',freq='W-THU'),'Cuenta','Labor','Modo','Factor','Parcela'])\
        .agg(Item=('Item',max),Uds=('Uds',sum),Monto=('Monto',sum))
    df_MAQ.reset_index(inplace=True)
    df_MAQ = df_MAQ[['Fecha','Cuenta','Labor','Modo','Parcela','Uds','Monto']]\
    .rename(columns={'Uds':'MAQ_Hrs','Monto':'MAQ_CRC'}).copy()
    df_MAQ['Pct_MAQ'] = df_MAQ['MAQ_Hrs'] / df_MAQ.groupby(['Fecha','Cuenta','Modo','Parcela'])['MAQ_Hrs'].transform('sum')


    # +++++++++++ Unir IN, MO y MAQ y prorratear correspondencias múltiples ++++++++++++++
    # Unir df MO y MAQ, y luego IN por 'Cuenta'
    dt = df_MO.merge(df_MAQ, how='outer', on=['Fecha','Cuenta','Modo','Labor','Parcela'])
    dt = df_IN.merge(dt, how='outer', on=['Fecha','Cuenta','Modo','Parcela'])

    # Ponderar MO y MAQ entre semanas con Insumos/Labores múltiples
    dt = dt.fillna(value={'Pct_MO': 1, 'Pct_MAQ': 1})
    dt['Pct_MO'] = dt.Pct_MO * dt.Pct_MAQ

    dt.IN_Uds = dt.apply(lambda x: x.Pct_MO * x.IN_Uds if x.Pct_MO < 1 else x.IN_Uds, axis=1)
    dt.IN_CRC = dt.apply(lambda x: x.Pct_MO * x.IN_CRC if x.Pct_MO < 1 else x.IN_CRC, axis=1)
    dt.MO_Hrs = dt.apply(lambda x: x.Pct * x.MO_Hrs if x.Pct < 1 else x.MO_Hrs, axis=1)
    dt.MO_CRC = dt.apply(lambda x: x.Pct * x.MO_CRC if x.Pct < 1 else x.MO_CRC, axis=1)
    dt.MAQ_Hrs = dt.apply(lambda x: x.Pct * x.MAQ_Hrs if x.Pct < 1 else x.MAQ_Hrs, axis=1)
    dt.MAQ_CRC = dt.apply(lambda x: x.Pct * x.MAQ_CRC if x.Pct < 1 else x.MAQ_CRC, axis=1)
    dt.Area = dt.apply(lambda x: x.Pct_MO * x.Area if x.Pct_MO < 1 else x.Area, axis=1)
    dt.Gas = dt.apply(lambda x: x.Pct_MO * x.Gas if x.Pct_MO < 1 else x.Gas, axis=1)
    dt.Diesel = dt.apply(lambda x: x.Pct_MO * x.Diesel if x.Pct_MO < 1 else x.Diesel, axis=1)
    dt.drop(['Pct', 'Pct_MO', 'Pct_MAQ'], axis=1, inplace=True)
    dt = dt.fillna(0)

    # Asignar gastos pre-cosecha a 'Cosecha' según periodo Feb-Ene
    dt['Cosecha'] = dt.Fecha.apply(lambda x: x.year+1 if x.month >=2 else x.year)


    # +++++++++++ Procesar REC ++++++++++++++
    df_REC = df[df['Factor'] == 'REC'].copy()
    df_REC['Labor'] = 'RE.Recoleccion'
    df_REC['Modo'] = 'Manual'
    df_REC['Item'] = 'MO'

    # Agrupar transacciones por semana, cuenta, modo, labor y parcela
    df_REC = df_REC.groupby([pd.Grouper(key='Fecha', freq='W-THU'), 'Cuenta', 'Labor', 'Modo', 'Parcela'])\
        .agg(Monto=('Monto', sum))
    df_REC.reset_index(inplace=True)
    df_REC = df_REC[['Fecha','Cuenta','Labor','Modo','Parcela','Monto']].rename(columns={'Monto':'MO_CRC'}).copy()
    df_REC = df_REC.fillna(0)

    # Asignar 'Cosecha' a gastos recoleccion según periodo Abr-Mar
    df_REC['Cosecha'] = df_REC.Fecha.apply(lambda x: x.year+1 if x.month >4 else x.year)


    # +++++++++++ Procesar COS ++++++++++++++
    df_COS = df[df['Factor'] == 'COS'].copy()
    df_COS['Labor'] = 'Produccion'
    df_COS['Modo'] = 'Manual'
    liquidacion = ['Verde (Liquidacion)', 'Maduro (Liquidacion)']
    df_COS.loc[(df_COS['Item'].isin(liquidacion)), 'Uds'] = 0
    df_COS.Uds = df_COS.apply(lambda x: 0 if (x.Fecha.month >=4 and x.Fecha.month <=9) else x.Uds, axis=1)\
                                if df_COS.shape[0] != 0 else np.nan   # Check en caso de no haber produccion

    # Agrupar transacciones por semana, cuenta, labor y parcela
    df_COS = df_COS.groupby([pd.Grouper(key='Fecha', freq='W-THU'), 'Cuenta', 'Labor', 'Modo', 'Parcela'])\
        .agg(Item=('Item', max), Uds=('Uds', sum), Monto=('Monto', sum))
    df_COS.reset_index(inplace=True)
    df_COS = df_COS[['Fecha','Cuenta','Modo','Parcela','Item','Uds','Monto','Labor']].rename(columns={'Uds':'IN_Uds','Monto':'IN_CRC'}).copy()
    df_COS = df_COS.fillna(0)

    # Asignar 'Cosecha' a ingresos según recolección (Oct-Feb) y liquidación (Mar-Dic)
    df_COS['Cosecha'] = np.nan
    df_COS['Cosecha'] = df_COS.apply(lambda x: x.Fecha.year+1 if
                        (x.Cuenta == '40100 · Cosecha Actual' and x.Fecha.month >=10) else x.Fecha.year, axis=1)\
                        if df_COS.shape[0] != 0 else np.nan   # Check en caso de no haber produccion

    # +++++++++++ Unir dt, REC y COS ++++++++++++++
    # Unir df MO y MAQ, y luego IN por 'Cuenta'
    dt = dt.merge(df_REC, how='outer', on=['Fecha','Cuenta', 'Modo', 'Labor','Parcela','Cosecha','MO_CRC'])
    dt = dt.merge(df_COS, how='outer', on=['Fecha','Cuenta', 'Modo', 'Labor','Parcela','Cosecha','Item','IN_Uds','IN_CRC'])
    dt = dt.fillna(0)

    # Crear columnas adicionales
    dt['Tot_CRC'] = dt.IN_CRC + dt.MO_CRC + dt.MAQ_CRC

    familias = {401:'Produccion', 501: 'Fitoproteccion', 502: 'Suelos', 503: 'Tejido', 505: 'Cosecha', 601: 'Maquinaria', 603: 'Indirectos'}
    dt['Familia'] = pd.to_numeric(dt['Cuenta'].str.slice(0, 3), errors='coerce').map(familias)

    dt['Actividad'] = dt['Cuenta'].str.slice(8, 50)

    OT = {'AT': 'Atomizo', 'HE': 'Herbicida', 'FE': 'Fertilizante'}
    dt['Ciclo'] = dt.Item.str.extract(r'([0-9]+\s[A-Z]+\#[A-Za-z0-9]+(\.[0-9]*)*)')[0]
    dt['OT'] = dt.Ciclo.str.slice(5, 7).astype('str').map(OT)

    fincas = {'CE': 'Centro', 'JI': 'Jimenez', 'LA': 'Los Angeles', 'MU': 'Murillos', 'ZA': 'Zona Alta', 'ZG': 'General',
              'ZX': 'Indirectos'}
    dt['Finca'] = dt['Parcela'].str.slice(0, 2).map(fincas)

    dt['Parcela'] = dt['Parcela'].str.slice(3, 100)
    dt = dt[['Fecha', 'Cosecha', 'Familia', 'Actividad', 'Labor', 'Modo', 'OT', 'Ciclo', 'Item', 'Finca', 'Parcela', 'IN_Uds',
             'IN_CRC', 'MO_Hrs', 'MO_CRC', 'MAQ_Hrs', 'MAQ_CRC', 'Tot_CRC', 'Area', 'Diesel', 'Gas']]


    # +++++++++++ Guardar dataframe en Database ++++++++++++++
    df_records = dt.to_dict('records')

    model_instances = []
    for record in df_records:
        record = Database(
                Fecha=record['Fecha'],
                Cosecha=record['Cosecha'],
                Familia=record['Familia'],
                Actividad=record['Actividad'],
                Labor=record['Labor'],
                Modo=record['Modo'],
                OT=record['OT'],
                Ciclo=record['Ciclo'],
                Item=record['Item'],
                Finca=record['Finca'],
                Parcela=record['Parcela'],
                IN_Uds=record['IN_Uds'],
                IN_CRC=record['IN_CRC'],
                MO_Hrs=record['MO_Hrs'],
                MO_CRC=record['MO_CRC'],
                MAQ_Hrs=record['MAQ_Hrs'],
                MAQ_CRC=record['MAQ_CRC'],
                Tot_CRC=record['Tot_CRC'],
                Area=record['Area'],
                Diesel=record['Diesel'],
                Gas=record['Gas'])
        model_instances.append(record)
        if len(model_instances) > 500:      # Anterior 2000
            Database.objects.bulk_create(model_instances)
            model_instances = []
    if model_instances:
        Database.objects.bulk_create(model_instances)

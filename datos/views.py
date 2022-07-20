import csv
import io
import json
import pandas as pd
from datetime import datetime
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max, Min, Sum
from .models import Database, Geojson, Parcelas
from .pandas import db_process
from .plotly import (plotly_treemap_title,
                    plotly_choropleth,
                    plotly_gantt,
                    plotly_treemap)
from .forms import ExportSearchForm, ValidateSearchForm
from .pruebas import date_range, OTsinIN, INsinMO, MAQsinMO, MECsinMO


def database_info(request):
    data_set = Database.objects.all()
    date_from = data_set.Fecha().min()
    date_to = data_set.Fecha().max()

    context = {'date_from': date_from, 'date_to': date_to}
    return render(request, 'datos/csv_upload.html', context)


@login_required
def ValidateDataView(request):
    template = 'datos/validate_data.html'
    fecha_inicial, fecha_final = date_range()
    form = ValidateSearchForm(request.POST or None, initial={'fecha_inicial': fecha_inicial, 'fecha_final': fecha_final})
    context = {'form':form, 'title': 'Validar datos'}

    if request.method == 'POST':
        fecha_inicial = request.POST.get('fecha_inicial')
        fecha_final = request.POST.get('fecha_final')
        reporte = request.POST.get('reporte')

        if fecha_inicial > fecha_final:
            messages.warning(request, "Error: Fecha inicial mayor que fecha final")
            return render(request, template, context)

        check_queryset = Database.objects.filter(Fecha__range=(fecha_inicial, fecha_final))
        if len(check_queryset) > 0:
            reports_dict = {'#1': OTsinIN,'#2': INsinMO,'#3': MAQsinMO,'#4': MECsinMO}
            df_check = pd.DataFrame(check_queryset.values())
            df_check = reports_dict.get(reporte)(df_check)
            df_check = df_check.to_html()
            context = {'form': form, 'df_check': df_check, 'title': 'Validar datos'}

        else:
            messages.info(request, "No hay datos para el periodo seleccionado")

    return render(request, template, context)


@login_required
def DeleteDataView(request):
    data = Database.objects.all()
    if request.method == 'POST':
        data.delete()
        messages.info(request, "Datos eliminados")

    context = {'title': 'Eliminar datos'}
    return render(request, 'datos/delete_data.html', context)


@login_required
def CsvUploadView(request):
    template = 'datos/csv_upload.html'

    # Database info card
    date_from = Database.objects.all().aggregate(Min('Fecha'))['Fecha__min']
    date_to = Database.objects.all().aggregate(Max('Fecha'))['Fecha__max']
    registros = Database.objects.count()
    context = {'date_from': date_from, 'date_to': date_to, 'registros': registros, 'title': 'Cargar datos'}

    # GET request returns the value of the data with the specified key.
    if request.method == 'POST':

        csv_file = request.FILES['file']

        if not csv_file.name.endswith('.CSV'):
            messages.warning(request, 'No es un archivo CSV')
            return render(request, template)

        data_set = csv_file.read().decode('latin1')

        # loop through new data and load to dataframe
        io_string = io.StringIO(data_set)

        datos = []
        for column in csv.reader(io_string):
            dato = [column[0],
                    column[1],
                    column[2],
                    column[3],
                    column[4],
                    column[5],
                    column[6],
                    column[7],
                    column[8],
                    column[9] or 0,
                    column[10]]
            datos.append(dato)

        data_set = pd.read_csv(datos, skiprows=[1], skipfooter=1, encoding='latin1',
                                parse_dates=[1], engine='python')

        # Aplicar funcion para procesar datos
        db_process(data_set)
        messages.info(request, 'Datos cargados satisfactoriamente')
        return redirect('/datos/upload-csv/')

    return render(request, template, context)


@login_required
def ExportView(request):
    template = 'datos/csv_export.html'
    form = ExportSearchForm(request.POST or None)
    context = {'form':form, 'title': 'Exportar datos'}

    if request.method == 'POST':
        fecha_inicial = request.POST.get('fecha_inicial')
        fecha_final = request.POST.get('fecha_final')

        if fecha_inicial > fecha_final:
            messages.warning(request, "Error: Fecha inicial mayor que fecha final")
            return render(request, template, context)

        check_queryset = Database.objects.filter(Fecha__range=(fecha_inicial, fecha_final))
        if len(check_queryset) > 0:

            #Exportar CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="datos.csv"'
            writer = csv.writer(response)
            writer.writerow([
                'Fecha', 'Cosecha', 'Familia', 'Actividad', 'Labor', 'Modo', 'OT',
                'Ciclo', 'Item', 'Finca', 'Parcela', 'IN_Uds', 'IN_CRC', 'MO_Hrs',
                'MO_CRC', 'MAQ_Hrs', 'MAQ_CRC', 'Tot_CRC', 'Area', 'Diesel', 'Gas'])
            for trans in check_queryset.values_list(
                    'Fecha', 'Cosecha', 'Familia', 'Actividad', 'Labor', 'Modo', 'OT', 'Ciclo',
                    'Item', 'Finca', 'Parcela', 'IN_Uds', 'IN_CRC', 'MO_Hrs', 'MO_CRC',
                    'MAQ_Hrs', 'MAQ_CRC', 'Tot_CRC', 'Area', 'Diesel', 'Gas'):
                writer.writerow(trans)
            return response

        else:
            messages.warning(request, "No hay datos para el periodo seleccionado")

    return render(request, template, context)


def IndexView(request):
    context = {}
    return render(request, 'datos/home.html', context)


def DashInfoView(request):
    if all([Parcelas.objects.exists(), Geojson.objects.exists()]):
        context = {}
        return render(request, 'datos/dash_info.html', context)
    else:
        messages.warning(request, "No hay informacion topografica - Primero cargar datos")
        return redirect('/datos/upload-csv/')


def DashSemanaView(request):
    if all([Database.objects.exists(), Parcelas.objects.exists(), Geojson.objects.exists()]):
        context = {}
        return render(request, 'datos/dash_semana.html', context)
    else:
        messages.warning(request, "Base de datos en blanco - Primero cargar datos")
        return redirect('/datos/upload-csv/')


def ChoroplethView(request):
    if all([Database.objects.exists(), Geojson.objects.exists()]):
        parcelas = Parcelas.objects.all()
        df = pd.DataFrame.from_records(parcelas.values())

        geojson = Geojson.objects.all().values('geojson').first().get('geojson')
        geojson = json.loads(geojson)

        fig = plotly_choropleth(df, geojson)

        context = {'choropleth': fig}
        return render(request, 'datos/choropleth.html', context)
    else:
        messages.warning(request, "Base de datos en blanco - Primero cargar datos")
        return redirect('/datos/upload-csv/')



def TreemapView(request):
    if Database.objects.exists():
        datos = Database.objects.all()
        df = pd.DataFrame.from_records(datos.values())

        fig = plotly_treemap_title(df)

        context = {'treemap': fig}
        return render(request, 'datos/treemap.html', context)
    else:
        messages.warning(request, "Base de datos en blanco - Primero cargar datos")
        return redirect('/datos/upload-csv/')


def GanttView(request):
    if Database.objects.exists():
        datos = Database.objects.all()
        df = pd.DataFrame.from_records(datos.values())

        fig = plotly_gantt(df)

        context = {'gantt': fig}
        return render(request, 'datos/gantt.html', context)
    else:
        messages.warning(request, "Base de datos en blanco - Primero cargar datos")
        return redirect('/datos/upload-csv/')

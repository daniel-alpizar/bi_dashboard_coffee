import csv
import io
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render
from .models import Parcelas, QB_Input, Database, Geojson
from django import forms


class CsvImportForm(forms.Form):
    csv_import = forms.FileField


class ParcelasAdmin(admin.ModelAdmin):
    list_display = ('finca', 'parcela', 'area', 'altitud', 'variedad', 'ciclos')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('csv-import/', self.import_csv)]
        return new_urls + urls

    def import_csv(self, request):
        if request.method == 'POST':
            Parcelas.objects.all().delete()

            csv_file = request.FILES['file']

            if not csv_file.name.endswith(('.csv', 'CSV')):
                messages.error(request, 'No es un archivo CSV')

            else:
                data_set = csv_file.read().decode('latin1')
                io_string = io.StringIO(data_set)
                next(io_string)

                for column in csv.reader(io_string):
                    Parcelas.objects.update_or_create(
                        finca=column[0],
                        parcela=column[1],
                        area=column[2],
                        altitud=column[3],
                        variedad=column[4],
                        ciclos=column[5],
                        )

        form = CsvImportForm()
        context = {'form': form}
        return render(request, 'admin/csv_import.html', context)


class GeojsonImportForm(forms.Form):
    geojson_import = forms.FileField


class GeojsonAdmin(admin.ModelAdmin):
    # list_display = ('geojson')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('geojson-import/', self.import_geojson)]
        return new_urls + urls

    def import_geojson(self, request):

        if request.method == 'POST':
            Geojson.objects.all().delete()

            geojson_file = request.FILES['file']

            if not geojson_file.name.endswith(('.geojson', 'GEOJSON')):
                messages.error(request, 'No es un archivo GeoJSON')

            else:
                contents = geojson_file.read()
                data = contents.decode()

                Geojson.objects.update_or_create(
                    geojson=data)

        form = GeojsonImportForm()
        context = {'form': form}
        return render(request, 'admin/geojson_import.html', context)


admin.site.register(Parcelas, ParcelasAdmin)
admin.site.register(Geojson, GeojsonAdmin)
admin.site.register(QB_Input)
admin.site.register(Database)

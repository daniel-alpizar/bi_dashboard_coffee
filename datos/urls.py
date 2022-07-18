from django.urls import include, path
from .views import (
    CsvUploadView,
    ValidateDataView,
    ExportView,
    DeleteDataView,
    DashInfoView,
    DashSemanaView,
    ChoroplethView,
    TreemapView,
    GanttView,
)
from . import plotly  # Necesario importar Plotly apps (No se referencian)
from . import dash_info
from . import dash_semana

urlpatterns = [
    path('upload-csv/', CsvUploadView, name="csv_upload"),
    path('validate-data/', ValidateDataView, name="validate_data"),
    path('export-csv/', ExportView, name="csv_export"),
    path('delete-data/', DeleteDataView, name="delete_data"),
    path('dash-info/', DashInfoView, name="dash_info"),
    path('dash-semana/', DashSemanaView, name="dash_semana"),
    path('choropleth-chart/', ChoroplethView, name="choropleth_chart"),
    path('treemap-chart/', TreemapView, name="treemap_chart"),
    path('gantt-chart/', GanttView, name="gantt_chart"),
    path('django_plotly_dash/', include('django_plotly_dash.urls')),

]

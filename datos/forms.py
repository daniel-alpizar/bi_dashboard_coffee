from django import forms


class ExportSearchForm(forms.Form):
    fecha_inicial = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    fecha_final = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))


report_choices = (
    ('#1', '1. OTs sin Insumos'),
    ('#2', '2. Insumos sin Mano de Obra'),
    ('#3', '3. Maquinaria sin Mano de Obra'),
    ('#4', '4. Mecanizado sin MO o MAQ')
)

class ValidateSearchForm(forms.Form):
    fecha_inicial = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    fecha_final = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    reporte = forms.ChoiceField(choices=report_choices)

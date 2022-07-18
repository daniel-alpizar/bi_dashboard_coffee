from django.db import models


class Parcelas(models.Model):
    finca = models.CharField(max_length=2)
    parcela = models.CharField(max_length=30)
    area = models.FloatField()
    altitud = models.IntegerField(blank=True, null=True)
    variedad = models.CharField(max_length=100, blank=True, null=True)
    ciclos = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f'{self.parcela} - {self.finca} - {self.area}'

    class Meta:
        verbose_name_plural = 'Parcelas'


class Geojson(models.Model):
    geojson = models.TextField()

    class Meta:
        verbose_name_plural = 'Geojson'


class QB_Input(models.Model):
    trans = models.IntegerField()
    date = models.DateField()
    type = models.CharField(max_length=30)
    account = models.CharField(max_length=50)
    payroll = models.CharField(max_length=50, blank=True)
    name = models.CharField(max_length=50)
    source = models.CharField(max_length=100)
    item = models.CharField(max_length=50, blank=True)
    lote = models.CharField(max_length=100)
    qty = models.FloatField(blank=True, null=True)
    amount = models.FloatField()

    def __str__(self):
        return f'{self.lote} - {self.date}'

    class Meta:
        verbose_name_plural = 'QB_Input'


class Database(models.Model):
    Fecha = models.DateField()
    Cosecha = models.IntegerField()
    Familia = models.CharField(max_length=30, blank=True)
    Actividad = models.CharField(max_length=50)
    Labor = models.CharField(max_length=50)
    Modo = models.CharField(max_length=100)
    OT = models.CharField(max_length=20, blank=True)
    Ciclo = models.CharField(max_length=20, blank=True)
    Item = models.CharField(max_length=100)
    Finca = models.CharField(max_length=50)
    Parcela = models.CharField(max_length=50)
    IN_Uds = models.FloatField()
    IN_CRC = models.FloatField()
    MO_Hrs = models.FloatField()
    MO_CRC = models.FloatField()
    MAQ_Hrs = models.FloatField()
    MAQ_CRC = models.FloatField()
    Tot_CRC = models.FloatField()
    Area = models.FloatField()
    Diesel = models.FloatField()
    Gas = models.FloatField()

    def __str__(self):
        return f'{self.Fecha} - {self.Parcela} - {self.Labor}'

    class Meta:
        verbose_name_plural = 'Database'

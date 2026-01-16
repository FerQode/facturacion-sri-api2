from rest_framework import serializers
# ⚠️ CAMBIO AQUÍ: Importamos ServicioModel (que es como tú lo tienes)
from adapters.infrastructure.models import ServicioModel 

class ServicioAguaSerializer(serializers.ModelSerializer):
    class Meta:
        # ⚠️ CAMBIO AQUÍ TAMBIÉN
        model = ServicioModel 
        fields = '__all__'
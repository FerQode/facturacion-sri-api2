from rest_framework import status
from rest_framework.test import APITestCase
from adapters.infrastructure.models import SocioModel, BarrioModel
from django.contrib.auth.models import User

class TestSocioProtection(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testadmin', password='password')
        self.client.force_authenticate(user=self.user)
        self.barrio = BarrioModel.objects.create(nombre="Barrio Test")

    def test_list_socios_safe_hydration(self):
        """
        Confirma que el endpoint GET /socios/ NO explota (500) 
        aunque existan registros históricos inválidos en BD.
        """
        # 1. Inyectamos "basura" en la BD directo (bypass validaciones de serializer/dominio)
        SocioModel.objects.create(
            identificacion="1234567890123", # 13 digitos
            tipo_identificacion="C",        # Pero dice ser Cédula (Invalid!)
            nombres="Socio",
            apellidos="Invalido",
            barrio=self.barrio
        )

        # 2. Consultamos el endpoint
        response = self.client.get('/api/v1/socios/')
        
        # 3. Debe ser 200 OK (La protección _validate=False funcionó)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verificamos que al menos recuperamos datos (depende de paginacion)
        # Si es paginado manual o PageNumberPagination
        if 'results' in response.data:
             self.assertGreaterEqual(len(response.data['results']), 1)
        else:
             self.assertGreaterEqual(len(response.data), 1)

    def test_create_socio_validates_consistency(self):
        """
        Confirma que crear un NUEVO socio sí valida fuertemente.
        """
        payload = {
            "identificacion": "1234567890123", # 13 digitos
            "tipo_identificacion": "C",        # Cédula
            "nombres": "Nuevo",
            "apellidos": "Socio",
            "barrio_id": self.barrio.id,
            "direccion": "Calle Falsa 123"
        }

        response = self.client.post('/api/v1/socios/', payload)
        
        # Debe fallar con 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("identificacion", response.data)
        self.assertIn("10 dígitos", str(response.data["identificacion"]))

    def test_create_socio_success(self):
        """
        Confirma que datos válidos pasan.
        """
        payload = {
            "identificacion": "1104663123", # 10 digitos (puede fallar checksum real, usaremos valida)
            "tipo_identificacion": "C",
            "nombres": "Nuevo",
            "apellidos": "Valido",
            "barrio_id": self.barrio.id,
            "direccion": "Calle Real 123"
        }
        # Usamos una válida de prueba: 1710034065
        payload["identificacion"] = "1710034065"

        response = self.client.post('/api/v1/socios/', payload)
        
        if response.status_code != 201:
            print(response.data)
            
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

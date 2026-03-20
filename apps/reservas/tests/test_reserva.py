from datetime import datetime, timezone
import pytest

from apps.funciones.models import Asiento, Funcion, Pelicula, Sala, TipoFormato
from apps.reservas.models import AsientoReservado, Reserva
from apps.usuario.tests.fixtures_user import get_authenticated_client, get_authenticated_admin_client, get_user_generico, api_client, get_super_user, test_password, grupo_usuarios_registrados, get_authenticated_client_and_user
from apps.funciones.tests.fixtures_funcion import get_tipo_formato, get_tipos_formatos, get_pelicula, get_peliculas, get_funcion, get_funciones, get_funcion_pasada, get_funcion_
from apps.funciones.tests.fixtures_sala import get_sala, get_salas, get_asiento, get_asientos, get_asiento_
from .fixtures_reserva import get_reserva, get_reservas
from apps.usuario.models import Usuario
from rest_framework import status



# Test de integración: Listar reservas con usuario admin
@pytest.mark.django_db
def test_api_listar_reservas(get_authenticated_admin_client, get_reservas):
    
    client = get_authenticated_admin_client

    response = client.get(f'/api/reserva/')

    assert response.status_code == 200

    data = response.data

    print(Reserva.objects.all())

    assert len(data['results']) == len(get_reservas)

    # Extraemos los IDs del response
    response_ids = {reserva['id'] for reserva in data['results']}
    reservas_ids = {reserva.id for reserva in get_reservas}
    # Comparamos que los conjuntos de IDs sean iguales
    assert response_ids == reservas_ids

# Test de integración: Listar reservas con usuario registrado (solo las suyas)
@pytest.mark.django_db
def test_api_listar_reservas2(get_authenticated_client, get_reservas):
    
    client = get_authenticated_client

    response = client.get(f'/api/reserva/')

    assert response.status_code == 200

    data = response.data

    print(Reserva.objects.all())

    assert len(data['results']) != len(get_reservas)

    # Extraemos los IDs del response
    response_ids = {reserva['id'] for reserva in data['results']}
    reservas_ids = {reserva.id for reserva in get_reservas}
    
    assert response_ids != reservas_ids

# Test de integración: Listar reservas sin autenticación falla
@pytest.mark.django_db
def test_api_listar_reservas_falla_usuario_no_autenticado(api_client, get_reservas):
    response = api_client.get(f'/api/reserva/')

    assert response.status_code == 401
    assert str(response.data['detail']) == "Authentication credentials were not provided."

# Test de aceptación: Creación exitosa de reserva
@pytest.mark.django_db
def test_api_creacion_reserva(mocker, get_authenticated_client, get_asientos, get_funcion):
    
    client = get_authenticated_client

    asiento1, asiento2, asiento3 = get_asientos

    funcion = get_funcion

    fecha_actual_mock = datetime(2025, 6, 13, 21, 0, 0, tzinfo=timezone.utc)
    mocker.patch('django.utils.timezone.now', return_value=fecha_actual_mock)

    data = {
        "funcion_id": funcion.id,
        "cantidad_entradas": 3,
        "asientos": [asiento1.id, asiento2.id, asiento3.id]
    }

    response = client.post(f'/api/reserva/', data=data)

    assert response.status_code == 201

    assert Reserva.objects.filter(
        funcion=funcion,
        funcion__activa=True,
        asientos_reservados__asiento__in=[asiento1, asiento2, asiento3]
    ).count() == 1

# Test de aceptación: Creación de reserva falla para función pasada
@pytest.mark.django_db
def test_api_creacion_reserva_falla_funcion_pasada(mocker, get_authenticated_client, get_asientos, get_funcion_pasada):
    
    client = get_authenticated_client

    asiento1, asiento2, asiento3 = get_asientos

    funcion = get_funcion_pasada

    fecha_actual_mock = datetime(2025, 6, 13, 21, 0, 0, tzinfo=timezone.utc)
    mocker.patch('django.utils.timezone.now', return_value=fecha_actual_mock)

    data = {
        "funcion_id": funcion.id,
        "cantidad_entradas": 3,
        "asientos": [asiento1.id, asiento2.id, asiento3.id]
    }

    response = client.post(f'/api/reserva/', data=data)

    assert response.status_code == 400
    assert str(response.data['funcion_id']['info']) == "La función ya pasó."

# Test de aceptación: Creación de reserva falla si asiento ocupado
@pytest.mark.django_db
def test_api_creacion_reserva_falla_asiento_ocupado(mocker, get_authenticated_client, get_asientos, get_reserva, get_funcion):
    
    client = get_authenticated_client

    asiento, _,_= get_asientos

    funcion = get_funcion

    fecha_actual_mock = datetime(2025, 6, 13, 21, 0, 0, tzinfo=timezone.utc)
    mocker.patch('django.utils.timezone.now', return_value=fecha_actual_mock)

    data = {
        "funcion_id": funcion.id,
        "cantidad_entradas": 1,
        "asientos": [asiento.id]
    }

    response = client.post(f'/api/reserva/', data=data)

    assert response.status_code == 400

    assert str(response.data[0]) == "El asiento C1 ya está reservado para esta función."

# Test de aceptación: Creación de reserva falla si cantidad de asientos no coincide
@pytest.mark.django_db
def test_api_creacion_reserva_falla_asientos_de_mas(mocker, get_authenticated_client, get_asientos, get_reserva, get_funcion):
    
    client = get_authenticated_client

    asiento1, asiento2,_= get_asientos

    funcion = get_funcion

    fecha_actual_mock = datetime(2025, 6, 13, 21, 0, 0, tzinfo=timezone.utc)
    mocker.patch('django.utils.timezone.now', return_value=fecha_actual_mock)

    data = {
        "funcion_id": funcion.id,
        "cantidad_entradas": 1,
        "asientos": [asiento1.id, asiento2.id]
    }

    response = client.post(f'/api/reserva/', data=data)

    assert response.status_code == 400

    assert str(response.data['info'][0]) == "La cantidad de asientos no coincide con la cantidad de entradas."

# Test de integración: Modificación de reserva propia
@pytest.mark.django_db
def test_api_modificacion_reserva(mocker, get_authenticated_client, get_reserva, get_asientos):
    
    client = get_authenticated_client

    asiento1, asiento2, asiento3 = get_asientos

    fecha_actual_mock = datetime(2025, 6, 13, 21, 0, 0, tzinfo=timezone.utc)
    mocker.patch('django.utils.timezone.now', return_value=fecha_actual_mock)

    data = {
        "cantidad_entradas": 2,
        "asientos": [asiento1.id, asiento2.id]
    }

    response = client.patch(f'/api/reserva/{get_reserva.id}/', data=data)

    assert response.status_code == 200
    assert response.data['id'] == get_reserva.id
    assert response.data['cantidad_entradas'] == 2
    ids_en_response = [a['asiento']['id'] for a in response.data['asientos_reservados']]
    assert ids_en_response == [asiento1.id, asiento2.id]

# Test de integración: Modificación de reserva ajena falla
@pytest.mark.django_db
def test_api_modificacion_reserva_ajena(mocker, get_authenticated_client_and_user, get_reservas, get_asientos):
    
    user, client = get_authenticated_client_and_user
    reserva1, reserva2, reserva3 = get_reservas
    asiento1, asiento2, asiento3 = get_asientos

    fecha_actual_mock = datetime(2025, 6, 13, 21, 0, 0, tzinfo=timezone.utc)
    mocker.patch('django.utils.timezone.now', return_value=fecha_actual_mock)

    data = {
        "cantidad_entradas": 2,
        "asientos": [asiento1.id, asiento2.id]
    }

    response = client.patch(f'/api/reserva/{reserva2.id}/', data=data)
    
    assert response.status_code == 404
    assert reserva2.usuario != user

# Test de integración: Eliminación de reserva propia
@pytest.mark.django_db
def test_api_eliminacion_reserva(get_authenticated_client, get_reserva):
    
    client = get_authenticated_client

    response = client.delete(f'/api/reserva/{get_reserva.id}/')

    assert response.status_code == 204
    assert Reserva.objects.filter(id=get_reserva.id).count() == 0

#-----------------

# Test unitario: Prueba creación de reserva
@pytest.mark.django_db
def test_api_creacion_reservaf(get_reserva):
    print(get_reserva)
    assert Reserva.objects.filter(funcion=1).exists()
# Test de aceptación: Flujo completo de reserva exitosa
@pytest.mark.django_db
def test_reserva_asiento_no_perteneciente_sala(get_authenticated_client, get_asiento_, get_salas, get_asiento, get_funcion, mocker):
    cliente = get_authenticated_client
    funcion = get_funcion
    sala1, sala2, sala3 = get_salas

# @pytest.mark.django_db
# def test_flujo_completo_reserva_exitosa(mocker, get_authenticated_client, get_asientos, get_funcion):
#     """
#     Escenario: Reserva completa exitosa

#     Given un usuario autenticado y una función con asientos disponibles
#     When realiza una reserva, la consulta, la modifica y la elimina
#     Then el sistema responde correctamente en cada paso
#     """

#     client = get_authenticated_client
#     asiento1, asiento2, _ = get_asientos
#     funcion = get_funcion

#     fecha_actual_mock = datetime(2025, 6, 13, 21, 0, 0, tzinfo=timezone.utc)
#     mocker.patch('django.utils.timezone.now', return_value=fecha_actual_mock)

#     # Paso 1: listar funciones
#     response_list = client.get('/api/funcion/')
#     assert response_list.status_code == 200
#     assert len(response_list.data['results']) > 0

#     # Paso 2: crear reserva
#     data = {
#         "funcion_id": funcion.id,
#         "cantidad_entradas": 2,
#         "asientos": [asiento1.id, asiento2.id]
#     }
#     response_create = client.post('/api/reserva/', data=data)
#     assert response_create.status_code == 201

#     reserva_id = response_create.data['id']

#     # Paso 3: obtener reserva
#     response_get = client.get(f'/api/reserva/{reserva_id}/')
#     assert response_get.status_code == 200
#     assert response_get.data['cantidad_entradas'] == 2

#     # Paso 4: modificar reserva
#     data_update = {
#         "cantidad_entradas": 1,
#         "asientos": [asiento1.id]
#     }
#     response_update = client.patch(f'/api/reserva/{reserva_id}/', data=data_update)
#     assert response_update.status_code == 200
#     assert response_update.data['cantidad_entradas'] == 1

#     # Paso 5: eliminar reserva
#     response_delete = client.delete(f'/api/reserva/{reserva_id}/')
#     assert response_delete.status_code == 204

#     # Verificar eliminación
#     response_get_after = client.get(f'/api/reserva/{reserva_id}/')
#     assert response_get_after.status_code == 404

@pytest.mark.django_db
def test_reserva_misma_sala_diferente_funcion(get_authenticated_client, get_salas, get_peliculas, get_funcion_, mocker, get_asiento):
    client = get_authenticated_client
    sala1, sala2, sala3 = get_salas
    pelicula1, pelicula2, pelicula3 = get_peliculas
    funcion = get_funcion_(pelicula=pelicula1, sala=sala1, fecha="2025-06-15")
    funcion2 = get_funcion_(pelicula=pelicula2, sala=sala1, fecha="2025-06-16")
    asiento = get_asiento

    fecha_actual_mock = datetime(2025, 6, 13, 21, 0, 0, tzinfo=timezone.utc)
    mocker.patch('django.utils.timezone.now', return_value=fecha_actual_mock)

    data = {
        "funcion_id": funcion.id,
        "cantidad_entradas": 1,
        "asientos": [asiento.id]        
    }
    response = client.post(f'/api/reserva/', data=data)
    assert response.status_code == status.HTTP_201_CREATED

    data = {
        "funcion_id": funcion2.id,
        "cantidad_entradas": 1,
        "asientos": [asiento.id]        
    }
    response = client.post(f'/api/reserva/', data=data)
    assert response.status_code == status.HTTP_201_CREATED


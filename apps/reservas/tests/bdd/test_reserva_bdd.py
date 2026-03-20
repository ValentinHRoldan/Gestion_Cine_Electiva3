from pytest_bdd import scenarios, given, when, then
from datetime import datetime
from django.utils import timezone
from apps.reservas.models import Reserva, AsientoReservado
from apps.usuario.tests.fixtures_user import get_authenticated_client
from apps.usuario.tests.fixtures_user import get_user_generico
from apps.usuario.tests.fixtures_user import test_password
from apps.usuario.tests.fixtures_user import grupo_usuarios_registrados
from apps.usuario.tests.fixtures_user import api_client
from apps.funciones.tests.fixtures_funcion import get_funcion
from apps.funciones.tests.fixtures_sala import get_asientos
from apps.funciones.tests.fixtures_sala import get_sala
from apps.funciones.tests.fixtures_funcion import get_pelicula
from apps.funciones.tests.fixtures_funcion import get_tipo_formato
import pytest

pytestmark = pytest.mark.django_db
scenarios("reserva.feature")
@given("un usuario autenticado", target_fixture="contexto")
def contexto(get_authenticated_client):
    return {"client": get_authenticated_client}


@given("existe una funcion futura con asientos disponibles", target_fixture="contexto")
def contexto(contexto, get_funcion, get_asientos, mocker):
    fecha_mock = timezone.make_aware(datetime(2025, 6, 13))
    mocker.patch('django.utils.timezone.now', return_value=fecha_mock)

    asiento1, asiento2, _ = get_asientos

    contexto.update({
        "funcion": get_funcion,
        "asiento1": asiento1,
        "asiento2": asiento2
    })

    return contexto

@when("el usuario crea una reserva")
def crear_reserva(contexto):
    client = contexto["client"]
    funcion = contexto["funcion"]
    asiento1 = contexto["asiento1"]
    asiento2 = contexto["asiento2"]

    response = client.post('/api/reserva/', {
        "funcion_id": funcion.id,
        "cantidad_entradas": 2,
        "asientos": [asiento1.id, asiento2.id]
    })

    assert response.status_code == 201

    contexto["reserva_id"] = response.data["id"]
    contexto["response"] = response

    return contexto

@then("la reserva se crea correctamente")
def validar_reserva(contexto):
    reserva_id = contexto["reserva_id"]

    assert Reserva.objects.filter(id=reserva_id).exists()

@then("los asientos quedan ocupados")
def validar_asientos_ocupados(contexto):
    response = contexto["response"]

    assert len(response.data["asientos_reservados"]) == 1

@when("el usuario modifica la reserva")
def modificar_reserva(contexto):
    client = contexto["client"]
    reserva_id = contexto["reserva_id"]
    asiento1 = contexto["asiento1"]

    response = client.patch(
        f'/api/reserva/{reserva_id}/',
        {
            "cantidad_entradas": 1,
            "asientos": [asiento1.id]
        }
    )

    assert response.status_code == 200
    contexto["response"] = response

    return contexto

@then("la reserva se actualiza correctamente")
def validar_modificacion(contexto):
    assert contexto["response"].data["cantidad_entradas"] == 1

@then("los asientos se actualizan correctamente")
def validar_actualizacion_asientos(contexto):
    funcion = contexto["funcion"]
    asiento1 = contexto["asiento1"]
    asiento2 = contexto["asiento2"]

    # asiento1 sigue ocupado
    assert AsientoReservado.objects.filter(
        asiento=asiento1, funcion=funcion
    ).exists()

    # asiento2 se liberó
    assert not AsientoReservado.objects.filter(
        asiento=asiento2, funcion=funcion
    ).exists()

@when("el usuario elimina la reserva")
def eliminar_reserva(contexto):
    client = contexto["client"]
    reserva_id = contexto["reserva_id"]

    response = client.delete(f'/api/reserva/{reserva_id}/')
    assert response.status_code == 204

    return contexto

@then("la reserva ya no existe")
def validar_eliminacion(contexto):
    reserva_id = contexto["reserva_id"]

    assert not Reserva.objects.filter(id=reserva_id).exists()

@then("los asientos quedan liberados")
def validar_asientos_liberados(contexto):
    funcion = contexto["funcion"]
    asiento1 = contexto["asiento1"]
    asiento2 = contexto["asiento2"]

    assert not AsientoReservado.objects.filter(
        asiento=asiento1, funcion=funcion
    ).exists()

    assert not AsientoReservado.objects.filter(
        asiento=asiento2, funcion=funcion
    ).exists()
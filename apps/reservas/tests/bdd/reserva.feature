Feature: Gestión de reservas
    Scenario: Flujo completo de reserva exitosa
        Given un usuario autenticado
        And existe una funcion futura con asientos disponibles

        When el usuario crea una reserva
        Then la reserva se crea correctamente
        And los asientos quedan ocupados

        When el usuario modifica la reserva
        Then la reserva se actualiza correctamente
        And los asientos se actualizan correctamente

        When el usuario elimina la reserva
        Then la reserva ya no existe
        And los asientos quedan liberados
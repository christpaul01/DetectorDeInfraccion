from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ObjectDoesNotExist
from camaras.models import TipoVehiculo, TipoInfraccion
from django.apps import AppConfig


def create_default_infraccion_types(sender, **kwargs):
    infraccion_data = [
        {"id": 1, "nombre": "Motociclista sin casco", "detalles": "Infraccion por conducir una motocicleta sin casco"},
        {"id": 2, "nombre": "Cruce ilegal", "detalles": "Infraccion por cruzar una intersección de forma ilegal"},
        {"id": 3, "nombre": "Giro en U", "detalles": "Infraccion por realizar un giro en U en una zona prohibida"},
    ]

    for infraccion in infraccion_data:
        # Intenta obtener el tipo de infracción basado en el id_tipo_infraccion
        tipo_infraccion = TipoInfraccion.objects.filter(id_tipo_infraccion=infraccion["id"]).first()

        # Si no existe, lo crea
        if not tipo_infraccion:
            tipo_infraccion = TipoInfraccion.objects.create(
                id_tipo_infraccion=infraccion["id"],
                nombre_tipo_infraccion=infraccion["nombre"],
                detalles=infraccion["detalles"]
            )
            print(f"Infracción '{infraccion['nombre']}' creada exitosamente.")
        else:
            # Si ya existe, verifica si los detalles coinciden, si no, los actualiza
            if (tipo_infraccion.nombre_tipo_infraccion != infraccion["nombre"] or
                tipo_infraccion.detalles != infraccion["detalles"]):
                tipo_infraccion.nombre_tipo_infraccion = infraccion["nombre"]
                tipo_infraccion.detalles = infraccion["detalles"]
                tipo_infraccion.save()
                print(f"Infracción '{infraccion['nombre']}' actualizada con nuevos detalles.")
            else:
                # NOTE: Para pruebas, quitar el comentario la siguiente línea
                # print(f"Infracción '{infraccion['nombre']}' ya existe y está actualizada.")
                pass


from django.core.exceptions import ObjectDoesNotExist
from .models import Umbral


def create_default_thresholds(sender, **kwargs):
    # Datos de los umbrales predeterminados
    threshold_data = [
        {"nombre_umbral": "Threshold_Vehicle", "valor_umbral": 0.5, "notas": "Umbral para la detección de vehículos"},
        {"nombre_umbral": "Threshold_Helmet", "valor_umbral": 0.70, "notas": "Umbral para la detección de cascos"},
        {"nombre_umbral": "Threshold_LicensePlate", "valor_umbral": 0.65,
         "notas": "Umbral para la detección de matrículas"},
    ]

    # Iterar sobre los umbrales para verificar si existen o crearlos
    for threshold in threshold_data:
        try:
            umbral, created = Umbral.objects.get_or_create(
                nombre_umbral=threshold["nombre_umbral"],
                defaults={
                    "valor_umbral": threshold["valor_umbral"],
                    "notas": threshold["notas"]
                }
            )

            if created:
                print(f"Umbral '{threshold['nombre_umbral']}' creado con éxito.")
            else:
                pass
                #print(f"El umbral '{threshold['nombre_umbral']}' ya existe.")
        except ObjectDoesNotExist:
            print(f"Error creando el umbral '{threshold['nombre_umbral']}'.")


# Usar esta función en las señales o llamarla cuando se inicie el sistema


def create_default_vehicle_types(sender, **kwargs):
    vehicle_data = [
        {"id": 2, "nombre": "Coche", "detalles": "Vehículo de cuatro ruedas"},
        {"id": 3, "nombre": "Motocicleta", "detalles": "Vehículo motorizado de dos ruedas"},
        {"id": 5, "nombre": "Autobús", "detalles": "Vehículo grande diseñado para transportar pasajeros"},
        {"id": 7, "nombre": "Camión", "detalles": "Vehículo motorizado diseñado para transportar carga"},
    ]

    for vehicle in vehicle_data:
        # Intenta obtener el tipo de vehículo basado en el id_tipo_vehiculo
        tipo_vehiculo = TipoVehiculo.objects.filter(id_tipo_vehiculo=vehicle["id"]).first()

        # Si no existe, lo crea
        if not tipo_vehiculo:
            tipo_vehiculo = TipoVehiculo.objects.create(
                id_tipo_vehiculo=vehicle["id"],
                nombre_tipo_vehiculo=vehicle["nombre"],
                detalles=vehicle["detalles"]
            )
            print(f"Vehicle type '{vehicle['nombre']}' created successfully.")
        else:
            # Si ya existe, verifica si los detalles coinciden, si no, los actualiza
            if (tipo_vehiculo.nombre_tipo_vehiculo != vehicle["nombre"] or
                tipo_vehiculo.detalles != vehicle["detalles"]):
                tipo_vehiculo.nombre_tipo_vehiculo = vehicle["nombre"]
                tipo_vehiculo.detalles = vehicle["detalles"]
                tipo_vehiculo.save()
                print(f"Vehicle type '{vehicle['nombre']}' updated with new details.")
            else:
                pass
                # print(f"Vehicle type '{vehicle['nombre']}' already exists and is up to date.")




def create_normal_staff_group(sender, **kwargs):
    group_name = 'NormalStaff'

    # Define the expected permissions
    expected_permission_codenames = [
        'add_camara',
        'change_camara',
        'delete_camara',
        'view_camara',
        'add_direccion',
        'change_direccion',
        'delete_direccion',
        'view_direccion',
        'add_roi',
        'change_roi',
        'delete_roi',
        'view_roi',
        'add_infraccion',
        'change_infraccion',
        'view_infraccion',
    ]

    # Check if the group already exists
    group, created = Group.objects.get_or_create(name=group_name)

    if created:
        print(f"Group '{group_name}' created successfully.")

    # Add permissions to the group
    try:
        # Get all permissions matching the expected codenames
        permissions = Permission.objects.filter(codename__in=expected_permission_codenames)

        # Get the current permissions of the group
        current_permissions = group.permissions.all()

        # Extract the codenames of the current permissions
        current_permission_codenames = [perm.codename for perm in current_permissions]

        # Find missing permissions that are not in the group
        missing_permissions = [perm for perm in permissions if perm.codename not in current_permission_codenames]

        if missing_permissions:
            # Add missing permissions to the group
            for permission in missing_permissions:
                group.permissions.add(permission)
            print(f"Added missing permissions to the '{group_name}' group.")
        else:
            pass
            # print(f"All Normal required permissions are already assigned to the '{group_name}' group.")

    except ObjectDoesNotExist:
        print(f"Some permissions were not found.")
        pass


def create_admin_group(sender, **kwargs):
    group_name = 'Admin'

    # Check if the group already exists
    group, created = Group.objects.get_or_create(name=group_name)

    if created:
        print(f"Group '{group_name}' created successfully.")

    # Fetch all permissions
    all_permissions = Permission.objects.all()

    # Get the current permissions of the group
    current_permissions = group.permissions.all()

    # Extract the codenames of the current permissions
    current_permission_codenames = [perm.codename for perm in current_permissions]

    # Find missing permissions that are not already in the group
    missing_permissions = [perm for perm in all_permissions if perm.codename not in current_permission_codenames]

    if missing_permissions:
        # Add missing permissions to the group
        for permission in missing_permissions:
            group.permissions.add(permission)
        print(f"Added all permissions to the '{group_name}' group.")
    else:
        # print(f"All Admin permissions are already assigned to the '{group_name}' group.")
        pass

# Connect the signal to the post_migrate hook
def register_signals():
    post_migrate.connect(create_normal_staff_group)
    post_migrate.connect(create_admin_group)
    post_migrate.connect(create_default_vehicle_types)
    post_migrate.connect(create_default_infraccion_types)
    post_migrate.connect(create_default_thresholds)
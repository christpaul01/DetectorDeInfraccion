from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ObjectDoesNotExist
from django.apps import AppConfig


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
            print(f"All Normal required permissions are already assigned to the '{group_name}' group.")

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
        print(f"All Admin permissions are already assigned to the '{group_name}' group.")

# Connect the signal to the post_migrate hook
def register_signals():
    post_migrate.connect(create_normal_staff_group)
    post_migrate.connect(create_admin_group)
import pcbnew
if hasattr(pcbnew, 'MODULE_3D_SETTINGS_List'):
    from .action_archive_project import ArchiveProject # Note the relative import!
    ArchiveProject().register() # Instantiate and register to Pcbnew
else:
    from .old_version import OldVersion as ReplicateLayout
    ReplicateLayout().register()  # Instantiate and register to Pcbnew

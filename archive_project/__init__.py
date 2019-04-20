try:
    import pcbnew
    if hasattr(pcbnew, 'MODULE_3D_SETTINGS_List'):
        from .action_archive_project import ArchiveProject # Note the relative import!
    else:
        from .old_version import OldVersion as ArchiveProject
    ArchiveProject().register()  # Instantiate and register to Pcbnew
except Exception as e:
    import os
    plugin_dir = os.path.dirname(os.path.realpath(__file__))
    log_file = os.path.join(plugin_dir, 'Archive_project_error.log')
    with open(log_file, 'w') as f:
        f.write(repr(e))

try:
    # Note the relative import!
    from .action_save_restore_layout import SaveRestoreLayout
    # Instantiate and register to Pcbnew
    SaveRestoreLayout().register()
except Exception as e:
    import os
    plugin_dir = os.path.dirname(os.path.realpath(__file__))
    log_file = os.path.join(plugin_dir, 'save_restore_layout_error.log')
    with open(log_file, 'w') as f:
        f.write(repr(e))
    from .no_wxpython import NoWxpython as SaveRestoreLayout
    SaveRestoreLayout().register()

try:
    # Note the relative import!
    from .action_copy_layout import CopyLayout
    # Instantiate and register to Pcbnew
    CopyLayout().register()
except Exception as e:
    import os
    plugin_dir = os.path.dirname(os.path.realpath(__file__))
    log_file = os.path.join(plugin_dir, 'copy_layout_error.log')
    with open(log_file, 'w') as f:
        f.write(repr(e))
    from .no_wxpython import NoWxpython as CopyLayout
    CopyLayout().register()

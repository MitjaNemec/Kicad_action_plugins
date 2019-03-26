try:
    # test for wxpython
    import wx
    # Note the relative import!
    from .action_replicate_layout import ReplicateLayout
    # Instantiate and register to Pcbnew
    ReplicateLayout().register()
except Exception as e:
    import os
    plugin_dir = os.path.dirname(os.path.realpath(__file__))
    log_file = os.path.join(plugin_dir, 'Replicate_layout_error.log')
    with open(log_file, 'w') as f:
        f.write(repr(e))
    from .no_wxpython import NoWxpython as ReplicateLayout
    ReplicateLayout().register()

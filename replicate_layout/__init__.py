try:
    import wx
    from .action_replicate_layout import ReplicateLayout  # Note the relative import!
    ReplicateLayout().register()  # Instantiate and register to Pcbnew
except Exception as e:
    with open('Replicate_layout_error.log', 'w') as f:
        f.write(repr(e))
    from .no_wxpython import NoWxpython as ReplicateLayout
    ReplicateLayout().register()  # Instantiate and register to Pcbnew


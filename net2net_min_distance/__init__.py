try:
    # Note the relative import!
    from .action_net2net_min_distance import Net2NedDistance
    # Instantiate and register to Pcbnew
    Net2NedDistance().register()
except Exception as e:
    import os
    plugin_dir = os.path.dirname(os.path.realpath(__file__))
    log_file = os.path.join(plugin_dir, 'net2net_min_distance_error.log')
    with open(log_file, 'w') as f:
        f.write(repr(e))

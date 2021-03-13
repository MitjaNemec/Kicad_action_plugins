try:
    # Note the relative import!
    from .action_length_stats import LengthStats
    # Instantiate and register to Pcbnew
    LengthStats().register()
except Exception as e:
    import os
    plugin_dir = os.path.dirname(os.path.realpath(__file__))
    log_file = os.path.join(plugin_dir, 'length_stats_error.log')
    with open(log_file, 'w') as f:
        f.write(repr(e))
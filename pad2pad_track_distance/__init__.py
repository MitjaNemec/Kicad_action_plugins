try:
    # Note the relative import!
    from .action_pad2pad_track_distance import Pad2PadTrackDistance
    # Instantiate and register to Pcbnew
    Pad2PadTrackDistance().register()
except Exception as e:
    import os
    plugin_dir = os.path.dirname(os.path.realpath(__file__))
    log_file = os.path.join(plugin_dir, 'Pad2pad_track_distance_error.log')
    with open(log_file, 'w') as f:
        f.write(repr(e))

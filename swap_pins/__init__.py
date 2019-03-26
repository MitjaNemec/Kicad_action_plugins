try:
    # Note the relative import!
    from .action_swap_pins import SwapPins
    # Instantiate and register to Pcbnew
    SwapPins().register()
except Exception as e:
    import os
    plugin_dir = os.path.dirname(os.path.realpath(__file__))
    log_file = os.path.join(plugin_dir, 'Swap_pins_error.log')
    with open(log_file, 'w') as f:
        f.write(repr(e))

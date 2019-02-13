try:
    from .action_place_footprints import PlaceFootprints  # Note the relative import!
    PlaceFootprints().register()  # Instantiate and register to Pcbnew
except Exception as e:
    with open('Replicate_layout_error.log', 'w') as f:
        f.write(repr(e))
    from .no_wxpython import NoWxpython as PlaceFootprints
    PlaceFootprints().register()  # Instantiate and register to Pcbnew


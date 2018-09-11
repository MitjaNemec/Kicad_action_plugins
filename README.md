# KiCad Action Plugin(s)


This repo contains Kicad pcbnew Action Plugins()

## Replicate layout

This plugin has been tested with Kicad 5.0 on Windows 7. You need to have KICAD_SCRIPTING_WXPYTHON enabled.

This plugin has been developed as a complex plugin according the [Python Plugin Development for Pcbnew](https://github.com/KiCad/kicad-source-mirror/blob/master/Documentation/development/pcbnew-plugins.md).

Within the plugin folder only *.py files are required for operation.

While the action plugin works within pcbnew, the `replicatelayout` module can be used also in pcbnew scripting console or even without pcbnew running. Additionally the `replicatelayout.py` module if run standalone will test itself aginst known correct layouts (provided within the plugin folder). This is to ease testing if pcbnew API changes in the future. The `replicatelayout` module does not work with Kicad 4.0.7 as the Python API lacks certain methods.

This plugin replicates layout section. The replication is based upon hierarchical sheets.
Basic requirement for replication is that the section for replication is completely contained within one hierarchical sheet, and replicated sections are just a copy of the same sheet. Complex hierarchies are supported as sheet for replication can contain subsheets. Plugin also replicates module text layout (References, Values and other text bound to a module).

Once the section for replication (pivot section) has been laid out (modules, tracks, text objects and zones placed) you need to:
1. Select anyone of the modules within the pivot section.
2. Run the plugin.
3. Choose which hirarchial level you wish to replicate.
4. choose between linear and circular replication.
5. Enter replication step size (x,y in linear replication and radius, angle (in degrees) for circular replication.
6. Select whether you want to replicate also tracks, zones and/or text objects.
7. Select whether you want to replicate tracks/zones/text which intersect the pivot bounding box or just those contained within the bounding box.
8. Select whether you want to delete already layed out tracks/zones/text (this is useful when updating already replicated layout).
9. Hit OK.

The replication can be linear or circular. For linear replication the plugin will ask for x and y offset (in mm) with respect to pivot section where replicated sections will be placed. For circular replication the plugin will ask for radius (in mm) and angle (in °) with respect to pivot section where replicated sections will be placed.

Additionally you can choose wheather you want to replicate also zones, text and/or tracks. By default only objects which are contained in bounding box constituted by all the modules in the section will be replicated. You can select to replicate also zones and tracks which intersect this bounding box. Additionally, tracks, text and zones already laid out in replicated bounding boxes can be removed (useful when updating). Note that in circular replication, bounding boxes are still squares alligned with x and y axis.

![Bounding box, contained, intersecting definitions](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/Replicate_layout_2.png)

![Bounding box circular replication](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/Replicate_layout_2circular.png)

Example of replication of complex hierarchical project

![Replication](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/Replication.gif)

## Delete Selected

This plugin has been tested with Kicad 5.0 on Windows 7. You need to have KICAD_SCRIPTING_WXPYTHON enabled.

This plugin has been developed as a complex plugin according the [Python Plugin Development for Pcbnew](https://github.com/KiCad/kicad-source-mirror/blob/master/Documentation/development/pcbnew-plugins.md).

Within the plugin folder only *.py files are required for operation.

This plugin deletes selected items. Items can be: zones and/or tracks and/or modules. The main intention is to delete selected tracks to redo part of the layout.

To run the plugin:
1. select items you want to delete (note that in kicad it is different if you start your selection box from left or right)
2. run the plugin
3. select what you want to delete
4. hit OK

![Delete selected tracks and zones](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/Delete_selected_anim.gif)

## pad2pad track distance

This plugin has been tested with Kicad 5.0 on Windows 7. You need to have KICAD_SCRIPTING_WXPYTHON enabled.

This plugin has been developed as a complex plugin according the [Python Plugin Development for Pcbnew](https://github.com/KiCad/kicad-source-mirror/blob/master/Documentation/development/pcbnew-plugins.md).

Within the plugin folder only *.py files are required for operation.

This plugin calculates shortest distance between two pads. The result is not always correct as the algorithm folows the track layout. Also the Via distance is not accounted for. Following picture shows the example where the distacne is not correct as the tracks go to pin #4 and then back over the same tracks as there is no connection between thick and thin track at the encircled area
![Track layout which confuses the algorithm](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/Distance_example.gif)

For complex tracks (GND, Supply rails) the calculation can take quite some time.

To run the plugin:
1. select two pads to measure the distance between
2. run the plugin
3. select what you want to delete
4. hit OK

![Measure pad to pad distance](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/pad2pad_animation.gif)

## Archive project

This plugin has been tested with Kicad 5.0 on Windows 7. You need to have KICAD_SCRIPTING_WXPYTHON enabled. The plugin does not work with post 5.0.0 nightlies (most likely since around 20.7.2018). The testing has not been thorough. The plugin works correctly only when KiCad language is English. For other languages lines 225-243 have to be changed.

This plugin has been developed as a complex plugin according the [Python Plugin Development for Pcbnew](https://github.com/KiCad/kicad-source-mirror/blob/master/Documentation/development/pcbnew-plugins.md).

Within the plugin folder only *.py files are required for operation.

This plugin archives the project thus making it portable.

The schematics archive is achieved via project cache library. The project cache library is copied to project-archive.lib which is modified and added to project symbol library table (if the table does not exist it is created). Also the links to the symbols within the schematics are modified so that they point to the symbols within archive library. Afterwards, the cache library is not refreshed until any change is made in schematics.

The archiving of the pcb and its footprints is already implemented within pcbnew.

The 3D models archive is placed in "shapes3D" subfolder where all 3D models are copied.
Then the links to the models within the layout (.kicad_pcb) file are modified so that they point to the archived 3D models with relative path to the project folder

Plugin is run from pcbnew. When the plugin is run, eeschema has to be closed. If the plugin finished successfully it automatically closes pcbnew. This is normal and required operation.

If the project is modified later it should be archived again in order to stay portable. If a symbol of a unit has to be replaced, all units with same symbol have to be deleted.

## Swap pins

This plugin has been tested with Kicad 5.0 on Windows 7. You need to have KICAD_SCRIPTING_WXPYTHON enabled.

This plugin has been developed as a complex plugin according the [Python Plugin Development for Pcbnew](https://github.com/KiCad/kicad-source-mirror/blob/master/Documentation/development/pcbnew-plugins.md).

Within the plugin folder only *.py files are required for operation.

This plugin swaps two pads (in layout) and coresponding pins (in schematics). The pins in the shematics have to be connected to local or global label or hierarchical label either directly or through short wire segment. The plugin also works across multi unit parts and/or across different hierarchical levels.

Only one pin can be connected. Currently "no connection" flags are not supported. Eeschema has to be closed when the plugin is executed in pcbnew. Once the plugin is done, save the layout, as the undo will only undo the layout leaving schematics in changed state. In order to undo the operation, you have to run the plugin again. 

Example of pin swaping
![swaping of pins on local labels](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/Swap_pins_animation.gif)

## Swap units

This plugin has been tested with Kicad 5.0 on Windows 7. You need to have KICAD_SCRIPTING_WXPYTHON enabled.

This plugin has been developed as a complex plugin according the [Python Plugin Development for Pcbnew](https://github.com/KiCad/kicad-source-mirror/blob/master/Documentation/development/pcbnew-plugins.md).

Within the plugin folder only *.py files are required for operation.

This plugin swaps two units (in layout) and coresponding units (in schematics). Eeschema has to be closed when the plugin is executed in pcbnew. Unit swwapping work across hierarchical pages. Once the plugin is done, save the layout, as the undo will only undo the layout leaving schematics in changed state. In order to undo the operation, you have to run the plugin again.

Example of unit swaping

![swaping units in different hierarchical pages](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/Swap_units_animation.gif)

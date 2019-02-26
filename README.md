# KiCad Action Plugin(s)


This repo contains KiCad pcbnew Action Plugins()

## Replicate layout

This plugin has been tested with KiCad 5.0.2 and 5.1-rc1 on Windows 7. You need to have KICAD_SCRIPTING_WXPYTHON enabled.

This plugin has been developed as a complex plugin according the [Python Plugin Development for Pcbnew](https://github.com/KiCad/kicad-source-mirror/blob/master/Documentation/development/pcbnew-plugins.md) guide.

Within the plugin folder only the *.py files are required for operation.

While the action plugin works within pcbnew, the `replicatelayout` module can be used also in the pcbnew scripting console or even without pcbnew running. If the `replicatelayout.py` is run standalone, it will test itself against known correct layouts (provided within the plugin folder). This is to ease testing if the pcbnew API changes in the future. The `replicatelayout` module does not work with KiCad 4.0.7 as the Python API lacks certain methods.

The purpose of this plugin is to replicate layout sections. The replication is based upon hierarchical sheets.
The basic requirement for replication is that the section to be replicated is completely contained within a single hierarchical sheet, and replicated sections are just copies of the same sheet. Complex hierarchies are supported because as replicated sheet can contain subsheets. The plugin replicates footprints, zones, tracks and text.

After the section for replication (pivot section) has been laid out (modules, tracks, text objects and zones placed) you need to:
1. Place the anchor modules for the sections you want to replicate. This defines the position and orientation of replicated sections. You can use [Place footprints] action plugin for this.
2. Select the same anchor module within the pivot section.
3. Run the plugin.
4. Choose which hierarchical level you wish to replicate.
5. Select which sheets you want to replicate (default is all of them)
6. Select whether you want to replicate also tracks, zones and/or text objects.
7. Select whether you want to replicate tracks/zones/text which intersect the pivot bounding box or just those contained within the bounding box.
8. Select whether you want to delete already laid out tracks/zones/text (this is useful when updating an already replicated layout).
9. Hit OK.

Additionally you can choose whether you want to also replicate zones, text and/or tracks. By default, only objects which are contained in the bounding box constituted by all the modules in the section will be replicated. You can select to also replicate zones and tracks which intersect this bounding box. Additionally, tracks, text and zones which are already laid out in the replicated bounding boxes can be removed (useful when updating). Note that bounding boxes are squares aligned with the x and y axis, regardless of section orientation.

Example replication of a complex hierarchical project. Replicating inner sheet first, then outer.

![Replication](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/replicate.gif)

## Place footprints

This plugin has been tested with KiCad 5.1 nightly from commit b426b9e7 onward on Windows 7. You need to have KICAD_SCRIPTING_WXPYTHON enabled.

This plugin has been developed as a complex plugin according the [Python Plugin Development for Pcbnew](https://github.com/KiCad/kicad-source-mirror/blob/master/Documentation/development/pcbnew-plugins.md) guide.

Within the plugin folder only the *.py files are required for operation.

This plugin will place footprints in:
- in line
- circular
- in square matrix

The plugins for placement are selected either by consecutive reference numbers or by same ID on different hierarchical sheets.

If you want to place the footprints by consecutive reference numbers you have to
1. select a footprint which is first in the sequence to be placed
2. run the plugin
3. select which place by reference number
4. choose which footprint in the sequence you want to place
5. select the arrangement (linear, matrix, circular)
6. select place dimension (step in x and y axes in linear and matrixc mode and angle step and radius in circlar mode)
7. run the plugin

If you want to place the footprints by same ID with
1. select a footprint which is first in the sequence to be placed
2. run the plugin
3. select the hierarchical level by which the footprints will be placed (in complex hierarchies)
4. choose from which sheets you want the footprint to place
5. select the arrangement (linear, matrix, circular)
6. select place dimension (step in x and y axes in linear and matrixc mode and angle step and radius in circlar mode)
7. run the plugin

Example of place by reference number
![Place by referenc number](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/place_by_ref.gif)

Example of place by sheet ID
![Place by sheet ID ](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/place_by_sheet.gif)


## Delete Selected

This plugin has been tested with KiCad 5.0 on Windows 7. You need to have KICAD_SCRIPTING_WXPYTHON enabled.

This plugin has been developed as a complex plugin according the [Python Plugin Development for Pcbnew](https://github.com/KiCad/kicad-source-mirror/blob/master/Documentation/development/pcbnew-plugins.md) guide.

Within the plugin folder only the *.py files are required for operation.

This plugin deletes selected items. Items can be: zones and/or tracks and/or modules. The main intention is to delete selected tracks in order to redo parts of the layout.

To run the plugin:
1. Select items you want to delete (note that in KiCad it is different if you start your selection box from left or right)
2. Run the plugin
3. Select what you want to delete
4. Hit OK

![Delete selected tracks and zones](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/Delete_selected_anim.gif)

## pad2pad track distance

This plugin has been tested with KiCad 5.1 nightly from commit b426b9e7 onward on Windows 7. You need to have KICAD_SCRIPTING_WXPYTHON enabled.

This plugin has been developed as a complex plugin according the [Python Plugin Development for Pcbnew](https://github.com/KiCad/kicad-source-mirror/blob/master/Documentation/development/pcbnew-plugins.md) guide.

Within the plugin folder only the *.py files are required for operation.

This plugin calculates the shortest distance between two pads. Use with caution because the result is not always correct as the algorithm follows the track layout. Also, the Via distance is not accounted for. The following picture shows an example where the distance is not correct. Here, the algorithm calculates the distance from the first pad to pin #4 and then to the other pad. It does not consider the connection between the two tracks at the encircled area where they actually branch off making the measured distance longer than it actually is.
![Track layout which confuses the algorithm](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/Distance_example.gif)

For complex tracks (GND, Supply rails) the calculation can take quite some time.

To run the plugin:
1. Select two pads to measure the distance between
2. Run the plugin
3. Select what you want to delete
4. Hit OK

![Measure pad to pad distance](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/pad2pad_animation.gif)

## net2net min distance

This plugin has been tested with KiCad 5.1 nightly from commit b426b9e7 onward on Windows 7. You need to have KICAD_SCRIPTING_WXPYTHON enabled.

This plugin has been developed as a complex plugin according the [Python Plugin Development for Pcbnew](https://github.com/KiCad/kicad-source-mirror/blob/master/Documentation/development/pcbnew-plugins.md) guide.

Within the plugin folder only the *.py files are required for operation.

This plugin calculates the shortest distance between two tracks on different nets. To use, select one pad on first net and one pad on second net and run the plugin.

## Archive project

This plugin has been tested with KiCad 5.0 on Windows 7. You need to have KICAD_SCRIPTING_WXPYTHON enabled. The plugin does not work with post 5.0.0 nightlies (most likely since around 20.7.2018). The testing has not been thorough. The plugin works correctly only when KiCad language is English. For other languages, the lines 225-243 have to be adapted.

This plugin has been developed as a complex plugin according the [Python Plugin Development for Pcbnew](https://github.com/KiCad/kicad-source-mirror/blob/master/Documentation/development/pcbnew-plugins.md) guide.

Within the plugin folder only the *.py files are required for operation.

This plugin archives the project thus making it portable.

The schematics archive is achieved via the project cache library. The project cache library is copied to project-archive.lib which is modified and added to the project symbol library table (if the table does not exist it is created). Also the links to the symbols within the schematics are modified so that they point to the symbols within the archive library. Afterwards, the cache library is deleted. Eeschema will recreate a correct cache library the next time the schematics are edited.

The archiving of the pcb and its footprints is already implemented within pcbnew.

The 3D models archive is placed in "shapes3D" subfolder where all 3D models are copied.
Then, the links to the models within the layout (.kicad_pcb) file are modified so that they point to the archived 3D models with a path relative to the project folder.

The plugin is run from pcbnew. When the plugin is run, eeschema has to be closed. If the plugin finished successfully, it automatically closes pcbnew. This behavior is expected and required to perform the operation.

If the project is modified later it should be archived again in order to stay portable. If a symbol of a unit has to be replaced, all units with the same symbol have to be deleted.

## Swap pins

This plugin has been tested with KiCad 5.0 on Windows 7. You need to have KICAD_SCRIPTING_WXPYTHON enabled.

This plugin has been developed as a complex plugin according the [Python Plugin Development for Pcbnew](https://github.com/KiCad/kicad-source-mirror/blob/master/Documentation/development/pcbnew-plugins.md) guide.

Within the plugin folder only the *.py files are required for operation.

This plugin swaps two pads (in layout) and their corresponding pins (in schematics). The pins in the schematics have to be connected to a local or global label or hierarchical label either directly or through a short wire segment. The plugin also works across multi-unit parts and/or across different hierarchical levels.

Only one pin can be connected. Currently "no connection" flags are not supported. Eeschema has to be closed when the plugin is executed in pcbnew. Once the plugin is done, you should save the layout. Note that using undo will only undo the change in the layout, but not the change in the schematics. To reverse the operation, you can run the plugin again.

Example of pin swapping
![swapping of pins on local labels](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/Swap_pins_animation.gif)

## Swap units

This plugin has been tested with KiCad 5.0 on Windows 7. You need to have KICAD_SCRIPTING_WXPYTHON enabled.

This plugin has been developed as a complex plugin according the [Python Plugin Development for Pcbnew](https://github.com/KiCad/kicad-source-mirror/blob/master/Documentation/development/pcbnew-plugins.md) guide.

Within the plugin folder only the *.py files are required for operation.

This plugin swaps two units (in layout) and r units (in schematics). Eeschema has to be closed when the plugin is executed in pcbnew. Unit swapping work across hierarchical pages.  Note that using undo will only undo the change in the layout, but not the change in the schematics. To reverse the operation, you can run the plugin again.

Example of unit swapping

![swapping units in different hierarchical pages](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/Swap_units_animation.gif)

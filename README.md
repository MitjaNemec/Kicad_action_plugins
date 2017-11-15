KiCad Action Plugin(s)
=====

This repo contains Kicad pcbnew Action Plugins()

Replicate layout
-----------
This plugin has been tested on Windows 7 Kicad nightly 2017-09-19 revision dddaa7e69. 

hile the action plugin works within pcbnew, the `replicatelayout` module can be used also in pcbnew scripting console. For example look at lines 210, 211 in `replicatelayout.py`. Aditionally the `replicatelayout.py` module if run standalon will test itself aginst known correct layouts. This is to ease testing if pcbnew API changes in the future.

This plugin replicates layout section. The replication is based upon hiearchical sheets.
Basic erquirement for replication is that the section for replication is completely contained within one hiearchical sheet, and replicated sections are just a copy of the same sheet. The example can be seen in this two pictures.

[Top sheet schematics](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/Replicate_layout_0.png)
[Hiearchical sheet to replicate](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/Replicate_layout_1.png)

Once the section for replication (pivot section) has been layout out (modules, tracks and zones placed) you need to select any of the modules within this section and run the plugin.

The plugin will ask for x and y offset (in mm) with respect to pivot section where replicated sections will be placed. Additionaly you can choose wheather to replicate only tracks and zones which are within the bounding box constituted by all the modules in the section. Otherwise even zones and tracks which only intersect this bounding box will also be replicated.

[Bounding box, contained, intersecting definitions](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/Replicate_layout_2.png)

Example of replication of only contained tracks and zones

[Replication of only contained tracks and zones](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/Contained.gif)

Example of replication including intersecting zones and tracks

[Replication including intersecting zones and tracks](https://raw.githubusercontent.com/MitjaNemec/Kicad_action_plugins/master/screenshots/Intersecting.gif)
# USD Example scripts
This example contains two scripted plugins with USD for 3ds Max : A modifier and a helper node.

## Installation
Place `max-2021-usd-examples` folder in one of the ApplicationPlugins folder paths:

`C:\Program Data\Autodesk\ApplicationPlugins\max-2021-usd-examples`

or 

`C:\Users\{username}\AppData\Roaming\Autodesk\ApplicationPlugins\max-2021-usd-examples`

## USD Export Helper
The general use case for an export helper:

- It is generally useful to save the export settings for an asset into the scene to re-export quickly.
- The export helper creates a root-level transform which becomes the root transform of the exported asset.
- Export roots can be normalized on export allowing a scene full of assets (for example, a set which shares common materials) to easily be exported without making destructive modification in your source scene.


## USD Export Modifier
Same use case as above - but doesn't add an extra transform to the root.

Export modifier supports instanced modifier usage. 

Options:

* Export Children

    - Use this to disable or enable the children of this node. By default this is on.

* Export End Result

    - When disabled, all modifiers above the USD Export Modifier are disabled prior to export.

## Asset Parameters

Both the export modifier and the export helper share these options.
- Export Normalized
    - When enabled, all exported root-level nodes are normalized: transforms are set to identity (0,0,0).


plugin helper usdExportSceneHelper
name:"Scene Export"
category:"USD"
classID:#(0x4de88987, 0x4d995a0)
extends:PointHelperObj 
replaceUI:false 
initialRollupState:0x1 --first rollup is closed
version:1
(	
	include "usd_scene_asset_params.ms"
	include "usd_scene_export_params.ms"
)
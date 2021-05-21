plugin modifier usdExportMod
name:"USD Export"
classID:#(0x5f6f1c2f, 0x4c7ef0eb)
extends:EmptyModifier 
replaceUI:true 
version:1
(
	include "usd_export_common_params.ms"
	include "usd_export_modifier_params.ms"
	include "usd_asset_params.ms"
)
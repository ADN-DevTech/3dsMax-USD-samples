plugin helper usdExportHelper
name:"Asset Export"
category:"USD"
classID:#(0x6777ac9d, 0x35295fb5)
extends:PointHelperObj 
replaceUI:false 
initialRollupState:0x1 --first rollup is closed
version:1
(
	include "usd_export_common_params.ms"
	include "usd_asset_metadata.ms"
	include "usd_asset_params.ms"
)
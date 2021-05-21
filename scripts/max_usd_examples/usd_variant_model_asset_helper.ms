plugin helper usdVariantModelAssetHelper
name:"Variant Asset"
category:"USD"
classID:#(0x3a72654a, 0x66e0221b)
extends:PointHelperObj
replaceUI:false
initialRollupState:0x1 --first rollup is closed
version:1
(
    include "usd_variant_params.ms"
    include "usd_asset_params.ms"
)
--The scripts should always contain at least 10 functions :
--   ScriptID, DisplaySourceName(), SourceSuperClassID(), SourceClassID(), DisplayDestinationName() 
--   DestinationSuperClassID(), DestinationClassID(), AboutText() and DefaultConversion, Conversion taking a param.
--Script ID that will append to destination

fn ScriptID = 
(
    ""
)

--Return the name to be display for the source in the Scene Converter UI
fn DisplaySourceName =
(
    #("StingrayPBS")
)

--Returns the source class of the super class id 
fn SourceSuperClassID =
(
    #(3072, 3072) --Material
)
--Returns the class id of the source class we use as a source for conversion
fn SourceClassID =
(
    #(249140708L, 1630788338L)
)

--Return the name to be display for the destination in the Scene Converter UI - must be in the order than the destination class ids
fn DisplayDestinationName =
(
    "Physical Material"
)

--Returns the destination class of the super class id
fn DestinationSuperClassID =
(
    3072 --Material
)

--Returns the class id of the class we use as a destination for conversion
-- so we convert from SourceClassID() to DestinationClassID()
fn DestinationClassID =
(
    #(1030429932L, 3735928833L) --Physical Material
)

--Validate that the source provided match with one of the SourceClass
fn VerifySource source =
( 
    local ret = false
    local src = SourceClassID()

    if(source == undefined) do return false

    if(classof src[1] == Array) then
    (
        for cd in src do
        (
            if((cd as string) == (source.ClassID as string)) do
            (
                ret = true
            )
        )
    )
    else
    (
        if((src as string) == (source.ClassID as string)) do
        (
            ret = true
        )
    )
	return ret
    --ret = IsStandin source 
)

--Validate that the destination provided match with one of the DestinationClass
fn VerifyDestination destination =
(
    local ret = false	
    local dest = DestinationClassID()

    if(destination == undefined) do return false

    if(classof dest[1] == Array) then
    (
        for cd in dest do
        (
            if((cd as string) == (destination.ClassID as string)) do
            (
                ret = true
            )
        )
    )
    else
    (
        if((dest as string) == (destination.ClassID as string)) do
        (
            ret = true
        )
    )
    ret 
)

--Returns some information about this conversion script
fn AboutText =
(
    "Converts StingrayPBS materials to Physical materials"
)

fn AddClamping src =
(
    if (src != undefined) then
    (
        local o = Output()
        o.map1 = src
        o.output.clamp = true
        o
    )
    else
        undefined
)

fn IsStandin source = 
(
	local ret = false
	if((source.ClassID as string) == "#(4294967295L, 0L)") do
	(
		ret = true
	)
	ret
)

fn getPropertyValue source prop =
(
	local ret = undefined
	if (IsStandin source) then (
		ret = GetStandinProperty source prop
	)
	else (
		ret = getProperty source prop
	)
	ret
)

fn getBitmapValue source property = 
(
	local map = undefined
	try (map = getPropertyValue source property) catch ()
	
	if (map != undefined) then
	(
		local full_path = mapPaths.getFullFilePath map.filename
		local bitmap_texture = Bitmaptexture ()
		bitmap_texture.filename = full_path
		return bitmap_texture
	)
	else
	(
		print("undefined texture")
		return undefined
	)
)

--Internal function that does the parameter mapping
fn ConvertFrom_SourceMtlToDestMat source dest =
(
    if ( false == VerifySource Source or 
         false == VerifyDestination Dest
        ) do
    (
        --Not the suitable nodes
        return undefined
    )

    dest.brdf_mode  = true
    dest.material_mode = 1

    dest.base_weight           =    1.0
    local diffuse = getPropertyValue source "base_color"
    dest.base_color            =    diffuse              -- Diffuse color

    if ((IsProperty diffuse "controller") and (diffuse.controller != undefined)) do (
        dest.base_color.controller = diffuse.controller
    )

    dest.base_color_map_on     =    (getPropertyValue source "use_color_map") > 0.0    -- Diffuse texture On/Off
	dest.base_color_map        =   getBitmapValue source "TEX_color_map"
	print dest.base_color_map

    local roughness        = getPropertyValue source "roughness"   -- Diffuse roughness
    dest.roughness        =  roughness
    if((IsProperty roughness "controller") and (roughness.controller != undefined)) do (
        dest.roughness.controller = roughness.controller
    )

    dest.diff_rough_map_on     =  getPropertyValue source "use_roughness_map" > 0.0   -- Diffuse roughness map on/off
    dest.roughness_map          = getBitmapValue source "TEX_roughness_map"       -- Diffuse roughness map


    --dest.roughness             =    getPropertyValue source "reflection_glossiness"            -- Specular Roughness
    --dest.roughness_inv         =    true

    --dest.roughness_map         =  getPropertyValue source "texmap_reflectionGlossiness"       -- Specular Roughness map
    --dest.roughness_map_on      =  getPropertyValue source "texmap_reflectionGlossiness_on"     -- Specular Roughness map On/Off


	--dest.transparency = 0.0

    --dest.trans_roughness      =  getPropertyValue source "refraction_glossiness"
    --dest.trans_roughness_inv  =  true
    --dest.trans_roughness_lock =  false

    ---dest.trans_color_map      =  getPropertyValue source "texmap_refraction"
    --dest.trans_color_map_on   =  getPropertyValue source "texmap_refraction_on"

    --dest.trans_rough_map      =  getPropertyValue source "texmap_refractionGlossiness"
    --dest.trans_rough_map_on   =  getPropertyValue source "texmap_refractionGlossiness_on"

    -- Converts metalnees map
    dest.metalness              = getPropertyValue source "metallic"
    dest.metalness_map     =  getBitmapValue source "TEX_metallic_map"
    dest.metalness_map_on  =  getPropertyValue source "use_metallic_map" > 0.0

    -- Converts normal map
    dest.bump_map_on          =  getPropertyValue source "use_normal_map" > 0.0
    dest.bump_map             =  getBitmapValue source "TEX_normal_map"
    --dest.bump_map_amt         =  getPropertyValue source "texmap_bump_multiplier" / 100.0

    -- Converts displacement map
    --dest.displacement_map_on  =  getPropertyValue source "texmap_displacement_on"
    --dest.displacement_map     =  getPropertyValue source "texmap_displacement"
    --dest.displacement_map_amt =  getPropertyValue source "texmap_displacement_multiplier" / 100.0

    -- Converts opacity map
    --dest.cutout_map        =  getPropertyValue source "texmap_opacity"
    --dest.cutout_map_on     =  getPropertyValue source "texmap_opacity_on"

    -- Emission 
    dest.emit_color           =  getPropertyValue source "emissive"
    dest.emission             =  getPropertyValue source "emissive_intensity"

    local selfIllumination = getPropertyValue source "emissive"
    if((IsProperty selfIllumination "controller") and (selfIllumination.controller != undefined)) do (
        dest.emit_color.controller = selfIllumination.controller
    )
    /*
	(
        local physical_scale = 1500
        local compensate_camera_exposure = getPropertyValue source "compensate_camera_exposure"
       if(compensate_camera_exposure) do
       (
           local p = SceneExposureControl.exposureControl

           if p != undefined do 
           (
              physical_scale = p.physical_scale
           )

           dest.emit_luminance = getPropertyValue source "selfIllumination_multiplier" / 3.1415 * physical_scale
      )
    )
	*/
    dest.emit_color_map        =  getBitmapValue source "TEX_emissive_map"
    dest.emit_color_map_on     =  getPropertyValue source "use_emissive_map" > 0.0

    dest
)

--This function is use as entry when the source is missing (due to a missing plugin) and cannot be completly loaded. 
--In that case a default object is created and returned.
fn DefaultConversion source /*Not use*/=
(
    --Create the dest material
    newMat = PhysicalMaterial()

    --return the new material
    newMat

)

--Main entry point from this script
--This function handles the material's creation
fn Conversion sourceMtl =
(
    if (false == VerifySource sourceMtl )  do
    (
        --Not the suitable node
        return undefined
    )
    
    --Create the dest material
    newMat = PhysicalMaterial()
    
    --Call the parameters mapping function to convert
    ConvertFrom_SourceMtlToDestMat sourceMtl newMat

    if (IsProperty sourceMtl "name") and (undefined != sourceMtl.name) and (String == classof sourceMtl.name)  and (IsProperty newMat "name") do
    (
        newMat.name = sourceMtl.name
    )

    --return the new material
    newMat
)
--old_mat = $.material
--old_mat.numberofbitmaps() 
--showProperties old_mat
--getProperty old_mat "TEX_roughness_map"
--btmp = getPropertyValue old_mat "TEX_color_map"
--new_mat = Conversion old_mat
--$.material = new_mat



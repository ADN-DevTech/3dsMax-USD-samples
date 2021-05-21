parameters usdAssetParams rollout:usdAssetParamsRollout
(
	exportNormalized type:#boolean ui:exportNormalized default:true
	exportFileName type:#string animatable:false ui:exportFileName default:""
	-- usd_kind type:#string
)

fn get_export_script = (
	imp_lib = Python.Import "imp"
	py_usd_export_mod = python.import("usd_export_utils")
	python.reload(py_usd_export_mod)
	return py_usd_export_mod
)

fn do_export_from_mod_panel _mod _nodes overwrite:undefined = (
	if USDExporter != undefined then (
		try (
			local export_script = get_export_script()
			export_script.export_from_modify_panel _mod _nodes overwrite:overwrite
			) catch (
				messageBox "Something went wrong. Check Maxscript Listener"
				format "*** % ***\n" (getCurrentException())
		)
	) else 
	(
		messageBox "Please install USD for Autodesk 3ds Max." icon:#warning title:"USD Exporter"
	)
)

rollout usdAssetParamsRollout "Asset Parameters"
(
	checkbox exportNormalized "Move to Origin"
	-- dropdownlist kind_dd "Model Kind:" items:#("Group", "Assembly", "Component", "SubComponent") selection:3
	-- on kind_dd selected i do (
	-- 	selected_kind_str = kind_dd.items[i]
	-- 	usd_kind = (toLower selected_kind_str)
	-- )
	label filenameLabel "File Name:" align:#left
	edittext exportFileName align:#left width:125 across:2 offset:[-10, 0]
	button browseButton "..." align:#right height:18 width:24 offset:[5, 0]
	on browseButton pressed do (
		local seed_filename = exportFileName.text
		if ( export_filename == "" ) do (
			seed_filename = maxFilePath + owningNodes[1].name
		)
		local specified_path = getSaveFileName caption:"USD Export Path" types:"USD (*.usd)|*.usd|USDA (*.usda)|*.usda|USDC (*.usdc)|*.usdc|USDZ (*.usdz)|*.usdz" filename:seed_filename historyCategory:"USD"
		if specified_path == undefined do (
			return 0
		)
		exportFileName.text = specified_path
	)
	button exportButton "Export" width:150
	on exportButton pressed do 
	(
		local owningNodes = refs.dependentNodes this
		local overwrite = undefined
		if ( owningNodes[1] != undefined ) then (
			if exportFileName.text == "" do (
				local seed_filename = maxFilePath + owningNodes[1].name
				local specified_path = getSaveFileName caption:"USD Export Path" types:"USD (*.usd)|*.usd|USDA (*.usda)|*.usda|USDC (*.usdc)|*.usdc|USDZ (*.usdz)|*.usdz" filename:seed_filename historyCategory:"USD"
				if specified_path == undefined do (
					return 0
				)
				exportFileName.text = specified_path
				overwrite = True
			)
			
			do_export_from_mod_panel this owningNodes overwrite:overwrite
		)
	)
	
	button usdViewButton "Open in USDView" width:150
	on usdViewButton pressed do
	(
		if UsdExporter != undefined then (
			try (
				export_filename = exportFilename.text
				local export_script = get_export_script()
				export_script.open_in_usd_view(export_filename)
			) catch (
				messageBox "Something went wrong. Check Maxscript Listener"
				format "*** % ***\n" (getCurrentException())
				)
		) else (
			messageBox "Please install USD for Autodesk 3ds Max." icon:#warning title:"USD Exporter"
		)
	)

)

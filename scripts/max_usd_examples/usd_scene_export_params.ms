fn get_scene_export_script = (
    py_usd_export_mod = python.import("usd_export_with_assets")
    python.reload(py_usd_export_mod)
    return py_usd_export_mod
)

fn get_scene_export_utils_script = (
    py_usd_export_mod = python.import("usd_export_utils")
    python.reload(py_usd_export_mod)
    return py_usd_export_mod
)


fn do_export_scene_with_assets _node overwrite:undefined = (
    if USDExporter != undefined then (
        try (
            local export_script = get_scene_export_script()
            export_script.export_from_helper _node overwrite:overwrite
            ) catch (
                messageBox "Something went wrong. Check Maxscript Listener"
                format "*** % ***\n" (getCurrentException())
        )
    ) else
    (
        messageBox "Please install USD for Autodesk 3ds Max." icon:#warning title:"USD Exporter"
    )
)
    
parameters usdSceneExportParams rollout:usdSceneExportParamsRollup
(
    exportFileName type:#string animatable:false ui:exportFileName default:""
    splitScene type:#boolean animatable:false ui:splitScene default:False
)
rollout usdSceneExportParamsRollup "Scene Export"
(
    checkbox splitScene "Split scene assets"

    label filenameLabel "Scene File Name:" align:#left
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
        relative_path = pathConfig.convertPathToRelativeTo  specified_path maxFilePath
        exportFileName.text = relative_path
    )

	button exportSceneButton "Export Scene" width:150
    on splitScene changed value do (
        --usdSceneAssetParamsRollup.updateEnabledStates()
    )
    on exportSceneButton pressed do 
    (
        local owningNodes = refs.dependentNodes this
        local overwrite = undefined
        if ( owningNodes[1] != undefined ) then 
        (
            if exportFileName.text == "" do 
            (
                local seed_filename = maxFilePath + (getFilenameFile maxFileName)
                local specified_path = getSaveFileName caption:"USD Export Path" types:"USD (*.usd)|*.usd|USDA (*.usda)|*.usda|USDC (*.usdc)|*.usdc|USDZ (*.usdz)|*.usdz" filename:seed_filename historyCategory:"USD"
                if specified_path == undefined do 
                (
                    return 0
                )
                relative_path = pathConfig.convertPathToRelativeTo  specified_path maxFilePath
                exportFileName.text = relative_path
                overwrite = True
            )
            do_export_scene_with_assets this overwrite:overwrite
        )
    )
    
    button usdViewButton "Open in USDView" width:150
    on usdViewButton pressed do
    (
        if UsdExporter != undefined then (
            try (
                export_filename = exportFilename.text
                local export_script = get_scene_export_utils_script()
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
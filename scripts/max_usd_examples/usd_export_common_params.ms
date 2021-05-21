parameters exportSettings rollout:exportSettingsRollout
(
    exportMeshes type:#boolean ui:exportMeshes default:true
    exportLights type:#boolean ui:exportLights default:true
    exportCameras type:#boolean ui:exportCameras default:true
    exportMaterials type:#boolean ui:exportMaterials default:true
    bakeTextures type:#boolean ui:bakeTextures default:False
    upAxis type:#integer ui:upAxis default:2
    --rootScope type:#string ui:rootScope default:"/"
)
rollout exportSettingsRollout "USD Export Parameters"
(
    checkbox exportMeshes "Export Meshes"
    checkbox exportLights "Export Lights"
    checkbox exportCameras "Export Cameras"
    checkbox exportMaterials "Export Materials"
    checkbox bakeTextures "Bake Textures"
    dropdownList upAxis "UpAxis:" items:#("Y-up", "Z-up")
    --edittext rootScope "RootScope:"
)

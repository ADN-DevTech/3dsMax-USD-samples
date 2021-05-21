
parameters usdProjectParams rollout:usdProjectParamsRollup 
(
	projectName type:#string animatable:false ui:projectName default:""
	projectPath type:#string animatable:false ui:projectPath default:""
    assetsFolder type:#string animatable:false ui:assetsFolder default:"Assets"
)

rollout usdProjectParamsRollup "Project Parameters"
(
    edittext projectName "Project Name:" labelOnTop:True readOnly:True
	edittext projectPath "Project Path:" labelOnTop:True
    button browseButton "Browse..." width:150
	edittext assetsFolder "AssetsFolder:" labelOnTop:True

	on browseButton pressed do 
	(
        local new_proj_path = browse_project_folder currentProjPath:projectPath.text
        if new_proj_path != undefined do (
            projectPath.text = new_proj_path
            local leaf = pathConfig.stripPathToLeaf new_proj_path
            projectName.text = leaf
        )    
	)
)

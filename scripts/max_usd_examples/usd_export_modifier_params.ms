parameters usdExportModifierParams rollout:usdExportModifierRollup 
(
	exportChildren type:#boolean ui:exportChildren default:true
	exportEndResult type:#boolean ui:exportEndResult default:true
)
rollout usdExportModifierRollup "Modifier Parameters"
(
	checkbox exportChildren "Export Node Children"
	checkbox exportEndResult "Export End Result"
)
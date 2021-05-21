###########################################################################
# Copyright (c) 2019 Autodesk, Inc.
# All rights reserved.
#
# These coded instructions, statements, and computer programs contain
# unpublished proprietary information written by Autodesk, Inc., and are
# protected by Federal copyright law. They may not be disclosed to third
# parties or copied or duplicated in any form, in whole or in part, without
# the prior written consent of Autodesk, Inc.
###########################################################################
# DESCRIPTION: Create a symbolic link to your build folder for Max.
# AUTHOR: Autodesk Inc.
###########################################################################

Param(
    [Parameter(Mandatory=$false, HelpMessage="Unlink")]
    [switch]$UNLINK=$false
)

$PRIVATE_COMPONENT_NAME = "max-2022-usd-examples"
$APPLICATION_PLUGINS_DIR = "$env:APPDATA\Autodesk\ApplicationPlugins"
$THIS_APPLICATION_DIR = "$APPLICATION_PLUGINS_DIR\$PRIVATE_COMPONENT_NAME"

if ($UNLINK) {
    (Get-Item $THIS_APPLICATION_DIR).Delete()
    Write-Host "Removed: $THIS_APPLICATION_DIR"
} Else {
    if (!(Test-Path -Path $APPLICATION_PLUGINS_DIR)) { 
        New-Item -ItemType Directory -Path $APPLICATION_PLUGINS_DIR
    }
    New-Item -ItemType SymbolicLink -Path $THIS_APPLICATION_DIR -Target (Resolve-Path -Path ".") -Force
}

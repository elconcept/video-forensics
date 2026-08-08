Windows bootstrap fix

The observed failure resolves scripts/bootstrap_h265nal.py relative to launchers/, producing:
launchers/scripts/bootstrap_h265nal.py

The executor introduces a repository-root path derived from $PSScriptRoot/.., resolves the bootstrap script with Join-Path, verifies that the file exists, invokes it with PowerShell's call operator, and temporarily switches the working directory to the repository root.

# Create conda environment
$condaEnvName = "build_env_neurology"
$condaCreateCmd = "conda create -n $condaEnvName python=3.13 -y"
Invoke-Expression -Command $condaCreateCmd

# Activate conda environment
$activateEnvCmd = "conda activate $condaEnvName"
Invoke-Expression -Command $activateEnvCmd

# Install packages from requirements.txt
$requirementsFile = "requirements.txt"
$installRequirementsCmd = "pip install -r $requirementsFile"
Invoke-Expression -Command $installRequirementsCmd

# Extra packages for building .exe
$requirementsFile = "build_exe_requirements.txt"
$installRequirementsCmd = "pip install -r $requirementsFile"
Invoke-Expression -Command $installRequirementsCmd

# Run pyinstaller with the skimage location
$pyInstallerCmd = @'
pyinstaller --onefile ./main.py
'@

Invoke-Expression -Command $pyInstallerCmd

# Back to previous env
$activateEnvCmd = "conda deactivate"
Invoke-Expression -Command $activateEnvCmd
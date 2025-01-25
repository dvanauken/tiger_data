# Cleanup existing directories
Remove-Item -Path "TigerGeoprocessing.egg-info" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "docs" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "tiger_processed" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "setup.py" -Force -ErrorAction SilentlyContinue

# Create new directory structure
$dirs = @(
    "app/client",
    "app/server",
    "app/server/data"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Path $dir -Force
}

# Move core files to server directory
Move-Item -Path "tiger_processor.py" -Destination "app/server/" -Force
Move-Item -Path "tiger_types.py" -Destination "app/server/" -Force
Move-Item -Path "TigerConfig.py" -Destination "app/server/tiger_config.py" -Force

# Create empty client files
New-Item -ItemType File -Path "app/client/index.html" -Force
New-Item -ItemType File -Path "app/client/style.css" -Force
New-Item -ItemType File -Path "app/client/script.js" -Force

# Create main.py in server directory
New-Item -ItemType File -Path "app/server/main.py" -Force

# List the final structure
Write-Host "`nFinal directory structure:"
Get-ChildItem -Path "." -Recurse | Select-Object FullName
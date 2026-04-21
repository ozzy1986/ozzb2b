# Move legacy WordPress assets into legacy/ using an allowlist.
# Only files/folders NOT in the allowlist are moved.

$ErrorActionPreference = 'Continue'

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    $keep = @(
        '.git',
        '.gitignore',
        '.gitattributes',
        '.editorconfig',
        '.dockerignore',
        'legacy',
        'deploy',
        'apps',
        'proto',
        'infra',
        'packages',
        '.github',
        'compose.dev.yml',
        'compose.prod.yml',
        'package.json',
        'pnpm-workspace.yaml',
        'pnpm-lock.yaml',
        '.nvmrc',
        '.node-version',
        '.python-version'
    )

    New-Item -ItemType Directory -Force -Path 'legacy' | Out-Null

    Get-ChildItem -Force -LiteralPath $root | ForEach-Object {
        $name = $_.Name
        if ($keep -contains $name) { return }
        $src = $_.FullName
        $dest = Join-Path 'legacy' $name
        git mv -- $src $dest 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Move-Item -LiteralPath $src -Destination $dest -Force
        }
        Write-Host "moved -> $dest"
    }
}
finally {
    Pop-Location
}

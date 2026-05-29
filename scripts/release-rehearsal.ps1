param(
  [string]$BaseUrl = "http://127.0.0.1:5173/api",
  [string]$Output = "release-evidence/release-candidate-rehearsal.md",
  [switch]$SkipDocker,
  [switch]$AllowDirty
)

$argsList = @(
  "$PSScriptRoot\release_rehearsal.py",
  "--base-url",
  $BaseUrl,
  "--output",
  $Output
)

if ($SkipDocker) {
  $argsList += "--skip-docker"
}

if ($AllowDirty) {
  $argsList += "--allow-dirty"
}

python @argsList

param(
  [string]$BaseUrl = $env:DEVMEMORY_API_BASE,
  [string]$Username = $env:STUDY_DEFAULT_USERNAME,
  [string]$Password = $env:STUDY_DEFAULT_PASSWORD
)

if (-not $BaseUrl) {
  $BaseUrl = "http://127.0.0.1:8000/api"
}
if (-not $Username) {
  $Username = "admin"
}
if (-not $Password) {
  $Password = "changeme"
}

python "$PSScriptRoot\smoke_test.py" --base-url $BaseUrl --username $Username --password $Password

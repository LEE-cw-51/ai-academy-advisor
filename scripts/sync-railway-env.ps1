# backend/.env -> Railway variables (비밀값은 stdout에 출력하지 않음)
# railway variables set KEY --stdin --service backend --skip-deploys
param(
    [string[]]$CorsOrigins = @("http://localhost:3000")
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$envFile = Join-Path $root "backend\.env"
$keys = @(
    "DATABASE_URL",
    "GROQ_API_KEY",
    "GROQ_BASE_URL",
    "LLM_PROVIDER",
    "LLM_MODEL",
    "EMBEDDING_PROVIDER",
    "VECTOR_STORE",
    "REVIEW_SOURCE",
    "EMBEDDING_MODEL",
    "EMBEDDING_DIM",
    "NAVER_CLIENT_ID",
    "NAVER_CLIENT_SECRET",
    "NAVER_BASE_URL"
)

if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    throw "railway CLI가 없습니다. npm install -g @railway/cli"
}

$vars = @{}
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$' -and $_.Trim() -notmatch '^\s*#') {
        $vars[$Matches[1]] = $Matches[2].Trim().Trim('"').Trim("'")
    }
}

$corsJson = ($CorsOrigins | ConvertTo-Json -Compress)
$vars["CORS_ORIGINS"] = $corsJson

Set-Location $root
foreach ($key in $keys) {
    if (-not $vars.ContainsKey($key)) { continue }
    $val = $vars[$key]
    if ([string]::IsNullOrWhiteSpace($val)) { continue }
    Write-Host "Setting $key"
    $val | railway variables set $key --stdin --service backend --skip-deploys
    if ($LASTEXITCODE -ne 0) {
        throw "railway variables set failed for $key (exit $LASTEXITCODE)"
    }
}
Write-Host "Setting CORS_ORIGINS"
$corsJson | railway variables set CORS_ORIGINS --stdin --service backend --skip-deploys
if ($LASTEXITCODE -ne 0) {
    throw "railway variables set failed for CORS_ORIGINS (exit $LASTEXITCODE)"
}
Write-Host "Railway variables synced."

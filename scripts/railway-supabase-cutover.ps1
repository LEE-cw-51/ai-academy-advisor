# Supabase DATABASE_URL을 Railway backend 서비스에 반영하고 헬스체크한다.
# 사전: railway login 완료, 프로젝트 루트에서 railway link (backend 서비스 선택)
#
# Usage:
#   .\scripts\railway-supabase-cutover.ps1
#   .\scripts\railway-supabase-cutover.ps1 -ApiUrl "https://your-backend.up.railway.app"

param(
    [string]$ApiUrl = "",
    [string]$EnvFile = "backend\.env"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    throw "railway CLI가 없습니다. npm install -g @railway/cli"
}

railway whoami | Out-Null

$envPath = Join-Path $root $EnvFile
if (-not (Test-Path $envPath)) {
    throw "환경 파일 없음: $envPath"
}

$dbLine = Get-Content $envPath | Where-Object { $_ -match '^\s*DATABASE_URL=' } | Select-Object -Last 1
if (-not $dbLine) {
    throw "DATABASE_URL이 $EnvFile에 없습니다."
}
$databaseUrl = ($dbLine -split '=', 2)[1].Trim().Trim('"').Trim("'")
if ($databaseUrl -notmatch '^postgresql') {
    throw "DATABASE_URL이 postgresql URL이 아닙니다."
}

Write-Host "Railway backend 서비스에 DATABASE_URL 설정 중..."
railway variables set "DATABASE_URL=$databaseUrl" --service backend

Write-Host "재배포 트리거 (최신 이미지 재시작)..."
railway redeploy --service backend -y

if (-not $ApiUrl) {
    $ApiUrl = (railway domain --service backend 2>$null | Select-Object -First 1)
    if ($ApiUrl -and $ApiUrl -notmatch '^https?://') {
        $ApiUrl = "https://$ApiUrl"
    }
}

if (-not $ApiUrl) {
    Write-Host "API URL을 자동으로 찾지 못했습니다. Railway 대시보드 도메인을 -ApiUrl로 넘겨 주세요."
    exit 0
}

$ApiUrl = $ApiUrl.TrimEnd('/')
Write-Host "헬스체크: $ApiUrl/health"
Start-Sleep -Seconds 15
for ($i = 1; $i -le 12; $i++) {
    try {
        $health = Invoke-RestMethod -Uri "$ApiUrl/health" -TimeoutSec 10
        Write-Host "health OK:" ($health | ConvertTo-Json -Compress)
        $academies = Invoke-RestMethod -Uri "$ApiUrl/academies?limit=1" -TimeoutSec 15
        $total = $academies.total
        Write-Host "GET /academies total=$total"
        if ($total -ge 411) {
            Write-Host "컷오버 검증 완료."
            exit 0
        }
        Write-Host "경고: academies total이 411 미만입니다. 배포/DB 연결을 확인하세요."
        exit 1
    } catch {
        Write-Host "시도 $i/12 대기 중... $($_.Exception.Message)"
        Start-Sleep -Seconds 10
    }
}
throw "헬스체크 시간 초과: $ApiUrl"

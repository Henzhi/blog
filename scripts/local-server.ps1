# ============================================================
#  本地博客：启动 / 停止 / 状态
#
#  用法（在任意 PowerShell 窗口）：
#     powershell -ExecutionPolicy Bypass -File C:\Code\VibeCoding\blog\scripts\local-server.ps1 start
#     powershell -ExecutionPolicy Bypass -File C:\Code\VibeCoding\blog\scripts\local-server.ps1 stop
#     powershell -ExecutionPolicy Bypass -File C:\Code\VibeCoding\blog\scripts\local-server.ps1 status
#
#  说明：
#   - 以 CREATE_NO_WINDOW 启动，无黑窗口、不随终端关闭而退出
#   - 端口默认 4321，可用 -Port 修改（改了要同步改 astro.config.mjs 的 site）
# ============================================================

param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'status', 'restart')]
    [string]$Action = 'start',

    [int]$Port = 4321
)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot          # scripts/ 的上一级 = 仓库根
$Dist     = Join-Path $RepoRoot 'dist'
$CmdFile  = Join-Path $PSScriptRoot 'serve-hidden.cmd'
$PidFile  = Join-Path $env:TEMP 'blog-local-4321.pid'

function Get-RunningProcess {
    if (-not (Test-Path $PidFile)) { return $null }
    $savedPid = (Get-Content $PidFile -Raw).Trim()
    if (-not $savedPid) { return $null }
    $p = Get-Process -Id $savedPid -ErrorAction SilentlyContinue
    # 进程可能被复用，校验一下名字
    if ($p -and $p.ProcessName -like 'python*') { return $p }
    return $null
}

function Stop-Server {
    $p = Get-RunningProcess
    if ($p) {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 600
        Write-Host "[stop] 已停止本地服务 (PID $($p.Id))"
    }
    else {
        Write-Host "[stop] 没有正在运行的本地服务"
    }
    Remove-Item $PidFile -ErrorAction SilentlyContinue
}

function Start-Server {
    if (-not (Test-Path $Dist)) {
        Write-Host "[error] 找不到 dist 目录：$Dist" -ForegroundColor Red
        Write-Host "        先在仓库根执行：npm run build" -ForegroundColor Yellow
        exit 1
    }
    if (-not (Test-Path (Join-Path $Dist 'index.html'))) {
        Write-Host "[error] dist\index.html 不存在，构建产物不完整" -ForegroundColor Red
        exit 1
    }

    # 已在运行则先停，保证干净
    if (Get-RunningProcess) { Stop-Server }

    # CREATE_NO_WINDOW = 0x08000000，无窗口且不随当前终端退出
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName        = 'cmd.exe'
    $psi.Arguments       = "/c `"$CmdFile`" `"$Dist`" $Port"
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow  = $true
    $psi.WindowStyle     = 'Hidden'

    $proc = [System.Diagnostics.Process]::Start($psi)
    $proc.Id | Out-File -FilePath $PidFile -Encoding ascii -NoNewline
    Write-Host "[start] 已启动本地服务 (PID $($proc.Id))，端口 $Port"

    Start-Sleep -Seconds 2
}

function Show-Status {
    $p = Get-RunningProcess
    if ($p) {
        Write-Host "[status] 运行中：http://localhost:$Port  (PID $($p.Id))"
    }
    else {
        Write-Host "[status] 未运行"
    }
}

function Test-Routes {
    Write-Host ''
    Write-Host '健康检查：'
    $routes = @('/', '/about/', '/archive/', '/projects/', '/posts/', '/rss.xml', '/pagefind/pagefind.js')
    $ok = 0
    foreach ($r in $routes) {
        $url = "http://localhost:$Port$r"
        try {
            $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 6
            $code = $resp.StatusCode
        }
        catch {
            $code = 'ERR'
        }
        if ($code -eq 200) { $ok++ }
        Write-Host ("   {0,-6} {1}" -f $code, $r)
    }
    Write-Host ''
    if ($ok -eq $routes.Count) {
        Write-Host "[ok] 全部 $ok 条路由正常" -ForegroundColor Green
        Write-Host "     打开：http://localhost:$Port" -ForegroundColor Cyan
    }
    else {
        Write-Host "[warn] $ok/$($routes.Count) 条路由正常" -ForegroundColor Yellow
    }
}

switch ($Action) {
    'start' { Start-Server; Test-Routes }
    'stop' { Stop-Server }
    'status' { Show-Status }
    'restart' { Stop-Server; Start-Server; Test-Routes }
}

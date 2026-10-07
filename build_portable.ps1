<#
.SYNOPSIS
    Rebuild "앨범 만들기.exe" and app\ at the repo root: the stand-alone program users double-click.

.DESCRIPTION
    Run this after changing the code, then commit "앨범 만들기.exe" and app\ together.
    Users who download the repository only need to unzip it and double-click the exe:
    no Python, no installation, no internet.

    1. Recreate .build-venv with requirements-build.txt only (no stray packages).
    2. Build with PyInstaller (onedir, no console window). The runtime goes to app\
       next to the exe (--contents-directory app).
    3. Smoke test: copy the result to a Korean/space path, hide Python from PATH,
       and make a real album (JPEG + HEIC + GIF). Stop here if it fails.
    4. Replace "앨범 만들기.exe" and app\ at the repo root.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File build_portable.ps1
    powershell -ExecutionPolicy Bypass -File build_portable.ps1 -Python C:\Python314\python.exe
#>
param([string]$Python)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$AppName = '앨범 만들기'
$Venv = Join-Path $PSScriptRoot '.build-venv'
$VenvPy = Join-Path $Venv 'Scripts\python.exe'
$BuildOut = Join-Path $PSScriptRoot "build\dist\$AppName"
$ExeName = "$AppName.exe"

function Step($message) { Write-Host "`n== $message" -ForegroundColor Cyan }

function Invoke-Checked {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "실패: $Exe $($Arguments -join ' ') (exit $LASTEXITCODE)" }
}

try {
    Step '1/4 빌드용 가상환경 만들기 (.build-venv)'
    if (Test-Path $Venv) { Remove-Item -Recurse -Force $Venv }
    if ($Python) {
        Invoke-Checked $Python @('-m', 'venv', $Venv)
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        Invoke-Checked 'py' @('-3', '-m', 'venv', $Venv)
    } else {
        Invoke-Checked 'python' @('-m', 'venv', $Venv)
    }
    Invoke-Checked $VenvPy @('-m', 'pip', 'install', '--quiet', '--disable-pip-version-check', '-r', 'requirements-build.txt')

    Step "2/4 $ExeName 빌드 (PyInstaller)"
    Invoke-Checked $VenvPy @('-m', 'PyInstaller', '--noconfirm', '--clean', '--log-level', 'WARN',
        '--windowed', '--onedir', '--name', $AppName, '--contents-directory', 'app',
        '--distpath', 'build\dist', '--workpath', 'build\work', '--specpath', 'build',
        '--paths', (Join-Path $PSScriptRoot 'scripts'), (Join-Path $PSScriptRoot 'scripts\album_app.py'))

    Step '3/4 동작 확인 (Python 없이, 한글·공백 경로에서 JPEG+HEIC+GIF로 앨범 만들기)'
    $Work = Join-Path $env:TEMP "a4lbum 검사 $(Get-Random)"
    $AppCopy = Join-Path $Work '앨범 프로그램'
    $Photos = Join-Path $Work '사진 모음'
    $Pdf = Join-Path $Work '결과 앨범.pdf'
    $Log = Join-Path $Work 'log.txt'
    New-Item -ItemType Directory -Force $AppCopy | Out-Null
    Copy-Item -Recurse "$BuildOut\*" $AppCopy
    Invoke-Checked $VenvPy @('packaging\build_helpers.py', 'samples', $Photos)

    $SavedPath = $env:PATH
    $env:PATH = ($env:PATH -split ';' | Where-Object { $_ -and -not [IO.File]::Exists("$_\python.exe") }) -join ';'
    try {
        $proc = Start-Process -FilePath (Join-Path $AppCopy $ExeName) -Wait -PassThru `
            -ArgumentList @('--smoke-test', "`"$Photos`"", "`"$Pdf`"", "`"$Log`"")
    } finally {
        $env:PATH = $SavedPath
    }
    $logText = if (Test-Path $Log) { Get-Content $Log -Raw -Encoding UTF8 } else { '(로그 없음)' }
    if ($proc.ExitCode -ne 0 -or -not (Test-Path $Pdf) -or $logText -notmatch '완료: 사진 3장 → 2페이지') {
        Write-Host $logText
        throw "동작 확인 실패 (exit $($proc.ExitCode)). 저장소의 exe는 바꾸지 않았습니다. 확인 폴더: $Work"
    }
    Write-Host $logText.Trim()
    Remove-Item -Recurse -Force $Work

    Step "4/4 저장소 최상위의 $ExeName 과 app\ 교체"
    $RootApp = Join-Path $PSScriptRoot 'app'
    if (Test-Path $RootApp) { Remove-Item -Recurse -Force $RootApp }
    Copy-Item -Recurse (Join-Path $BuildOut 'app') $RootApp
    Copy-Item -Force (Join-Path $BuildOut $ExeName) (Join-Path $PSScriptRoot $ExeName)
    $mb = '{0:N1}' -f ((Get-ChildItem $RootApp -Recurse -File | Measure-Object Length -Sum).Sum / 1MB)
    Write-Host "`n완료: $ExeName + app\ ($mb MB). 둘을 함께 커밋하세요." -ForegroundColor Green
    exit 0
} catch {
    Write-Host "`n오류: $_" -ForegroundColor Red
    exit 1
}

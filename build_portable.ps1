<#
.SYNOPSIS
    Rebuild "앨범 만들기 (한국어).exe", "Photo Album Maker (English).exe" and app\ at the
    repo root: the stand-alone program users double-click.

.DESCRIPTION
    Run this after changing the code, then commit both exes and app\ together.
    Users who download the repository only need to unzip it and double-click an exe:
    no Python, no installation, no internet.

    The two exes are byte-for-byte copies of one build sharing one app\ folder;
    album_app.py switches to English when its exe name contains "(English)", and
    shows the exe name without ".exe" as the window title.

    1. Recreate .build-venv with requirements-build.txt only (no stray packages).
    2. Build with PyInstaller (onedir, no console window). The runtime goes to app\
       next to the exe (--contents-directory app). The exe gets packaging\app.ico (a photo with
       a note label), and the window reads the same icon back from the exe.
       Copy the exe to the Korean and the English name.
    3. Smoke test both exes: copy the result to a Korean/space path, hide Python
       from PATH, and make a real album (JPEG + HEIC + GIF). Stop here if it fails.
    4. Replace both exes and app\ at the repo root (and remove the old single
       "앨범 만들기.exe" if it is still there).
    5. Remake examples\photos_album.pdf with the new Korean exe (make_example.ps1).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File build_portable.ps1
    powershell -ExecutionPolicy Bypass -File build_portable.ps1 -Python C:\Python314\python.exe
#>
param([string]$Python)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

# Window titles in album_app.title() must match these names (tests/test_english.py checks).
$KoName = '앨범 만들기 (한국어)'
$EnName = 'Photo Album Maker (English)'
$Exes = @(
    @{ Name = "$KoName.exe"; Expect = '완료: 사진 3장 → 2페이지' },
    @{ Name = "$EnName.exe"; Expect = 'Done: 3 photos → 2 pages' }
)
$OldExes = @('앨범 만들기.exe')  # earlier single-language name
$BuildName = 'a4lbum'  # PyInstaller's own output name; users never see it
$Venv = Join-Path $PSScriptRoot '.build-venv'
$VenvPy = Join-Path $Venv 'Scripts\python.exe'
$BuildOut = Join-Path $PSScriptRoot "build\dist\$BuildName"

function Step($message) { Write-Host "`n== $message" -ForegroundColor Cyan }

function Invoke-Checked {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "실패: $Exe $($Arguments -join ' ') (exit $LASTEXITCODE)" }
}

try {
    # A running exe locks app\ and step 4 would fail halfway, leaving app\ half deleted.
    $running = Get-Process | Where-Object { $_.Path -and $_.Path.StartsWith("$PSScriptRoot\") -and $_.Path.EndsWith('.exe') }
    if ($running) {
        throw "실행 중인 앨범 프로그램을 먼저 닫아 주세요: $(($running | ForEach-Object { Split-Path $_.Path -Leaf }) -join ', ')"
    }

    Step '1/5 빌드용 가상환경 만들기 (.build-venv)'
    if (Test-Path $Venv) { Remove-Item -Recurse -Force $Venv }
    if ($Python) {
        Invoke-Checked $Python @('-m', 'venv', $Venv)
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        Invoke-Checked 'py' @('-3', '-m', 'venv', $Venv)
    } else {
        Invoke-Checked 'python' @('-m', 'venv', $Venv)
    }
    Invoke-Checked $VenvPy @('-m', 'pip', 'install', '--quiet', '--disable-pip-version-check', '-r', 'requirements-build.txt')

    Step "2/5 빌드 (PyInstaller) → $KoName.exe, $EnName.exe"
    Invoke-Checked $VenvPy @('-m', 'PyInstaller', '--noconfirm', '--clean', '--log-level', 'WARN',
        '--windowed', '--onedir', '--name', $BuildName, '--contents-directory', 'app',
        '--icon', (Join-Path $PSScriptRoot 'packaging\app.ico'),
        '--distpath', 'build\dist', '--workpath', 'build\work', '--specpath', 'build',
        '--paths', (Join-Path $PSScriptRoot 'scripts'), (Join-Path $PSScriptRoot 'scripts\album_app.py'))
    $BuiltExe = Join-Path $BuildOut "$BuildName.exe"
    foreach ($exe in $Exes) { Copy-Item -Force $BuiltExe (Join-Path $BuildOut $exe.Name) }
    Remove-Item $BuiltExe

    Step '3/5 동작 확인 (exe 2개 각각, Python 없이, 한글·공백 경로에서 JPEG+HEIC+GIF로 앨범 만들기)'
    $Work = Join-Path $env:TEMP "a4lbum 검사 $(Get-Random)"
    $AppCopy = Join-Path $Work '앨범 프로그램'
    $Photos = Join-Path $Work '사진 모음'
    New-Item -ItemType Directory -Force $AppCopy | Out-Null
    Copy-Item -Recurse "$BuildOut\*" $AppCopy
    Invoke-Checked $VenvPy @('packaging\build_helpers.py', 'samples', $Photos)

    $SavedPath = $env:PATH
    $env:PATH = ($env:PATH -split ';' | Where-Object { $_ -and -not [IO.File]::Exists("$_\python.exe") }) -join ';'
    try {
        foreach ($exe in $Exes) {
            $Pdf = Join-Path $Work "결과 앨범 $($exe.Name).pdf"
            $Log = Join-Path $Work "log $($exe.Name).txt"
            $proc = Start-Process -FilePath (Join-Path $AppCopy $exe.Name) -Wait -PassThru `
                -ArgumentList @('--smoke-test', "`"$Photos`"", "`"$Pdf`"", "`"$Log`"")
            $logText = if (Test-Path $Log) { Get-Content $Log -Raw -Encoding UTF8 } else { '(로그 없음)' }
            if ($proc.ExitCode -ne 0 -or -not (Test-Path $Pdf) -or -not $logText.Contains($exe.Expect)) {
                Write-Host $logText
                throw "$($exe.Name) 동작 확인 실패 (exit $($proc.ExitCode)). 저장소의 exe는 바꾸지 않았습니다. 확인 폴더: $Work"
            }
            Write-Host "[$($exe.Name)]"
            Write-Host $logText.Trim()
        }
    } finally {
        $env:PATH = $SavedPath
    }
    Remove-Item -Recurse -Force $Work

    Step '4/5 저장소 최상위의 exe 2개와 app\ 교체'
    $RootApp = Join-Path $PSScriptRoot 'app'
    if (Test-Path $RootApp) { Remove-Item -Recurse -Force $RootApp }
    Copy-Item -Recurse (Join-Path $BuildOut 'app') $RootApp
    foreach ($old in $OldExes) {
        $oldPath = Join-Path $PSScriptRoot $old
        if (Test-Path $oldPath) { Remove-Item -Force $oldPath }
    }
    foreach ($exe in $Exes) { Copy-Item -Force (Join-Path $BuildOut $exe.Name) (Join-Path $PSScriptRoot $exe.Name) }
    $mb = '{0:N1}' -f ((Get-ChildItem $RootApp -Recurse -File | Measure-Object Length -Sum).Sum / 1MB)

    Step '5/5 예시 PDF 다시 만들기 (examples\photos_album.pdf)'
    & (Join-Path $PSScriptRoot 'make_example.ps1') -Exe (Join-Path $PSScriptRoot "$KoName.exe")
    if ($LASTEXITCODE -ne 0) { throw '예시 PDF를 만들지 못했습니다. exe와 app\은 이미 교체되었습니다.' }

    Write-Host "`n완료: $KoName.exe + $EnName.exe + app\ ($mb MB) + 예시 PDF. 함께 커밋하세요." -ForegroundColor Green
    exit 0
} catch {
    Write-Host "`n오류: $_" -ForegroundColor Red
    exit 1
}

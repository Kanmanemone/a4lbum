<#
.SYNOPSIS
    Remake examples\photos_album.pdf from examples\photos\ with the built Korean exe.

.DESCRIPTION
    build_portable.ps1 runs this after replacing the exes, so the example PDF in the
    repository always comes from the current program. It can also be run on its own.

    The exe's --smoke-test mode makes the album without a window, with the CLI
    defaults: name order and a leading "숫자_" dropped from the captions.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File make_example.ps1
#>
param([string]$Exe = (Join-Path $PSScriptRoot '앨범 만들기 (한국어).exe'))

$ErrorActionPreference = 'Stop'

$Photos = Join-Path $PSScriptRoot 'examples\photos'
$Pdf = Join-Path $PSScriptRoot 'examples\photos_album.pdf'
$Log = Join-Path $env:TEMP "a4lbum example $(Get-Random).txt"

try {
    if (-not (Test-Path $Exe)) { throw "exe가 없습니다: $Exe (먼저 build_portable.ps1로 빌드하세요)" }
    $proc = Start-Process -FilePath $Exe -Wait -PassThru `
        -ArgumentList @('--smoke-test', "`"$Photos`"", "`"$Pdf`"", "`"$Log`"")
    $logText = if (Test-Path $Log) { Get-Content $Log -Raw -Encoding UTF8 } else { '(로그 없음)' }
    Write-Host $logText.Trim()
    if ($proc.ExitCode -ne 0) { throw "예시 PDF를 만들지 못했습니다 (exit $($proc.ExitCode))." }
    Write-Host "`n완료: examples\photos_album.pdf" -ForegroundColor Green
    exit 0
} catch {
    Write-Host "`n오류: $_" -ForegroundColor Red
    exit 1
} finally {
    if (Test-Path $Log) { Remove-Item -Force $Log }
}

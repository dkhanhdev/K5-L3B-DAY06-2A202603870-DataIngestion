$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$PgBin = Join-Path $ProjectRoot '.runtime/postgres/Library/bin'
$PgData = Join-Path $ProjectRoot '.runtime/pgdata'
if (-not (Test-Path -LiteralPath (Join-Path $PgBin 'pg_ctl.exe'))) {
    throw 'PostgreSQL runtime missing. Follow docs/PIPELINE.md or use Docker Compose.'
}
$env:PATH = $PgBin + ';' + $env:PATH
if (-not (Test-Path -LiteralPath (Join-Path $PgData 'PG_VERSION'))) {
    & (Join-Path $PgBin 'initdb.exe') -D $PgData -U day6 -A trust -E UTF8 --locale=C
    if ($LASTEXITCODE -ne 0) { throw 'initdb failed' }
}
& (Join-Path $PgBin 'pg_ctl.exe') -D $PgData status
if ($LASTEXITCODE -ne 0) {
    & (Join-Path $PgBin 'pg_ctl.exe') -D $PgData -l (Join-Path $ProjectRoot '.runtime/postgres.log') -o '-h 127.0.0.1 -p 55433' -w start
    if ($LASTEXITCODE -ne 0) { throw 'pg_ctl start failed' }
}
$Exists = & (Join-Path $PgBin 'psql.exe') -h 127.0.0.1 -p 55433 -U day6 -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='day6_lab'"
if ($LASTEXITCODE -ne 0) { throw 'Database connection failed' }
if ($Exists -ne '1') {
    & (Join-Path $PgBin 'createdb.exe') -h 127.0.0.1 -p 55433 -U day6 day6_lab
    if ($LASTEXITCODE -ne 0) { throw 'createdb failed' }
}
Write-Output 'Local lab database ready on 127.0.0.1:55433'

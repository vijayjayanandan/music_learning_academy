# Generate self-signed SSL certificates for local/dev use.
# For production, use Let's Encrypt or a real CA.

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SslDir = Join-Path $ScriptDir "ssl"

if (-not (Test-Path $SslDir)) {
    New-Item -ItemType Directory -Path $SslDir | Out-Null
}

openssl req -x509 -nodes -days 365 `
    -newkey rsa:2048 `
    -keyout "$SslDir\key.pem" `
    -out "$SslDir\cert.pem" `
    -subj "/C=US/ST=Local/L=Dev/O=MusicAcademy/CN=localhost"

Write-Host "SSL certificates generated in $SslDir\"
Write-Host "  - cert.pem (certificate)"
Write-Host "  - key.pem  (private key)"

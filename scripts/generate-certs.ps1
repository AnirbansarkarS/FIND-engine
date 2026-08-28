# PowerShell script to generate TLS certificates for search.yourdomain
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CertsDir = Join-Path $ScriptDir "..\nginx\certs"

if (-not (Test-Path $CertsDir)) {
    New-Item -ItemType Directory -Path $CertsDir | Out-Null
}

$KeyPath = Join-Path $CertsDir "search.yourdomain.key"
$CrtPath = Join-Path $CertsDir "search.yourdomain.crt"

Write-Host "Generating private TLS certificates for search.yourdomain..." -ForegroundColor Green

if (Get-Command openssl -ErrorAction SilentlyContinue) {
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
      -keyout $KeyPath `
      -out $CrtPath `
      -subj "/C=US/ST=Private/L=HomeServer/O=PrivateInfra/OU=Search/CN=search.yourdomain" `
      -addext "subjectAltName=DNS:search.yourdomain,DNS:localhost,IP:127.0.0.1"
    Write-Host "OpenSSL Certificate created successfully in $CertsDir" -ForegroundColor Green
} else {
    Write-Host "OpenSSL not detected. Creating Windows Self-Signed Certificate..." -ForegroundColor Yellow
    $cert = New-SelfSignedCertificate -DnsName "search.yourdomain", "localhost" -CertStoreLocation "cert:\CurrentUser\My"
    Write-Host "Self-signed certificate created in Windows Cert Store: $($cert.Thumbprint)" -ForegroundColor Green
}

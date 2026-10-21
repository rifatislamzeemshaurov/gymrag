# Dot-sourced by deploy.ps1 / destroy.ps1 from the project root.
# Loads .env and exposes its values to the AWS CLI, Docker and Terraform.

$EnvFile = ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Host ".env not found - copy .env.example to .env and fill in the values." -ForegroundColor Red
    exit 1
}

function Read-EnvValue {
    param([string]$Name, [string]$File = $EnvFile)
    $line = Get-Content $File | Where-Object { $_ -match "^$Name=" } | Select-Object -First 1
    if (-not $line) { return $null }
    return ($line -split '=', 2)[1].Trim()
}

# Writes KEY=value into .env (replacing the existing line, or appending).
function Set-EnvValue {
    param([string]$Name, [string]$Value, [string]$File = $EnvFile)
    $found = $false
    $lines = @(Get-Content $File | ForEach-Object {
        if ($_ -match "^$Name=") { $found = $true; "$Name=$Value" } else { $_ }
    })
    if (-not $found) { $lines += "$Name=$Value" }
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllLines((Resolve-Path $File), [string[]]$lines, $utf8NoBom)
}

# --- AWS credentials + region ----------------------------------------------
# Exported as the standard AWS_* variables, which the AWS CLI and Terraform's
# AWS provider both read. Left unset when empty so an "aws configure" profile
# still works as a fallback.
foreach ($name in "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY") {
    $value = Read-EnvValue -Name $name
    if (-not [string]::IsNullOrWhiteSpace($value)) {
        Set-Item -Path "Env:$name" -Value $value
    }
}
$awsRegion = Read-EnvValue -Name "AWS_REGION"
if (-not [string]::IsNullOrWhiteSpace($awsRegion)) {
    $env:AWS_REGION = $awsRegion
    $env:AWS_DEFAULT_REGION = $awsRegion
}

# --- Terraform variables -----------------------------------------------------
# Terraform auto-reads any TF_VAR_<name> environment variable as the value for
# variable <name>. Anything left empty in .env falls back to the default in
# terraform/variables.tf.
$tfVars = [ordered]@{
    USE_CUSTOM_DOMAIN = "use_custom_domain"
    DOMAIN_NAME       = "domain_name"
    APP_SUBDOMAIN     = "app_subdomain"
    OPENAI_MODEL      = "openai_model"
    CONTAINER_CPU     = "container_cpu"
    CONTAINER_MEMORY  = "container_memory"
    DESIRED_COUNT     = "desired_count"
}
foreach ($name in $tfVars.Keys) {
    $value = Read-EnvValue -Name $name
    if (-not [string]::IsNullOrWhiteSpace($value)) {
        Set-Item -Path "Env:TF_VAR_$($tfVars[$name])" -Value $value
    } elseif ($name -eq "APP_SUBDOMAIN" -and $null -ne $value) {
        # An explicitly empty APP_SUBDOMAIN means "serve on the apex domain".
        # PowerShell 5.1 deletes an env var set to "", so a single space is
        # passed instead; Terraform trims it.
        $env:TF_VAR_app_subdomain = " "
    }
}

# --- Pre-flight: credentials must work and target the expected account -------
$actualAccountId = aws sts get-caller-identity --query Account --output text
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "AWS credentials were rejected - check AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY in .env." -ForegroundColor Red
    exit 1
}
$expectedAccountId = Read-EnvValue -Name "AWS_ACCOUNT_ID"
if (-not [string]::IsNullOrWhiteSpace($expectedAccountId) -and $actualAccountId -ne $expectedAccountId) {
    Write-Host ""
    Write-Host "AWS account mismatch: credentials belong to $actualAccountId but .env sets AWS_ACCOUNT_ID=$expectedAccountId." -ForegroundColor Red
    exit 1
}

# --- Custom domain (one command) ---------------------------------------------
# Set-CustomDomain gym.example.com -> finds the Route 53 hosted zone that owns
# the name (works for an apex like example.com too), saves the choice to .env
# so every later deploy keeps it, and sets the Terraform variables.
# Set-CustomDomain none            -> detaches it again.
function Set-CustomDomain {
    param([string]$Domain)
    $name = $Domain.ToLower().Trim() -replace '^https?://', '' -replace '/.*$', '' -replace '\.$', ''
    if ($name -eq "none") {
        Set-EnvValue -Name "USE_CUSTOM_DOMAIN" -Value "false"
        $env:TF_VAR_use_custom_domain = "false"
        Write-Host "Custom domain detached - the app will be served on its CloudFront domain." -ForegroundColor Yellow
        return
    }
    $zones = aws route53 list-hosted-zones --query 'HostedZones[?Config.PrivateZone==`false`].Name' --output text
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Could not list Route 53 hosted zones." -ForegroundColor Red
        exit 1
    }
    $zone = ""
    foreach ($z in ("$zones" -split '\s+')) {
        $z = $z.TrimEnd('.')
        if ($z -and ($name -eq $z -or $name.EndsWith(".$z")) -and $z.Length -gt $zone.Length) { $zone = $z }
    }
    if (-not $zone) {
        Write-Host "No public Route 53 hosted zone found for $name in this AWS account." -ForegroundColor Red
        Write-Host "Create the hosted zone first (see DEPLOYMENT.md, section 6), then re-run." -ForegroundColor Yellow
        exit 1
    }
    $sub = if ($name -eq $zone) { "" } else { $name.Substring(0, $name.Length - $zone.Length - 1) }
    Set-EnvValue -Name "USE_CUSTOM_DOMAIN" -Value "true"
    Set-EnvValue -Name "DOMAIN_NAME" -Value $zone
    Set-EnvValue -Name "APP_SUBDOMAIN" -Value $sub
    $env:TF_VAR_use_custom_domain = "true"
    $env:TF_VAR_domain_name = $zone
    $env:TF_VAR_app_subdomain = if ($sub) { $sub } else { " " }
    Write-Host "Custom domain: https://$name (hosted zone $zone) - saved to .env" -ForegroundColor Cyan
}

#!/bin/bash
# Sourced by deploy.sh / destroy.sh from the project root.
# Loads .env and exposes its values to the AWS CLI, Docker and Terraform.

ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
  echo ".env not found - copy .env.example to .env and fill in the values."
  exit 1
fi

read_env_value() {
  grep -m1 "^$1=" "$ENV_FILE" | cut -d '=' -f2- | tr -d '\r'
}

# Writes KEY=value into .env (replacing the existing line, or appending).
set_env_value() {
  if grep -q "^$1=" "$ENV_FILE"; then
    local tmp
    tmp=$(mktemp)
    awk -v k="$1" -v v="$2" 'BEGIN { FS = OFS = "=" } $1 == k { print k "=" v; next } { print }' "$ENV_FILE" > "$tmp" && cat "$tmp" > "$ENV_FILE" && rm -f "$tmp"
  else
    printf '%s=%s\n' "$1" "$2" >> "$ENV_FILE"
  fi
}

# --- AWS credentials + region ----------------------------------------------
# Exported as the standard AWS_* variables, which the AWS CLI and Terraform's
# AWS provider both read. Left unset when empty so an "aws configure" profile
# still works as a fallback.
for name in AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY; do
  value=$(read_env_value "$name")
  if [ -n "$value" ]; then
    export "$name=$value"
  fi
done
ENV_AWS_REGION=$(read_env_value AWS_REGION)
if [ -n "$ENV_AWS_REGION" ]; then
  export AWS_REGION="$ENV_AWS_REGION"
  export AWS_DEFAULT_REGION="$ENV_AWS_REGION"
fi

# --- Terraform variables -----------------------------------------------------
# Terraform auto-reads any TF_VAR_<name> environment variable as the value for
# variable <name>. Anything left empty in .env falls back to the default in
# terraform/variables.tf.
for pair in \
  USE_CUSTOM_DOMAIN:use_custom_domain \
  DOMAIN_NAME:domain_name \
  APP_SUBDOMAIN:app_subdomain \
  OPENAI_MODEL:openai_model \
  CONTAINER_CPU:container_cpu \
  CONTAINER_MEMORY:container_memory \
  DESIRED_COUNT:desired_count; do
  key=${pair%%:*}
  value=$(read_env_value "$key")
  # An explicitly empty APP_SUBDOMAIN means "serve on the apex domain".
  if [ -n "$value" ] || { [ "$key" = "APP_SUBDOMAIN" ] && grep -q "^APP_SUBDOMAIN=" "$ENV_FILE"; }; then
    export "TF_VAR_${pair##*:}=$value"
  fi
done

# --- Pre-flight: credentials must work and target the expected account -------
if ! ACTUAL_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text); then
  echo ""
  echo "AWS credentials were rejected - check AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY in .env."
  exit 1
fi
ACTUAL_ACCOUNT_ID=$(echo "$ACTUAL_ACCOUNT_ID" | tr -d '\r')
EXPECTED_ACCOUNT_ID=$(read_env_value AWS_ACCOUNT_ID)
if [ -n "$EXPECTED_ACCOUNT_ID" ] && [ "$ACTUAL_ACCOUNT_ID" != "$EXPECTED_ACCOUNT_ID" ]; then
  echo ""
  echo "AWS account mismatch: credentials belong to $ACTUAL_ACCOUNT_ID but .env sets AWS_ACCOUNT_ID=$EXPECTED_ACCOUNT_ID."
  exit 1
fi

# --- Custom domain (one command) ---------------------------------------------
# attach_custom_domain gym.example.com  -> finds the Route 53 hosted zone that
# owns the name (works for an apex like example.com too), saves the choice to
# .env so every later deploy keeps it, and exports the Terraform variables.
# attach_custom_domain none             -> detaches it again.
attach_custom_domain() {
  local domain zone="" z zones sub=""
  domain=$(echo "$1" | tr '[:upper:]' '[:lower:]' | sed -e 's#^https\{0,1\}://##' -e 's#/.*$##' -e 's#\.$##')
  if [ "$domain" = "none" ]; then
    set_env_value USE_CUSTOM_DOMAIN false
    export TF_VAR_use_custom_domain=false
    echo "Custom domain detached - the app will be served on its CloudFront domain."
    return 0
  fi
  zones=$(aws route53 list-hosted-zones --query 'HostedZones[?Config.PrivateZone==`false`].Name' --output text | tr -d '\r')
  for z in $zones; do
    z=${z%.}
    if [ "$domain" = "$z" ] || [[ "$domain" == *".$z" ]]; then
      if [ ${#z} -gt ${#zone} ]; then zone=$z; fi
    fi
  done
  if [ -z "$zone" ]; then
    echo "No public Route 53 hosted zone found for $domain in this AWS account."
    echo "Create the hosted zone first (see DEPLOYMENT.md, section 6), then re-run."
    exit 1
  fi
  if [ "$domain" != "$zone" ]; then sub=${domain%."$zone"}; fi
  set_env_value USE_CUSTOM_DOMAIN true
  set_env_value DOMAIN_NAME "$zone"
  set_env_value APP_SUBDOMAIN "$sub"
  export TF_VAR_use_custom_domain=true TF_VAR_domain_name="$zone" TF_VAR_app_subdomain="$sub"
  echo "Custom domain: https://$domain (hosted zone $zone) - saved to .env"
}

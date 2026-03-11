#!/bin/sh
#
# Loops in assets/controlled-vocabularies to create datapackage.yaml
#
: "${1:?Usage: $0 <asset_name>}"

ASSET_NAME="$1"

/usr/local/bin/schema_gov_it_tools.bin datapackage create \
    --ttl "${ASSET_NAME}.ttl" \
    --frame "${ASSET_NAME}.frame.yamlld" \
    --vocabulary-uri "changeme" \
    --output "datapackage.yaml" \
    --lang it \
    --force

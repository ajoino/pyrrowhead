#!/bin/bash

# Created by Emanuel Palm (https://github.com/emanuelpalm)

cd "$(dirname "$0")" || exit
source "lib_certs.sh"
cd ..

# ROOT

create_root_keystore \
  "cloud-root/crypto/root.p12" "arrowhead.eu"

# CONSUMER CLOUD

create_cloud_keystore \
  "cloud-root/crypto/root.p12" "arrowhead.eu" \
  "cloud-{{ cloud_name }}/crypto/{{ cloud_name }}.p12" "{{ cloud_name }}.{{ company_name }}.arrowhead.eu"

create_consumer_system_keystore() {
  SYSTEM_NAME=$1
  SYSTEM_SANS=$2

  create_system_keystore \
    "cloud-root/crypto/root.p12" "arrowhead.eu" \
    "cloud-{{ cloud_name }}/crypto/{{ cloud_name }}.p12" "{{ cloud_name }}.{{ company_name }}.arrowhead.eu" \
    "cloud-{{ cloud_name }}/crypto/${SYSTEM_NAME}.p12" "${SYSTEM_NAME}.{{ cloud_name }}.{{ company_name }}.arrowhead.eu" \
    "${SYSTEM_SANS}"
}

{% if client_systems != None %}
{% for system, config in client_systems.items() %}
create_consumer_system_keystore "{{ system }}" "ip:{{ config['address'] }}"
{% endfor %}
{% endif %}
{% for system, config in core_systems.items() %}
create_consumer_system_keystore "{{ system }}" "ip:{{ config['address'] }}"
{% endfor %}

create_sysop_keystore \
  "cloud-root/crypto/root.p12" "arrowhead.eu" \
  "cloud-{{ cloud_name }}/crypto/{{ cloud_name }}.p12" "{{ cloud_name }}.{{ company_name }}.arrowhead.eu" \
  "cloud-{{ cloud_name }}/crypto/sysop.p12" "sysop.{{ cloud_name }}.{{ company_name }}.arrowhead.eu"

create_truststore \
  "cloud-{{ cloud_name }}/crypto/truststore.p12" \
  "cloud-{{ cloud_name }}/crypto/{{ cloud_name }}.crt" "{{ cloud_name }}.{{ company_name }}.arrowhead.eu" \

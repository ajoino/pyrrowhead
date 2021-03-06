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
  "cloud-data-consumer/crypto/conet-demo-consumer.p12" "conet-demo-consumer.ltu.arrowhead.eu"

create_consumer_system_keystore() {
  SYSTEM_NAME=$1

  create_system_keystore \
    "cloud-root/crypto/root.p12" "arrowhead.eu" \
    "cloud-data-consumer/crypto/conet-demo-consumer.p12" "conet-demo-consumer.ltu.arrowhead.eu" \
    "cloud-data-consumer/crypto/${SYSTEM_NAME}.p12" "${SYSTEM_NAME}.conet-demo-consumer.ltu.arrowhead.eu" \
    "dns:core.consumer,ip:172.23.2.13,dns:localhost,ip:127.0.0.1"
}

create_consumer_system_keystore "authorization"
create_consumer_system_keystore "contract_proxy"
create_consumer_system_keystore "data_consumer"
create_consumer_system_keystore "event_handler"
create_consumer_system_keystore "datamanager"
create_consumer_system_keystore "gatekeeper"
create_consumer_system_keystore "gateway"
create_consumer_system_keystore "orchestrator"
create_consumer_system_keystore "service_registry"

create_sysop_keystore \
  "cloud-root/crypto/root.p12" "arrowhead.eu" \
  "cloud-data-consumer/crypto/conet-demo-consumer.p12" "conet-demo-consumer.ltu.arrowhead.eu" \
  "cloud-data-consumer/crypto/sysop.p12" "sysop.conet-demo-consumer.ltu.arrowhead.eu"

create_truststore \
  "cloud-data-consumer/crypto/truststore.p12" \
  "cloud-data-consumer/crypto/conet-demo-consumer.crt" "conet-demo-consumer.ltu.arrowhead.eu" \
  "cloud-relay/crypto/conet-demo-relay.crt" "conet-demo-relay.ltu.arrowhead.eu"

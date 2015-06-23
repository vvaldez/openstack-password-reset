#!/bin/bash

INSTANCE=$1

. /root/keystonerc_demo

if [[ "${INSTANCE}" == "rhel" ]]
then
	FLAVOR=m1.small
	IMAGE=$(nova image-list | awk '/rhel/ { print $4 }')
elif [[ "${INSTANCE}" == "windows" ]]
then
	FLAVOR=m1.medium
	IMAGE=$(nova image-list | awk '/windows/ { print $4 }')
elif [[ -z "${INSTANCE}" ]]
then
  echo "ERROR: Must specify which demo to perform: 'rhel|windows'"
  exit 1
else
	echo "ERROR: Demo name '${INSTANCE}' not supported for this demo."
	exit 1
fi

trap ctrl_c INT

cleanup() {
	nova delete ${INSTANCE}
	return $?

}

ctrl_c() {
	echo -e "\nCaught CTRL+C, cleaning up"
	cleanup
	exit $?
}

wait_for_instances() {
  echo -en "\nWaiting for ${INSTANCE} instance(s) to build "
	while [[ $(nova list | grep BUILD) ]]
        do
                echo -n "."
                sleep 2
        done
        echo ""
}
cmd() {
  if [ ! -z "$1" ]  
  then
    CMD_TEXT=$1
    CMD_TO_RUN=$2
  fi
  echo ""
  echo "Press ENTER to initiate '${CMD_TEXT}'"
  read
  echo "INFO: Starting command: '${CMD_TO_RUN}'"
  ${CMD_TO_RUN}
  echo "INFO: Finished with '${CMD_TEXT}'"
}

TIMESTAMP=$(python -c "import time; print time.time()")
echo "INFO: Using timestamp: ${TIMESTAMP}"

cmd "Create ${INSTANCE} instance" "nova boot --image=${IMAGE}
 --user-data password-reset-${INSTANCE}.userdata\
 --flavor ${FLAVOR}\
 --key-name demo\
 ${INSTANCE}"

wait_for_instances

INSTANCE_ID=$(nova list | awk "/${INSTANCE} / {print \$2}")
PORT_ID=$(neutron port-list --device_id ${INSTANCE_ID} | awk '/ip_address/ {print $2}')
neutron floatingip-create --port-id ${PORT_ID} external

cmd "Step 1. Request Password Reset" "nova meta ${INSTANCE} set password-reset=${TIMESTAMP}"
nova show ${INSTANCE} | grep -e Value -e name -e image -e id -e metadata -e "+--"
cmd "Step 2. Reboot Instance to Initiate Password Reset" "nova reboot ${INSTANCE}"
cmd "Delete ${INSTANCE} instance" "nova delete ${INSTANCE}"

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
  nova show ${INSTANCE} | grep -e Value -e " name" -e metadata -e "+--"
  echo -en "\nWaiting for ${INSTANCE} instance(s) to build "
	while [[ $(nova list | grep BUILD) ]]
        do
                echo -n "."
                sleep 2
        done
        echo ""
  INSTANCE_ID=$(nova list | awk "/${INSTANCE} / {print \$2}")
  PORT_ID=$(neutron port-list --device_id ${INSTANCE_ID} | awk '/ip_address/ {print $2}')
  neutron floatingip-create --port-id ${PORT_ID} external
}
cmd() {
  if [ ! -z "$1" ]  
  then
    CMD_TEXT=$1
    CMD_TO_RUN=$2
  fi
  if [ ! "$3" == "--nowait" ]
  then
    echo ""
    echo "Press ENTER to initiate '${CMD_TEXT}'"
    read
  fi
  echo "INFO: Starting command: '${CMD_TO_RUN}'"
  ${CMD_TO_RUN}
  echo "INFO: Finished with '${CMD_TEXT}'"
}

TIMESTAMP=$(python -c "import time; print time.time()")
echo "INFO: Using timestamp: ${TIMESTAMP}"

cmd "Step 0: Create ${INSTANCE} instance with no metadata" "nova boot --image=${IMAGE}
 --user-data password-reset-${INSTANCE}.userdata\
 --flavor ${FLAVOR}\
 --key-name demo\
 ${INSTANCE}" "--nowait"

wait_for_instances

cmd "Step 1: Set password reset in metadata" "nova meta ${INSTANCE} set password-reset=${TIMESTAMP}"
cmd "Step 2: Reboot Instance to Initiate Password Reset" "nova reboot ${INSTANCE}"
cmd "Delete ${INSTANCE} instance" "nova delete ${INSTANCE}"

TIMESTAMP=$(python -c "import time; print time.time()")
echo "INFO: Using timestamp: ${TIMESTAMP}"

cmd "Step 0: Create ${INSTANCE} instance with metadata" "nova boot --image=${IMAGE}
 --user-data password-reset-${INSTANCE}.userdata\
 --flavor ${FLAVOR}\
 --meta password-reset="${TIMESTAMP}" \
 --key-name demo\
 ${INSTANCE}" "--nowait"

wait_for_instances

cmd "Step 1: Reboot Instance to Initiate Password Reset" "nova reboot ${INSTANCE}"
cmd "Delete ${INSTANCE} instance" "nova delete ${INSTANCE}"

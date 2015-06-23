# Password Reset

OpenStack uses novan get-password and nova root-password to manage the admin password. However, in some cases it may be required to reset an existing password without rebuilding the instance. This method also handles the case where the private key was lost or an SSH keypair not used. 

See the password-reset-demo.sh script for details on how to use this.

## Preparation
Configure a webserver to host the password-reset.py script. The .userdata scripts point to the webserver to dynamically grab the reset script. The examples here use http://10.12.137.55:8181 so modify as needed.

## Boot an instance with metadata

```
  nova boot --image=rhel-7\
  --user-data password-reset-linux.userdata\
  --flavor m1.small\
  --key-name demo\
  --file password-reset-linux.sh\
  instance
```

```
  nova boot --image=windows2012-r2\
  --user-data password-reset-windows.userdata\
  --flavor m1.small\
  --key-name demo\
  --file password-reset-windows.sh\
  instance
```

NOTE: For Windows injection the following package is required: 
https://people.redhat.com/~rjones/libguestfs-winsupport/7/7.1/x86_64/libguestfs-winsupport-7.1-4.el7.x86_64.rpm

* Step 1. Request Password Reset with: "nova meta instance set reset-password=true"
* Step 2. Reboot Instance to Initiate Password Reset with: "nova reboot instance"
* Step 3. Poweron Instance with: "nova start instance"

** Change metadata and reboot the system to reset the password
```
  nova meta ${INSTANCE} set password-reset=${TIMESTAMP}
  nova reboot ${INSTANCE}
```

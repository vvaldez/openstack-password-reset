# Password Reset

## Overview

OpenStack uses a few different methods to manage authentication into the instance. First of all, cloud images typically do not have a password set for the root or Administrator user. On the Linux side, root SSH is typically disabled by default. There are a few ways to connect to a Linux or Windows instance:
* Images
  * For Linux based instances these examples refer to the **RHEL 7** cloud image https://access.redhat.com/downloads/content/69/ver=/rhel---7/7.0/x86_64/product-downloads
  * For Windows based instances these examples refer to the **cloudbase-init** image: http://www.cloudbase.it/cloud-init-for-windows-instances/
* Using SSH keys
  * If an SSH keypair is used, the public key is injected via cloud-init for Linux so the private key can be used to SSH in as a user. For RHEL this is cloud-user.
  * For Windows, cloudbase-init creates an admin user and generates a random password. The public key is used to encrypt the password and post it to the metadata service. The password is retrievable via **nova get-password**.
* Using password retrieval
  * The **nova get-password** command can be used to retrieve a password from the metadata service. This is added by default with the Windows cloudbase-init image. For Linux this can be scripted and posted to metadata
  * The password can also be retrieved via Horizon with a small change in the Horizon configuration: https://dev.cloudwatt.com/en/blog/horizon-icehouse-retrieve-a-password-generated-by-an-instance.html
* Rebuild the Instance
  * Any instance can be rebuilt with the **nova rebuild** command so the standard out-of-the box authentication experience will work. To preserve any data simply use a Cinder block volume to store state data if needed
* Change password
  * The **nova root-password** command is intended to reset the root or Administrator account, but does not yet work on KVM-based hypervisors
* Password Reset
  * The scripts here add a new functionality to use both user-data and meta-data to instruct a script on the system to reset and post a new password

## Prerequisites
In order to pass in userdata and modify the password properly, ensure the following packages are installed on the KVM hypervisors:

```
  yum install libguestfs python-libguestfs libguestfs-tools-c libguestfs-winsupport
```

NOTE: For Windows injection the following package version or higher is required:
* https://people.redhat.com/~rjones/libguestfs-winsupport/7/7.1/x86_64/libguestfs-winsupport-7.1-4.el7.x86_64.rpm


## Preparation
Configure a webserver to host the **password-reset.py** script. The **.userdata** scripts point to the webserver to dynamically fetch the password reset script. The examples here use **http://10.12.137.55:8181** so modify as needed.

## Pass Script to Instance via user-data

Boot an instance in Horizon and for the **Post-Creation** tab either browse to or paste in the appropriate user-data script based on the OS that is being instantiated. 

Alternatively, use the CLI or API:

```
  nova boot --image=rhel-7\
  --user-data password-reset-linux.userdata\
  --flavor m1.small\
  instance
```

```
  nova boot --image=windows2012-r2\
  --user-data password-reset-windows.userdata\
  --flavor m1.small\
  instance
```
## Request Password Reset via meta-data

Set the meta-data parameter **password-reset** to something. A timestamp is a good value since it changes over time and subsequent reset requests will not work if the value passed is the same as it was previously. For example, setting **password-reset=true** will work the first time, but the script running on the instance will cache this value and will not reset it in the future if this same value is used. Therefore, a timestamp is a good value to pass as it will be unique each time.

```
  nova meta ${INSTANCE} set password-reset=${TIMESTAMP}
```

## Reboot Instance
Lastly, reboot the instance so the script is run which will check meta-data for the password-reset request. For Linux this can be accomplished from the NOVNC console with CTRL+ALT+DEL. For Windows server this is more difficult so **nova** can be used.

```
  nova reboot ${INSTANCE}
```

## Password Reset
As part of the boot up process the **password-reset.py** script will be fetched and executed. If requested, the password for root or admin will be reset and posted to the console. Part of this scripted process includes another instance reboot so the actual password can be displayed.

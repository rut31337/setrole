#!/bin/bash

# Set CloudForms/ManageIQ server roles on the command line
# Patrick Rutledge prutledg@redhat.com

# You must get configure_server_settings.rb from https://github.com/ManageIQ/manageiq/blob/master/tools/configure_server_settings.rb and install it in /var/www/miq/vmdb/tools and make it executable.

# This is a list of current known roles as of CloudForms 4.5
known_roles="automate ems_metrics_coordinator ems_metrics_collector ems_metrics_processor database_operations embedded_ansible ems_inventory ems_operations rhn_mirror event git_owner notifier reporting scheduler smartproxy smartstate user_interface web_services websocket"

# uncomment this if you want to use dry run to test the script
#deb="-d"

usage() {
        echo "Usage: $0 -r|--role <role to enable/disable>"
        echo "          -s|--serverid <serverid>"
        echo "          -d|--dry - Dry Run"
        echo "          -l|--list <comma separated list of ALL roles> (danger, no checking done)"
        echo "If using --list you must provide all roles that will be enabled, any missing roles in this list will be DISABLED."
}

if ! options=$(getopt -o hds:r:l: -l help,dry,role:,list:,serverid: -- "$@")
then
        usage
        exit 1
fi

# Defaut serverid
serverID=1

set -- $options

while [ $# -gt 0 ]
do
    case $1 in
    -r|--role) requested_role="$2" ; shift ;;
    -l|--list) requested_list="$2" ; shift ;;
    -s|--serverid) serverID="$2" ; shift ;;
    -d|--dry) deb="-d" ; shift ;;
    -h|--help) usage; exit ;;
    (--) shift; break;;
    (*) echo "$0: error - unrecognized option $1" 1>&2; usage; exit 1;;
    esac
    shift
done

if [ -n "$requested_list" -a -n "$requested_role" ]
then
        echo "Error, you cannot specify --role and --list."
        exit 1
fi

if [ -n "$requested_list" ]
then
        requested_list=`echo $requested_list|sed "s/'//g"`
        ./configure_server_settings.rb -s $serverID -p server/role -v $requested_list $deb
        exit
fi

requested_role=`echo $requested_role|sed "s/'//g"`
# Check if requested role is valid
found=false
for r in $known_roles
do
        if [ $requested_role == $r ]
        then
                found=true
                break
        fi
done
if [ $found == false ]
then
        echo "Error, the specified role ($requested_role) is invalid.  Exiting."
        exit 1
fi

if [ ! -d /var/www/miq/vmdb/tools ]
then
        echo "Error, /var/www/miq/vmdb/tools does not exist... are you sure this is a MIQ server?"
        exit 1
fi

# Get into VMDB tools working dir
cd /var/www/miq/vmdb/tools

if [ ! -x configure_server_settings.rb ]
then
        echo "Error, configure_server_settings.rb is not in /var/www/miq/vmdb/tools! Get it from https://github.com/ManageIQ/manageiq/blob/master/tools/configure_server_settings.rb and make it execuatable."
        exit 1
fi

# Get current roles by requesting a dummy role using "dry run"
current_roles=`./configure_server_settings.rb -s $serverID -p server/role -v dummy -d |grep Setting|awk '{print $5}'|sed -e 's/\[\([^]]*\)\],/\1/g'`

# See if the requested role is enabled or disabled
current_list=`echo $current_roles|sed 's/,/ /g'`
found=false
for r in $current_list
do
        if [ $requested_role == $r ]
        then
                echo "Role $requested_role is currently enabled, we will disable it."
                found=true
                break
        fi
done

if [ $found == false ]
then
        echo "Role $requested_role is currently disabled, we will enable it."
        # This is a role that is not currently enabled, append it to the role list
        new_roles=`echo "$current_roles,$requested_role"`
else
        # This is a role that is currently enabled, append it to the role list
        new_roles=""
        for r in $current_list
        do
                if [ $r != $requested_role ]
                then
                        new_roles+="$r,"
                fi
        done
        new_roles=`echo $new_roles|sed 's/,$//'`
fi

# Append new role in VMDB
./configure_server_settings.rb -s $serverID -p server/role -v $new_roles $deb

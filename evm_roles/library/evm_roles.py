#!/usr/bin/python

# EVM Roles Ansible Module
# Patrick Rutledge <prutledg@redhat.com>

DOCUMENTATION = '''
---
module: evm_roles
short_description: Enable/Disable/List EVM Roles
description:
     - Enable/Disable/List EVM Roles
options:
  state:
    description:
     - Indicate desired state of the target.
    default: present
    choices: ['present', 'absent', 'list']
  role:
     description:
      - Role you wish to enable or disable
'''

EXAMPLES = '''
# Disable EVM Role
---
- name: Disable EVM Role
  local_action:
    module: evm_roles
    role: "{{ role }}"
    state: absent
  register: enabled_roles
- debug: var=enabled_roles

# Enable EVM Role
---
- name: Enable EVM Role
  local_action:
    module: evm_roles
    role: "{{ role }}"
    state: present
  register: enabled_roles
- debug: var=enabled_roles

# Get List Of EVM Roles
---
- name: Get Enabled EVM Roles
  local_action:
    module: evm_roles
    state: list
  register: enabled_roles
- debug: var=enabled_roles
'''

def checkrole(module, role):
    if not role in known_roles:
        module.fail_json(msg = 'Unknown role requested: %s' % module.params.get("role"))

def main():
    ch = logging.StreamHandler(log_capture_string)
    ch.setLevel(logging.DEBUG)
    ### Optionally add a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    ### Add the console handler to the logger
    logger.addHandler(ch)
    ### Install configure_server_settings script in VMDB/tools if not already installed
    if not (os.path.isfile(fpath) and os.access(fpath, os.X_OK)):
      urllib.urlretrieve ("https://raw.githubusercontent.com/ManageIQ/manageiq/master/tools/configure_server_settings.rb", fpath)
      os.chmod(fpath, stat.S_IREAD | stat.S_IEXEC)

    argument_spec=dict(
            role=dict(required=False, type='str'),
            state=dict(default='present', choices=['present', 'absent', 'list']),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
    )
    cmd = fpath + " -s 1 -p server/role -v dummy -d |grep Setting|awk '{print $5}'"
    croles = subprocess.check_output(cmd, shell=True)
    croles = croles.rstrip()
    croles = croles.replace("[", "")
    croles = croles.replace("],", "")
    current_roles=croles.split(',')
    if module.params.get('state') == 'present':
      checkrole(module, module.params.get("role"))
      enable_role(module, current_roles)
    elif module.params.get('state') == 'absent':
      checkrole(module, module.params.get("role"))
      disable_role(module, current_roles)
    elif module.params.get('state') == 'list':
      list_roles(module, croles)
    else:
      module.exit_json(msg = 'Unsupported state')

def enable_role(module, current_roles):
    try:
	role = module.params.get("role")
        if not role in current_roles:
          new_roles=current_roles
          new_roles.append(role)
          nroles = ','.join(new_roles)
          cmd = fpath + " -s 1 -p server/role -v " + nroles
          subprocess.check_output(cmd, shell=True)
          module.exit_json(changed=True, msg="Role %s enabled" % role, cmd = '%s' % cmd, enabled_roles='%s' % nroles)
        else:
          module.exit_json(changed=False, msg="No change necessary")
    except Exception, e:
        log_contents = log_capture_string.getvalue()
        log_capture_string.close()
        module.fail_json(msg = '%s' % e,stdout='%s' % log_contents)

def disable_role(module, current_roles):
    try:
	role = module.params.get("role")
        if role in current_roles:
          new_roles=current_roles
          new_roles.remove(role)
          nroles = ','.join(new_roles)
          cmd = fpath + " -s 1 -p server/role -v " + nroles
          subprocess.check_output(cmd, shell=True)
          module.exit_json(changed=True, msg="Role %s disabled" % role, cmd = '%s' % cmd, enabled_roles='%s' % nroles)
        else:
          module.exit_json(changed=False, msg="No change necessary")
    except Exception, e:
        log_contents = log_capture_string.getvalue()
        log_capture_string.close()
        module.fail_json(msg = '%s' % e,stdout='%s' % log_contents)

def list_roles(module, croles):
    try:
        roles = ''.join(croles)
        module.exit_json(changed=True, enabled_roles='%s' % roles)
    except Exception, e:
        log_contents = log_capture_string.getvalue()
        log_capture_string.close()
        module.fail_json(msg = '%s' % e,stdout='%s' % log_contents)

# import module snippets
import ansible
import os
import functools
import logging
import logging.handlers
import io
import datetime
import sys
import yaml
import json
import urllib

# Known Roles
known_roles = {"automate", "ems_metrics_coordinator", "ems_metrics_collector", "ems_metrics_processor", "database_operations", "embedded_ansible", "ems_inventory", "ems_operations", "rhn_mirror", "event", "git_owner", "notifier", "reporting", "scheduler", "smartproxy", "smartstate", "user_interface", "web_services", "websocket"}

# Path to confgure server settings.rb
fpath = "/var/www/miq/vmdb/tools/configure_server_settings.rb"

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_capture_string = io.BytesIO()

from ansible.module_utils.basic import *

main()

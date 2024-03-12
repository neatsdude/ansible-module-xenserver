#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
'''xen_vm_import: wrapper around xe vm-import command
   TODO:
    * Imports and creates the VM from the OVA file or image
'''

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: xen_vm_import
author:
    - Nitesh Dudhe (@neatsdude)
    - Jesse Cooper (@jessecooper)
version_added: "1.1"
short_description: Imports the OVA file to create the VM
requirements: [ xe ]
description:
    - Imports the OVA file to create the VM in xenserver guests using xe commands
    - Renames the VM and the description
    - Starts the VM 
options:
    filename:
        description:
            - Location of the OVA file
        required: true
    name_label:
        description:
            - The desired name of the VM
        required: true
    name_description:
        description:
            - The desired description of the VM
        required: true
    sr_name:
        description:
            - The storage name-label
        required: true

'''

EXAMPLES = '''
- xen_vm_import:
    filename: <ova filename>
    name_label: <vm name>
    name_description: <description of the vm-name>
    sr_name: <name of the host SR where you want to deploy the image>
'''

import os
import socket
import traceback

from ansible.module_utils.basic import (
    AnsibleModule,
    get_distribution,
    get_distribution_version,
    get_platform,
    load_platform_subclass,
)
from ansible.module_utils._text import to_native
from ansible.module_utils.xenserver_common import XeBase
import XeVmStart



class XeVmInstall(XeBase):
    """
    This is a xe vm_list command wrapper class
    """
    def get_sr_uuid(self, sr_name=None):
        self.cmd.append('sr-list')
        self.cmd.append('name-label={0}'.format(sr_name))
        rc, out, err = module.run_command(self.cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))
        out = [i.split(':')[1].strip() for i in out.splitlines() if 'uuid' in i]
        return to_native(out[0]).strip()

    def vm_change(self, name_label=None, name_description=None, vm_uuid=None):
        self.cmd.append('vm-param-set')
        self.cmd.append('uuid={0}'.format(vm_uuid))
        self.cmd.append('name-label={0}'.format(name_label))
        self.cmd.append('name-description={0}'.format(name_description))
        rc, out, err = module.run_command(self.cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))
        return to_native('Success').strip()

    def vm_import(self, filename=None, name_label=None, sr_uuid=None, name_description=None):
        """vm_list(str) -> dict
        Args:
            filename (str): parameters to return from each vm.
            name_label (str): parameters to return from each vm.
            sr_name (str): parameters to return from each vm.
            name_description (str): parameters to return from each vm.
        Returns:
            dict
        """
# Get the sr-uuid
        self.cmd.append('vm-import')
        self.cmd.append('filename={0}'.format(filename))
        self.cmd.append('sr-uuid={0}'.format(sr_uuid))
        rc, out, err = self.module.run_command(self.cmd)
        if rc != 0:
            self.module.fail_json(msg="%s Command failed rc=%d, out=%s, err=%s" % (self.cmd, rc, out, err))
        return to_native(out).strip()



def main():
    '''
     filename: <ova filename>
     name_label: <vm name>
     name_description: <description of the vm-name>
     sr_name: <name of the host SR where you want to deploy the image>
    '''
    global module
    module = AnsibleModule(
        argument_spec=dict(
            filename=dict(required=True),
            name_label=dict(required=True),
            name_description= {"required": True},
            sr_name= {"required": True}
        ),
        supports_check_mode=True,
    )

    get_sr_uuid_cmd = XeVmInstall(module)
    vm_import_cmd = XeVmInstall(module)
    vm_name_cmd = XeVmInstall(module)
    filename = module.params['filename']
    vm_name = module.params['name_label']
    name_description = module.params['name_description']
    sr_name = module.params['sr_name']

    sr_uuid = get_sr_uuid_cmd.get_sr_uuid(sr_name=sr_name)

    vm_uuid = vm_import_cmd.vm_import(
        filename=filename,
        sr_uuid=sr_uuid,
        )

    vm_report = vm_name_cmd.vm_change(
        name_label=vm_name,
        name_description=name_description,
        vm_uuid=vm_uuid
        )

    vm_start_cmd = XeVmStart(module)
    out = vm_start_cmd.vm_start(uuid=vm_uuid)
    out_formated = out.strip().split()[1::2]

    kw = dict(
        changed=True,
        sr_uuid=sr_uuid,
        vm_uuid=vm_uuid,
        vm_name_report=vm_report,
        vm_start=out,
        ansible_facts=dict(
            ansible_fqdn=socket.getfqdn(),
            ansible_domain='.'.join(socket.getfqdn().split('.')[1:])
            )
        )

    #if changed:
    #    kw['diff'] = {'after': '\n',
    #                  'before': '\n'}

    module.exit_json(**kw)

if __name__ == '__main__':
    main()

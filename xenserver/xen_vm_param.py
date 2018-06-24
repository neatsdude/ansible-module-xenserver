#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: xen_vm_param
author:
    - Jesse Cooper (@jessecooper)
version_added: "2.1"
short_description: Manage xenserver
requirements: [ xe ]
description:
    - Manage xenserver guests using xe commands
options:
    uuid:
        description:
            - uuid of vm
        required: true
    action:
        description:
            - [get|set|remove|add|clear] all or common seperated list of vm params to return
        required: true
    param-name:
        description:
            - the vm paramater
        required: true
'''

EXAMPLES = '''
- xen_vm_param:
    uuid: <vm uuid>
    action: get
    params-name: networks
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
# If this module ever gets into ansible or one could install it as such
#from ansible.module_utils.xenserver_common import XeBase

class XeBase(object):
    """
    This is a xe command generic class
    Is part of xenserver_common package
    """
    def __init__(self, module):
        self.module = module
        self.cmd = ['xe']

class XeVmParam(XeBase):
    """
    This is a xe vm_list command wrapper class
    """

    def get(self, uuid, param_name):
        """get(str, str) -> dict
        Args:
            params (str): parameters to return from each vm.
        Returns:
            dict
        """
        self.cmd.append('vm-param-get')
        self.cmd.append('uuid=%s' % uuid)
        self.cmd.append('param-name=%s' % param_name)
        rc, out, err = self.module.run_command(self.cmd)
        if rc != 0:
            self.module.fail_json(msg="Command failed rc=%d, out=%s, err=%s" % (rc, out, err))
        return to_native(out).strip()

def main():
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(required=True),
            uuid=dict(required=True),
            param=dict(required=True)
        ),
        supports_check_mode=True,
    )

    vm_param_cmd = XeVmParam(module)
    vm_param = module.params['param']
    vm_uuid = module.params['uuid']
    vm_action = module.params['action']

    if vm_action == 'get':
        out = vm_param_cmd.get(vm_uuid, vm_param)
    # set up other actions
    
    # split output by \n and : and remove the last 3 indexe I am sure this can be done better
    #out_formated = 
    kw = dict(changed=True, vm_param=out,
              ansible_facts=dict(
                    ansible_fqdn=socket.getfqdn(),
                    ansible_domain='.'.join(socket.getfqdn().split('.')[1:])
                    )
              )

    #if changed:
    #    kw['diff'] = {'after': 'hostname = ' + name + '\n',
    #                  'before': 'hostname = ' + name_before + '\n'}

    module.exit_json(**kw)

if __name__ == '__main__':
    main()

#!/usr/bin/python

# TODO: Add copyright data here
import traceback

ANSIBLE_METADATA = {
    "metadata_version": "1.0",
    "status": ["preview"],
    "supported_by": "community"
}

DOCUMENTATION = """
---
module: aff
short_description: Check and create traffic change requests with Algosec FireFlow.
description:
    - Algosec Ansible module will help you manage and orchestrate your tasks to work with Algosec FireFlow service.
    - When used, the `aff` command will check if a certain traffic is allowed between `source` and `dest`.
    - If the connectivity is not allowed between the nodes, the module will create a "Change Request"
    - on Algosec's FireFlow and will provide the change request url in the module call result.
author: "Almog Cohen (@AlmogCohen)"

requirements:
    - algosec - python package that should be obtained internally

options:
    ip_address:
        required: true
        description:
            - IP address (or hostname) of the Algosec server.
    user:
        required: true
        description:
            - Username credentials to use for auth.
    password:
        required: true
        description:
            - Password credentials to use for auth.
    requester:
        required: true
        description:
            - The first and last name of the requester.
    email:
        required: true
        description:
            - The email address of the requester.
    sources:
        required: true
        description:
            - Comma separated list of IP address for the traffic sources.
            - For example: 192.168.1.5, PAYROLL_WEB_SERVER
    destinations:
        required: true
        description:
            - Comma separated list of IP address for the traffic destinations.
            - For example: 192.168.1.5, PAYROLL_WEB_SERVER
    services:
        required: true
        description:
            - List of services of the traffic to allow. Accepted services are as defined on Algosec
            - or by port/proto format (e.g. tcp/50,udp/100,ssh).
    template:
        default: Basic
        required: false
        description:
            - Full name of template which ticket is to be opened upon.
            - Default is the Basic template.
    transport:
        default: ipv4
        choices: [ ipv4, ipv6 ]
        description:
            - Set the network connectivity check transport layer type.

"""

EXAMPLES = """
   - name: Create Traffic Change Request if needed
     hosts: algosec-server

     - name: Create Traffic Change Request
       # We use delegation to use the local python interpreter (and virtualenv if enabled)
       delegate_to: localhost
       aff_allow_traffic:
         ip_address: 192.168.58.128
         user: admin
         password: S0mePA$$w0rd

         requester: almogco
         email: almog@email.com
         sources: 192.168.12.12,123.123.132.123
         destinations: 16.47.71.62,234.234.234.234
         services: HTTPS,http,tcp/80,tcp/51
       register: result

     - name: Print the test results
       debug: var=result
"""

RETURN = """
is_traffic_allowed:
    description: State whether the traffic is currently allowed
    returned:
        - always
    type: bool
    sample: True, False
connectivity_status:
    description: The current connectivity status of the traffic.
    Can be Allowed, Blocked, Partially Blocked or Not Routed.
    returned:
        - always
    type: string
    sample: Partially, Allowed, Blocked, Not Routed
change_request_url:
    description: URL for the change request ticket on the Algosec server
    returned:
        - on traffic Change Request creation
    type: string
    sample: https://192.168.58.128/FireFlow/Ticket/Display.html?id=2410
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from algosec.api_client import AlgosecFirewallAnalyzerAPIClient, AlgosecFireFlowAPIClient
    from algosec.errors import AlgosecAPIError
    from algosec.models import DeviceAllowanceState, ChangeRequestAction

    HAS_LIB = True
except ImportError:
    HAS_LIB = False


def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            ip_address=dict(required=True),
            user=dict(required=True, aliases=["username"]),
            password=dict(aliases=["pass", "pwd"], required=True, no_log=True),
            requester=dict(required=True),
            email=dict(required=True),
            sources=dict(type="list", required=True),
            destinations=dict(type="list", required=True),
            services=dict(type="list", required=True),
            template=dict(default="Basic", required=False),
            transport=dict(default="ipv4", required=False, choices=["ipv4", "ipv6"])
        )
    )

    if not HAS_LIB:
        module.fail_json(msg="algoec package is required for this module")

    try:
        afa_client = AlgosecFirewallAnalyzerAPIClient(
            module.params["ip_address"],
            module.params["user"],
            module.params["password"],
        )
        connectivity_status = afa_client.check_connectivity_status(
            source=module.params["sources"],
            dest=module.params["destinations"],
            service=module.params["services"],
        )
    except AlgosecAPIError:
        module.fail_json(msg="Error executing traffic simulation query:\n{}".format(traceback.format_exc()))
        return

    response = {"connectivity_status": connectivity_status.value.text}
    if connectivity_status == DeviceAllowanceState.ALLOWED:
        module.log("Connectivity check passed. No FireFlow ticket is required")
        response["is_traffic_allowed"] = True
        response["changed"] = False
    else:
        response["is_traffic_allowed"] = False

        module.log(
            "Connectivity status is {}. Opening ticket on Algosec FireFlow at {}".format(
                connectivity_status,
                module.params["ip_address"]
            )
        )
        if not module.check_mode:
            try:
                aff_client = AlgosecFireFlowAPIClient(
                    module.params["ip_address"],
                    module.params["user"],
                    module.params["password"],
                )
                requester = module.params["requester"]
                change_request_url = aff_client.create_change_request(
                    # TODO: drop action is not yet supported
                    action=ChangeRequestAction.ALLOW,
                    subject="Allow {} traffic from {} to {} (issued via Ansible)".format(
                        module.params["services"],
                        module.params["sources"],
                        module.params["destinations"]
                    ),
                    requester_name=requester,
                    email=module.params["email"],
                    sources=module.params["sources"],
                    destinations=module.params["destinations"],
                    services=module.params["services"],
                    template=module.params["template"],
                    description="Traffic change request created by {} directly from Ansible.".format(requester)
                )
            except AlgosecAPIError:
                module.fail_json(msg="Error creating change request:\n{}".format(traceback.format_exc()))
                return
            response["change_request_url"] = change_request_url
        response["changed"] = True

    module.exit_json(**response)


if __name__ == "__main__":
    main()

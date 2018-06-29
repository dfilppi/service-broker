[![CircleCI](https://circleci.com/gh/cloudify-examples/mariadb-blueprint.svg?style=svg)](https://circleci.com/gh/cloudify-examples/mariadb-blueprint)

# MariaDB Blueprint

This blueprint deploys a MariaDB/Galera Cluster. This blueprint is part of the *End-to-end Solutions Package*, which demonstrates functionality in Cloudify using a Database, Load Balancer, and several front-end applications. After completing this deployment, continue with the solution package by installing the [HAProxy Blueprint](https://github.com/cloudify-examples/haproxy-blueprint).


## Compatibility

Tested with:
  * Cloudify 4.3.1


## Pre-installation steps

**Please note the following requirement for manager configuration.**

This example requires configuration of [multiple management (agent) networks](https://docs.cloudify.co/4.3.0/install_maintain/installation/installing-manager/#multi-network-management) upon installation of your Cloudify Manager.

The required name of the agent network is `external`, and should map to a public IP address. For example:

```bash
[centos@ip-10-10-4-47 ~]$ sudo grep "networks" /etc/cloudify/config.yaml 
    networks: {default: 10.10.4.47, external: 54.67.45.103}
```

Upload the required plugins:

  * [Openstack Plugin](https://github.com/cloudify-cosmo/cloudify-openstack-plugin/releases).
  * [AWSSDK Plugin](https://github.com/cloudify-incubator/cloudify-awssdk-plugin/releases).
  * [AWS Plugin](https://github.com/cloudify-cosmo/cloudify-aws-plugin/releases).
  * [GCP Plugin](https://github.com/cloudify-incubator/cloudify-gcp-plugin/releases).
  * [Azure Plugin](https://github.com/cloudify-incubator/cloudify-azure-plugin/releases).
  * [Utilities Plugin](https://github.com/cloudify-incubator/cloudify-utilities-plugin/releases).

_Check the relevant blueprint for the latest version of the plugin._

**Install the relevant example network blueprint for the IaaS that you wish to deploy on:**

  * [Openstack Example Network](https://github.com/cloudify-examples/openstack-example-network)
  * [AWS Example Network](https://github.com/cloudify-examples/aws-example-network)
  * [GCP Example Network](https://github.com/cloudify-examples/gcp-example-network)
  * [Azure Example Network](https://github.com/cloudify-examples/azure-example-network)

In addition to the pre-requisites for your example network blueprint, you will need the following secrets:

  * `agent_key_private` and `agent_key_public`. If you do not already have these secrets, can generate them with the `keys.yaml` blueprint in the [helpful blueprint](https://github.com/cloudify-examples/helpful-blueprint) repo.


## Installation

On your Cloudify Manager, navigate to _Local Blueprints_ select _Upload_.

[Right-click and copy URL](https://github.com/cloudify-examples/mariadb-blueprint/archive/master.zip). Paste the URL where it says _Enter blueprint url_. Provide a blueprint name, such as _db_ in the field labeled _blueprint name_.

Select the blueprint for the relevant IaaS you wish to deploy on, for example _aws.yaml_ from _Blueprint filename_ menu. Click **Upload**.

After the new blueprint has been created, click the **Deploy** button.

Navigate to _Deployments_, find your new deployment, select _Install_ from the _workflow_s menu. At this stage, you may provide your own values for any of the default _deployment inputs_.

For example, the _openstack.yaml_ blueprint requires that you provide a value for `image`. This is the ID of a _Centos 7_ image. You may also need to override the default `flavor` as the default value `2` may not be available in your account or appropriate.


## Uninstallation

Navigate to the deployment and select `Uninstall`. When the uninstall workflow is finished, select `Delete deployment`.

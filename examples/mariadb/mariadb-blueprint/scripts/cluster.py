#!/usr/bin/env python

import subprocess
from cloudify import ctx
from cloudify import exceptions


def execute_command(_command, env_vars=None):

    ctx.logger.debug('_command {0}.'.format(_command))

    subprocess_args = {
        'args': _command.split(),
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE
    }

    if env_vars:
        # env_vars = execute_command('printenv')
        subprocess_args['env'] = env_vars

    ctx.logger.debug('subprocess_args {0}.'.format(subprocess_args))

    process = subprocess.Popen(**subprocess_args)
    output, error = process.communicate()

    ctx.logger.debug('command: {0} '.format(_command))
    ctx.logger.debug('error: {0} '.format(error))
    ctx.logger.debug('process.returncode: {0} '.format(process.returncode))

    if process.returncode:
        ctx.logger.error('Running `{0}` returns error.'.format(_command))
        return False

    return output


if __name__ == '__main__':

    if ctx.type == 'relationship-instance':
        instance = ctx.target.instance
    elif ctx.type == 'node-instance':
        instance = ctx.instance
    else:
        raise exceptions.NonRecoverableError('Neither relationship, nor node -instance.')

    cluster_addresses = \
        instance.runtime_properties.get(
            'cluster_addresses', [])

    if not cluster_addresses:
        instance.runtime_properties['cluster_addresses'] = \
            cluster_addresses

    for relationship in instance.relationships:
        ip = relationship.target.instance.runtime_properties.get('ip')
        if not ip or ip in cluster_addresses:
            continue
        master = instance.runtime_properties.get('master')
        if not master:
            instance.runtime_properties['master'] = ip
        cluster_addresses.append(ip)

    instance.runtime_properties['cluster_addresses'] = \
        cluster_addresses

    if ctx.type == 'node-instance':
        instance.update()

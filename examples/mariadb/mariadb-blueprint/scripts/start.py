#!/usr/bin/env python

import subprocess
import tempfile
from cloudify import ctx
from cloudify.state import ctx_parameters as inputs
from cloudify.exceptions import OperationRetry


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

    execute_command('sudo systemctl stop mariadb')
    cluster_addresses = inputs.get('cluster_addresses', [])
    master = inputs.get('master', ctx.instance.host_ip)

    if ctx.instance.host_ip not in cluster_addresses:
        cluster_addresses.append(ctx.instance.host_ip)

    config = """[galera]
wsrep_on={0}
binlog_format={1}
default-storage-engine={2}
innodb_autoinc_lock_mode={3}
wsrep_provider={4}
wsrep_cluster_name='{5}'
wsrep_node_address='{6}'
wsrep_node_name='{7}'
wsrep_sst_method={8}
wsrep_cluster_address='{9}'
""".format(
        inputs.get('wsrep_on', 'ON'),
        inputs.get('binlog_format', 'row'),
        inputs.get('default_storage_engine', 'InnoDB'),
        inputs.get('innodb_autoinc_lock_mode', '2'),
        inputs.get('wsrep_provider', '/usr/lib64/galera/libgalera_smm.so'),
        ctx.deployment.id,
        ctx.instance.host_ip,
        ctx.instance.id,
        inputs.get('wsrep_sst_method', 'rsync'),
        inputs.get('wsrep_cluster_address',
                   'gcomm://{0}'.format(','.join(cluster_addresses)))
    )

    tf = tempfile.NamedTemporaryFile()
    with open(tf.name, 'w') as outfile:
        outfile.write(config)

    execute_command('sudo cp {0} {1}'.format(tf.name, '/etc/my.cnf.d/server.cnf'))

    if ctx.workflow_id == 'install' and master == ctx.instance.host_ip:
        started = execute_command('sudo /usr/bin/galera_new_cluster')
    else:
        started = execute_command('sudo systemctl start mariadb')

    if started is False:
        raise OperationRetry('Didnt start/add cluster node. Retrying.')

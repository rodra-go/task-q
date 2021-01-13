#!/usr/bin/env python3
import os
import sys
import pwd
import time
import click
import signal
import peewee
import tempfile
from subprocess import Popen



@click.group()
@click.version_option(version='1.1.0')
def main():
    """TaskQ - Task queue tool CLI"""
    pass


@main.command(short_help='installs taskq dependencies')
@click.argument('home_path',
                type=click.Path(exists=True),
                required=True)
@click.argument('owner_id',
                type=int,
                required=True)
def install(home_path, owner_id):
    from taskq.utils import Configuration
    config = Configuration()
    config.install(home_path, owner_id)
    initdb()
    ENV = config.loadEnv()
    fix_db_permissions(ENV['db_path'])


@main.command(short_help='adds a new task to queue')
@click.argument('command',
                type=str,
                required=True)
@click.argument('context',
                type=click.Path(exists=True),
                required=False)
def add(command, context):
    from taskq.resources import TaskCreator
    user_id = os.getuid()
    user_name = pwd.getpwuid( os.getuid() ).pw_name

    task = TaskCreator(command, context, user_id, user_name)
    task_id = task.add_to_queue()
    return task_id





@main.command(short_help="aborts a task from the queue")
@click.argument('task_id',
                type=int,
                required=True)
def abort(task_id):
    from taskq.resources import TaskQHelper
    ownership = TaskQHelper.check_ownership(task_id, os.getuid())

    if ownership is True:
        response = TaskQHelper.abort_task(task_id)
        if response:
            click.echo('Task with ID={} successfully aborted!'.format(task_id))
        else:
            click.echo('Task with ID={} is not running anymore, impossible to abort!'.format(task_id))
    else:
        click.echo('Impossible to abort task.')
        click.echo('Only the task owner or the queue owner can abort the task with ID={}.'.format(task_id))


@main.command(short_help="inserts task back into the queue")
@click.argument('task_id',
                type=int,
                required=True)
def reset(task_id):
    from taskq.resources import TaskQHelper
    ownership = TaskQHelper.check_ownership(task_id, os.getuid())

    if ownership is True:
        response = TaskQHelper.reset_task(task_id)
        if response:
            click.echo('Task with ID={} successfully reseted!'.format(task_id))
        else:
            click.echo('Task with ID={} is waiting to be processed!'.format(task_id))

    else:
        click.echo('Impossible to reset task.')
        click.echo('Only the task owner or the queue owner can reset the task with ID={}.'.format(task_id))


@main.command(short_help="shows task queue information")
@click.argument('task_id',
                type=int,
                required=True)
def info(task_id):
    from taskq.resources import TaskQHelper
    table = TaskQHelper.task_info(task_id)

    click.echo(table)


@main.command(short_help='shows queue information')
@click.option('--all', 'mode', flag_value='all',
                help='shows all tasks')
@click.option('--running', 'mode', flag_value='running',
                help='shows only running tasks')
@click.option('--done', 'mode', flag_value='done',
                help='shows only completed tasks')
@click.option('--mine', 'mode', flag_value='mine',
                help='show only tasks belonging to the user')
def show_queue(mode):
    from taskq.resources import TaskQHelper
    table = TaskQHelper.show_queue(mode)

    click.echo(table)


@main.command(short_help='calls the task handler')
def call_task_handler():
    from taskq.utils import Configuration
    config = Configuration()
    ENV = config.loadEnv()

    if str(ENV['owner_id']) == str(os.getuid()):
        from taskq.resources import TaskHandler
        handler = TaskHandler()
        message = handler.handle()
    else:
        click.echo('Sorry, only the TaskQ Owner can call the Task Handler.')


def initdb():
    from taskq.utils import Configuration
    config = Configuration()
    ENV = config.loadEnv()

    if os.path.exists(ENV['db_path']):
        os.remove(ENV['db_path'])

    from taskq.models import Queue, Variable

    Queue.create_table()
    click.echo("Table 'Queue' created successfully!")
    Variable.create_table()
    click.echo("Table 'Variable' created successfully!")

def fix_db_permissions(db_path):
    with Popen(['sudo chmod g+w {}'.format(db_path)], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True) as proc:
        proc.wait()

@main.command(short_help="starts the queue processing")
def start():
    from taskq.utils import Configuration
    config = Configuration()
    ENV = config.loadEnv()

    if str(ENV['owner_id']) == str(os.getuid()):
        import taskq
        from taskq.resources import TaskQHelper

        def start_task_handler():

            def show_setting_prgrp():
                os.setpgrp()

            script = '''#!/bin/sh
            screen -dmS taskq_task_handler bash -c "python3 {}"
            '''.format(os.path.join(taskq.__path__[0], 'task-handler.py'))

            script_file = tempfile.NamedTemporaryFile('wt')
            script_file.write(script)
            script_file.flush()

            proc = Popen(
                ['sh', script_file.name],
                preexec_fn=show_setting_prgrp,
            )
            time.sleep(1)
            os.killpg(proc.pid, signal.SIGUSR1)
            time.sleep(3)

            TASK_HANDLER_ACTIVE = TaskQHelper.modify_variable('TASK_HANDLER_ACTIVE','True')


        TASK_HANDLER_ACTIVE = TaskQHelper.get_variable('TASK_HANDLER_ACTIVE')

        if TASK_HANDLER_ACTIVE is None:
            click.echo('Starting Task Handler Bot...')
            start_task_handler()
        else:
            if TASK_HANDLER_ACTIVE.value == 'False':
                click.echo('Restarting Task Handler Bot...')
                start_task_handler()
            else:
                TASK_HANDLER_PID = TaskQHelper.get_variable('TASK_HANDLER_PID')
                click.echo('Task Handler already running! PID: {}'.format(TASK_HANDLER_PID.value))

    else:
        click.echo('Sorry, only the TaskQ Owner can start the queue.')


@main.command(short_help="stops the queue processing")
def stop():
    from taskq.utils import Configuration
    config = Configuration()
    ENV = config.loadEnv()

    if str(ENV['owner_id']) == str(os.getuid()):
        from taskq.resources import TaskQHelper

        TASK_HANDLER_ACTIVE = TaskQHelper.get_variable('TASK_HANDLER_ACTIVE')
        if TASK_HANDLER_ACTIVE is not None:

            if TASK_HANDLER_ACTIVE.value == 'True':
                TASK_HANDLER_PID = TaskQHelper.get_variable('TASK_HANDLER_PID')

                if TASK_HANDLER_PID is not None:
                    cmd = 'kill -9 {}'.format(str(TASK_HANDLER_PID.value))
                    proc = Popen(cmd, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
                    proc.wait()
                    TASK_HANDLER_ACTIVE = TaskQHelper.modify_variable('TASK_HANDLER_ACTIVE','False')
                    click.echo("Task Handler successfully stoped! PID: {}".format(TASK_HANDLER_PID.value))
                    TASK_HANDLER_PID = TaskQHelper.del_variable('TASK_HANDLER_PID')

                else:
                    click.echo('Impossible to find Task Handler PID!')

            else:
                click.echo('Impossible to stop, Task Handler not active.')

        else:
            click.echo('Impossible to stop, Task Handler not active.')

    else:
        click.echo('Sorry, only the TaskQ Owner can stop the queue.')



if __name__ == '__main__':
    args = sys.argv
    if "--help" in args or len(args) == 1:
        print("TaskQ")
    main()

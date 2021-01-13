#!/usr/bin/env python3
import os
import sys
import time
import signal
import click
import schedule
from subprocess import Popen
from taskq.resources import TaskQHelper


def signal_usr1(signum, frame):
    "Callback invoked when a signal is received"
    global received
    received = True


def job():
    # click.echo('Calling Task Handler')
    proc = Popen(['taskq', 'call-task-handler'], stdin=None, stdout=None, stderr=None, close_fds=True)
    proc.wait()

    return proc.pid

def bot():
    schedule.every(10).seconds.do(job)

    while 1:
        # click.echo('Running...')
        schedule.run_pending()
        # click.echo('...')
        time.sleep(1)
        # click.echo('Done!\n')

received = False
TASK_HANDLER_PID = TaskQHelper.modify_variable('TASK_HANDLER_PID',str(os.getpid()))
signal.signal(signal.SIGUSR1, signal_usr1)

bot()

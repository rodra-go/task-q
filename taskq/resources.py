#!/usr/bin/env python3
import os
import pwd
import tabulate
import tempfile
import datetime
from pathlib import Path
from subprocess import Popen
from taskq.settings import TASKQ_SLOTS
from taskq.models import Queue, Variable, AbortQueue
from taskq.utils import Configuration

# Criamos o banco de dados
config = Configuration()
ENV = config.loadEnv()

class TaskCreator:
    def __init__(self, command, context, user_id, user_name):
        self.command = command
        self.context = context
        self.user_id = user_id
        self.user_name = user_name

    def add_to_queue(self):
        task = {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'command': self.command,
            'context': self.context,
        }
        task_id = Queue.insert(task).execute()

        return task_id



class TaskHandler:
    def __init__(self):
        self.subprocess = None
        self.pid = None
        self.next = None
        self.slot_available = None

    def handle(self):
        self.check_slot_availability()
        if self.slot_available == True:
            self.get_next()
            if self.next:
                self.execute()
                self.update()
                return self.message()
            else:
                return self.message()
        else:
            return self.message()


    def get_next(self):
        self.next = (Queue.select()
                        .where(Queue.is_waiting == True)
                        .order_by(Queue.created_at.asc())
                        .first()
                    )


    def check_slot_availability(self):
        check = (Queue.select()
                        .where(Queue.is_running == True)
                        .count()
                    )

        if check >= TASKQ_SLOTS:
            self.slot_available = False
        else:
            self.slot_available = True


    def execute(self):

        script = '''#!/bin/sh
        {}
        '''.format(self.next.command)

        print(script)

        script_file = tempfile.NamedTemporaryFile('wt')
        script_file.write(script)
        script_file.flush()


        with Popen(['sh', script_file.name], close_fds=True) as proc:
            self.next.is_waiting = False
            self.next.is_running = True
            self.next.pid = proc.pid
            self.next.started_at = datetime.datetime.now()
            self.next.save()
            proc.wait()


    def update(self):
        self.next.is_complete = True
        self.next.is_running = False
        self.next.completed_at = datetime.datetime.now()
        self.next.save()


    def message(self):
        if self.slot_available:
            if self.next:
                if self.pid:
                    return 'Task with ID={} running with PID={}.'
            else:
                return 'No elegible task to be executed.'
        else:
            return 'System is currently busy. Please, try again later.'


class AbortHandler:
    def __init__(self):
        self.subprocess = None
        self.pid = None
        self.next = None
        self.slot_available = None

    def handle(self):

        self.get_next()
        if self.next:
            self.execute()
            self.update()
            return self.message()
        else:
            return self.message()


    def get_next(self):
        self.next = (AbortQueue.select()
                        .where(AbortQueue.is_waiting == True)
                        .order_by(AbortQueue.created_at.asc())
                        .first()
                    )


    def execute(self):

        script = '''#!/bin/sh
        pkill -P {}
        '''.format(self.next.pid)

        print(script)

        script_file = tempfile.NamedTemporaryFile('wt')
        script_file.write(script)
        script_file.flush()


        with Popen(['sh', script_file.name], close_fds=True) as proc:
            self.next.is_waiting = False
            self.next.started_at = datetime.datetime.now()
            proc.wait()
            self.next.save()

        task = (Queue.select()
                    .where(Queue.id == self.next.task_id)
                    .first()
                )

        task.is_running = False
        task.is_canceled = True
        task.canceled_at = datetime.datetime.now()
        task.save()

    def update(self):
        self.next.is_complete = True
        self.next.completed_at = datetime.datetime.now()
        self.next.save()


    def message(self):
        if self.slot_available:
            if self.next:
                if self.pid:
                    return 'Abort with ID={} running with PID={}.'
            else:
                return 'No elegible abort to be executed.'
        else:
            return 'System is currently busy. Please, try again later.'


class TaskQHelper:

    @classmethod
    def check_ownership(cls, task_id, user_id):
        task = (Queue.select()
                    .where(Queue.id == task_id)
                    .first()
                )

        if task is not None:
            if (str(task.user_id) == str(user_id)
                or str(ENV['owner_id']) == str(user_id)):
                return True
            else:
                return False
        else:
            return None

    @classmethod
    def abort_task(cls, task_id):
        task = (Queue.select()
                    .where(Queue.id == task_id)
                    .first()
                )

        if task is not None:
            if task.is_running:
                # with Popen(['pkill', '-P', str(task.pid)], close_fds=True) as proc:
                #     proc.wait()
                abort = {
                    'user_id': task.user_id,
                    'user_name': task.user_name,
                    'task_id': task.id,
                    'pid': task.pid,
                    'is_waiting': True,
                    'is_complete': False,
                    'created_at': datetime.datetime.now(),
                }
                abort_id = AbortQueue.insert(abort).execute()
                # task.is_waiting = False
                # task.is_running = False
                # task.is_canceled = True
                # task.canceled_at = datetime.datetime.now()
                # task.save()
                return task.id
            elif not task.is_running and task.is_waiting:
                task.is_waiting = False
                task.is_running = False
                task.is_canceled = True
                task.canceled_at = datetime.datetime.now()
                task.save()
                return task.id
            else:
                return None
        else:
            return None

    @classmethod
    def reset_task(cls, task_id):
        task = (Queue.select()
                    .where(Queue.id == task_id)
                    .first()
                )
        if task.is_running:
            # with Popen(['pkill', '-P', str(task.pid)], close_fds=True) as proc:
            #     proc.wait()
            abort = {
                'user_id': task.user_id,
                'user_name': task.user_name,
                'task_id': task.id,
                'pid': task.pid,
                'is_waiting': True,
                'is_complete': False,
                'created_at': datetime.datetime.now(),
            }
            abort_id = AbortQueue.insert(abort).execute()
            task.is_waiting = True
            task.is_complete = False
            task.started_at = None
            task.completed_at = None
            task.save()

            return task.id
        elif not task.is_running and not task.is_waiting:
            task.is_waiting = True
            task.is_complete = False
            task.started_at = None
            task.completed_at = None
            task.save()
            return task.id
        else:
            return None


    @classmethod
    def task_info(cls, task_id):
        data = (Queue.select()
                    .where(Queue.id == task_id)
                    .dicts()
                )

        header = list(Queue._meta.fields.keys())

        f = lambda x: [str(y) for y in list(x.values())]
        rows = [f(task) for task in data]

        return tabulate.tabulate(rows, header)


    @classmethod
    def show_queue(cls, mode):

        data = (Queue.select()
                     .where(Queue.is_waiting == True)
                     .order_by(Queue.created_at.asc())
                     .dicts()
                )

        if mode == 'mine':
            data = (Queue.select()
                         .where(Queue.user_id == os.getuid())
                         .order_by(Queue.created_at.asc())
                         .dicts()
                    )

        if mode == 'all':
            data = (Queue.select()
                         .order_by(Queue.created_at.asc())
                         .dicts()
                    )

        elif mode == 'done':
             data = (Queue.select()
                         .where(Queue.is_complete == True)
                         .order_by(Queue.created_at.asc())
                         .dicts()
                    )
        elif mode == 'running':
             data = (Queue.select()
                         .where(Queue.is_running == True)
                         .order_by(Queue.created_at.asc())
                         .dicts()
                    )

        header = list(Queue._meta.fields.keys())

        f = lambda x: [str(y) for y in list(x.values())]
        rows = [f(task) for task in data]

        return tabulate.tabulate(rows, header)


    @classmethod
    def show_abort_queue(cls, mode):

        data = (AbortQueue.select()
                     .where(AbortQueue.is_waiting == True)
                     .order_by(AbortQueue.created_at.asc())
                     .dicts()
                )

        if mode == 'mine':
            data = (AbortQueue.select()
                         .where(AbortQueue.user_id == os.getuid())
                         .order_by(AbortQueue.created_at.asc())
                         .dicts()
                    )

        if mode == 'all':
            data = (AbortQueue.select()
                         .order_by(AbortQueue.created_at.asc())
                         .dicts()
                    )

        elif mode == 'done':
             data = (AbortQueue.select()
                         .where(AbortQueue.is_complete == True)
                         .order_by(AbortQueue.created_at.asc())
                         .dicts()
                    )


        header = list(AbortQueue._meta.fields.keys())

        f = lambda x: [str(y) for y in list(x.values())]
        rows = [f(task) for task in data]

        return tabulate.tabulate(rows, header)


    @classmethod
    def modify_variable(cls, name: str, value: str):
        data = {
            'name': name,
            'value': value,
        }
        variable = (Variable.select()
                            .where(Variable.name == name)
                            .first())

        if variable is None:
            var_id = Variable.insert(data).execute()
        else:
            variable.value = value
            variable.save()

        return variable

    @classmethod
    def get_variable(cls, name: str):
        variable = (Variable.select()
                            .where(Variable.name == name)
                            .first())

        return variable


    @classmethod
    def del_variable(cls, name: str):
        variable = (Variable.select()
                            .where(Variable.name == name)
                            .first())
        variable.delete_instance()

        return True

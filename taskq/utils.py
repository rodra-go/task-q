#!/usr/bin/env python3
import os
import pwd
import taskq
import pickle
from pathlib import Path
from subprocess import Popen


class Configuration:
    def __init__(self):
        self.env = {}
        self.env_path = os.path.join(taskq.__path__[0], 'env.pkl')
        self.home_path = None
        self.owner_id = None

    def install(self, home_path, owner_id):
        self.home_path = home_path
        self.owner_id = owner_id
        self.createEnv()
        self.createHome()
        self.fixPermissions()
        self.saveEnv()

    def createEnv(self):
        self.env['owner_id'] = self.owner_id
        self.env['env_path'] = self.env_path
        self.env['taskq_home_path'] = self.home_path + '/.taskq'
        self.env['home_user_id'] = os.getuid()
        self.env['home_user_name'] = pwd.getpwuid( os.getuid() ).pw_name
        self.env['db_path'] = self.home_path + '/.taskq/taskq.db'
        self.env['permission_fix_cmds'] = [
            'sudo chown -R :100 {}'.format(self.env['taskq_home_path']),
            'sudo chmod -R g+rwxs {}'.format(self.env['taskq_home_path']),
            'sudo setfacl -d -m g::rwx {}'.format(self.env['taskq_home_path']),
        ]


    def loadEnv(self):
        if os.path.exists(self.env_path):
            with open(self.env_path, 'rb') as file:
                self.env = pickle.load(file)
            return self.env
        else:
            return None


    def createHome(self):
        if not os.path.exists(self.env['taskq_home_path']):
            os.makedirs(self.env['taskq_home_path'])
            return True
        else:
            return False


    def fixPermissions(self):
        for cmd in self.env['permission_fix_cmds']:
            proc = Popen([cmd], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
            proc.wait()

        return True


    def saveEnv(self):
        with open(self.env['env_path'], 'wb') as file:
            pickle.dump(self.env,
                        file,
                        pickle.HIGHEST_PROTOCOL)

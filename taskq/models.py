#!/usr/bin/env python3
import os
import peewee
import datetime
import click
from taskq.utils import Configuration

# Criamos o banco de dados
config = Configuration()
ENV = config.loadEnv()
db = peewee.SqliteDatabase(ENV['db_path'])


class BaseModel(peewee.Model):
    """Classe model base"""

    class Meta:
        # Indica em qual banco de dados a tabela
        # 'author' sera criada (obrigatorio). Neste caso,
        # utilizamos o banco 'codigo_avulso.db' criado anteriormente
        database = db


class Queue(BaseModel):

    """
    Classe que representa a tabela Author
    """
    # A tabela possui apenas o campo 'name', que receberá o nome do autor sera unico
    user_id = peewee.IntegerField(null=True)
    user_name = peewee.TextField(null=True)
    command = peewee.TextField(null=True)
    context = peewee.TextField(null=True)
    output = peewee.TextField(null=True)
    pid = peewee.IntegerField(null=True)
    is_waiting = peewee.BooleanField(default=True)
    is_running = peewee.BooleanField(default=False)
    is_broken = peewee.BooleanField(default=False)
    is_complete = peewee.BooleanField(default=False)
    is_canceled = peewee.BooleanField(default=False)
    created_at = peewee.DateTimeField(default=datetime.datetime.now)
    started_at = peewee.DateTimeField(null=True)
    completed_at = peewee.DateTimeField(null=True)
    canceled_at = peewee.DateTimeField(null=True)


class AbortQueue(BaseModel):

    """
    Classe que representa a tabela Author
    """
    # A tabela possui apenas o campo 'name', que receberá o nome do autor sera unico
    user_id = peewee.IntegerField(null=True)
    user_name = peewee.TextField(null=True)
    pid = peewee.IntegerField(null=True)
    task_id = peewee.IntegerField(null=True)
    is_waiting = peewee.BooleanField(default=True)
    is_complete = peewee.BooleanField(default=False)
    created_at = peewee.DateTimeField(default=datetime.datetime.now)
    started_at = peewee.DateTimeField(null=True)
    completed_at = peewee.DateTimeField(null=True)


class Variable(BaseModel):

    """
    Classe que representa a tabela Author
    """
    # A tabela possui apenas o campo 'name', que receberá o nome do autor sera unico
    name = peewee.TextField(null=True)
    value = peewee.TextField(null=True)
    created_at = peewee.DateTimeField(default=datetime.datetime.now)
    updated_at = peewee.DateTimeField

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.now()
        return super(Variable, self).save(*args, **kwargs)


if __name__ == '__main__':
    try:
        Queue.create_table()
        click.echo("Table 'Queue' created successfully!")
        Variable.create_table()
        click.echo("Table 'Variable' created successfully!")
        AbortQueue.create_table()
        click.echo("Table 'AbortQueue' created successfully!")
    except peewee.OperationalError:
        click.echo("Table 'Queue' already exists!")

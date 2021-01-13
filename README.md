# TaskQ

Simple CLI for multi user queue execution in Linux. TaskQ allows a single computer
to be used by different users concurrently. TaskQ allows each user to submit a
task to the same queue, which will be handled by the Task Handler Bot.

## 1. Setup

### 1.1. Installing TaskQ

TaskQ needs to be installed in order to set its dependecies correctly.
In order to do that, it needs a folder to be the TaskQ home, where the app
will save its local files, and also an UID to define
the owner of TaskQ's queue. It is important to note that the Task Handler Bot
will run with the privileges of user that executed the installation step below.

``
sudo taskq install $HOME $(id -u $USER)
``

### 1.2. Starting Task Handler

The Task Handler is the bot that will execute the tasks in the TaskQ queue.
It is necessary to start it manually. It is important to note that only the
TaskQ queue owner has the priviliges to start or to stop the Task Handler.

``
taskq start
``

In order to stop the queue, do:

``
taskq stop
``

## 2. Using the TaskQ


### 2.1. Show the queue

To show the queue waiting list, run the command below:

``
taskq show-queue
``

It is possible to filter the table with the options below:
- **all**: shows all the tasks in the queue, including the completed and failed ones.
- **running**: shows only the tasks that are running at the moment
- **mine**: shows only the tasks that belong to the user
- **done**: shows only the tasks that are complete


### 2.2. Add a task to the queue

A task for TaskQ is basically a bash command that will be executed within the
queue owner context. To add a task to the queue, do:

``
taskq add '<command string>'
``

### 2.3. Abort a task

Aborting a task will remove it out of the waiting list:

``
taskq abort <task id>
``

### 2.4. Reset a task

Reseting a task will put it back into the waiting list:

``
taskq reset <task id>
``

For more information, excecute ``taskq --help``.

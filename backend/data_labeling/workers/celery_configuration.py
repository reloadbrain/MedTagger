"""Module responsible for definition of Celery configuration"""
import os
from typing import List

from data_labeling.config import ConfigurationFile


def get_all_modules_with_tasks() -> List[str]:
    """Generate list of all modules with Celery tasks

    :return: list of all modules with tasks
    """
    module_prefix = 'data_labeling.workers.'
    tasks_directory = 'data_labeling/workers'
    python_files = filter(lambda filename: filename.endswith('.py'), os.listdir(tasks_directory))
    return [module_prefix + os.path.splitext(filename)[0] for filename in python_files]


configuration = ConfigurationFile()
broker_url = configuration.get('celery', 'broker', fallback='pyamqp://guest:guest@localhost//')
imports = get_all_modules_with_tasks()

# The default serializers for Celery >=3.1 is JSON, which doesn't make sense if we send binary data to task
task_serializer = 'pickle'
accept_content = {'pickle'}
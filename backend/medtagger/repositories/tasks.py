"""Module responsible for definition of TaskRepository."""
from typing import Any, List

from medtagger.database import db_connection_session, db_transaction_session
from medtagger.database.models import Task, LabelTag, Dataset
from medtagger.exceptions import InternalErrorException


def get_all_tasks(include_disabled: bool = False) -> List[Task]:
    """Fetch all tasks from database ordered by key."""
    query = Task.query
    if not include_disabled:
        query = query.filter(~Task.disabled)
    return query.order_by(Task.key).all()


def get_task_by_key(key: str) -> Task:
    """Fetch Task from database.

    :param key: key for a Task
    :return: Task object
    """
    with db_connection_session() as session:
        task = session.query(Task).filter(Task.key == key).first()
    return task


def add_task(key: str, name: str, image_path: str, datasets_keys: List[str],  # pylint: disable-msg=too-many-arguments
             description: str, label_examples: List[str], tags: List[LabelTag]) -> Task:
    """Add new Task to the database.

    :param key: key that will identify such Task
    :param name: name that will be used in the Use Interface for such Task
    :param image_path: path to the image that represents such Task (used in User Interface)
    :param datasets_keys: Keys of Datasets that Task takes Scans from
    :param description: Description of a given Task
    :param label_examples: List of paths to examples of labels for given Task
    :param tags: Label Tags that will be created and assigned to Task
    :return: Task object
    """
    with db_transaction_session() as session:
        task = Task(key, name, image_path)
        datasets = Dataset.query.filter(Dataset.key.in_(datasets_keys)).all()  # type: ignore
        task.datasets = datasets
        task.label_examples = label_examples
        task.available_tags = tags
        task.description = description
        session.add(task)
    return task


def assign_label_tag(tag: LabelTag, task_key: str) -> None:
    """Assign existing Label Tag to Task.

    :param tag: tag that should be assigned to Task
    :param task_key: key that will identify such Task
    """
    with db_transaction_session() as session:
        task = Task.query.filter(Task.key == task_key).one()
        task.available_tags.append(tag)
        session.add(task)


def unassign_label_tag(tag: LabelTag, task_key: str) -> None:
    """Unassign Label Tag from Task.

    :param tag: tag that should be unassigned from Task
    :param task_key: key that will identify such Task
    """
    with db_transaction_session() as session:
        task = Task.query.filter(Task.key == task_key).one()
        task.available_tags.remove(tag)
        session.add(task)


def update(task_key: str, name: str = None, image_path: str = None,  # pylint: disable-msg=too-many-arguments
           datasets_keys: List[str] = None, description: str = None, label_examples: List[str] = None) -> Task:
    """Update Datasets where this Task will be available.

    :param task_key: key that will identify such Task
    :param name: (optional) new name for such Task
    :param image_path: (optional) new path to the image which shows on the UI
    :param description: (optional) Description of a given Task
    :param label_examples: (optional) List of paths to examples of labels for given Task
    :param datasets_keys: (optional) keys of Datasets which should have this Task
    """
    with db_transaction_session() as session:
        task = Task.query.filter(Task.key == task_key).one()
        update_parameter_if_needed(task, 'name', name)
        update_parameter_if_needed(task, 'image_path', image_path)
        update_parameter_if_needed(task, 'description', description)
        update_parameter_if_needed(task, 'label_examples', label_examples)
        if datasets_keys:
            datasets = Dataset.query.filter(Dataset.key.in_(datasets_keys)).all()  # type: ignore
            task.datasets = datasets
        session.add(task)
    return task


def update_parameter_if_needed(task: Task, name: str, value: Any) -> None:
    """Help function to update single parameter."""
    if value is not None:
        setattr(task, name, value)


def disable(task_key: str) -> None:
    """Disable existing Task."""
    with db_transaction_session():
        disabling_query = Task.query.filter(Task.key == task_key)
        updated = disabling_query.update({'disabled': True}, synchronize_session='fetch')
        if not updated:
            raise InternalErrorException(f'Task "{task_key}" was not disabled due to unknown database error.')


def enable(task_key: str) -> None:
    """Enable existing Task."""
    with db_transaction_session():
        enabling_query = Task.query.filter(Task.key == task_key)
        updated = enabling_query.update({'disabled': False}, synchronize_session='fetch')
        if not updated:
            raise InternalErrorException(f'Task "{task_key}" was not enabled due to unknown database error.')

from typing import List
from .schemas import Task, TaskList, TaskStatus

def parse_sheet_to_tasks(sheet_values: List[List[str]]) -> TaskList:
    """
    Convert raw Google Sheets values into validated Task objects.
    Expects first row to be headers.
    """
    headers = sheet_values[0]
    rows = sheet_values[1:]

    tasks = []
    for row in rows:
        try:
            task = Task(
                task_id=int(row[0]),
                description=row[1],
                status=TaskStatus(row[2]) if len(row) > 2 else TaskStatus.TODO
            )
            tasks.append(task)
        except Exception as e:
            # log + skip invalid rows
            print(f"Skipping invalid row {row}: {e}")

    return TaskList(tasks=tasks)

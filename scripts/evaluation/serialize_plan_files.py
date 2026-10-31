"""Validate DAGs and impose explicit shared-file edit ordering, preserving dependencies."""
import posixpath


def files(task):
    return {posixpath.normpath(path.replace('\\','/')).casefold() for path in task['implementation_files']}


def ancestors(tasks):
    by_id={t['id']:t for t in tasks}
    if len(by_id)!=len(tasks):raise ValueError('Duplicate task IDs')
    result={}
    def visit(id,visiting):
        if id not in by_id:raise ValueError('Unknown dependency: '+id)
        if id in visiting:raise ValueError('Dependency cycle')
        if id in result:return result[id]
        found=set()
        for parent in by_id[id]['depends_on']:
            found.add(parent);found.update(visit(parent,visiting|{id}))
        result[id]=found
        return found
    for id in by_id:visit(id,set())
    return result


def conflicts(tasks):
    parents=ancestors(tasks);found=[]
    for i,left in enumerate(tasks):
        for right in tasks[i+1:]:
            overlap=files(left)&files(right)
            if overlap and left['id'] not in parents[right['id']] and right['id'] not in parents[left['id']]:
                found.append(dict(left=left['id'],right=right['id'],files=sorted(overlap)))
    return found


def serialize(tasks):
    """Use a stable topological order; add resource-order edges only where needed."""
    ancestors(tasks)
    pending=list(tasks);ordered=[];done=set()
    while pending:
        ready=next(t for t in pending if set(t['depends_on'])<=done)
        ordered.append(ready);done.add(ready['id']);pending.remove(ready)
    writers={};added=[]
    for task in ordered:
        for path in sorted(files(task)):
            previous=writers.get(path)
            if previous and previous not in ancestors(tasks)[task['id']]:
                task['depends_on'].append(previous)
                added.append(dict(task=task['id'],depends_on=previous,reason='serialize edits to shared file',file=path))
            writers[path]=task['id']
    if conflicts(tasks):raise AssertionError('Unserialized shared-file edits remain')
    return added

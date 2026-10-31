"""New reference application boundary, separate from the existing Qt application."""
from copy import deepcopy
from ghost_box.mail.search import matches

class MailApp:
    def __init__(self, *, provider, model, clock):
        self.provider,self.model,self.clock = provider,model,clock
        self.account=None; self._mail=[]; self.coverage={}; self.result=None
        self._epoch=0; self._operations=set(); self._model=None; self._last_used=clock()
    def switch_account(self, account):
        self.clear(); self.account=account
    def clear(self):
        self._mail=[]; self.coverage={}; self.result=None
        self._epoch+=1; self._operations.clear()
    def messages(self):
        return deepcopy(self._mail)
    def fetch(self, start, end):
        if self.account is None or start>=end or start.tzinfo is None or end.tzinfo is None:
            raise ValueError('Select account and ordered timezone-aware dates')
        rows=self.provider.fetch(self.account,start,end)
        self._mail=list({m['id']:deepcopy(m) for m in rows}.values())
        self.coverage={'account':self.account,'start':start,'end':end}
    def search(self, query, *, sender, start, end):
        selected=[m for m in self._mail if query and matches(m,query)
                  and matches(m,sender,field='sender') and start.timestamp()<=m['timestamp']<end.timestamp()]
        return {'messages':deepcopy(selected),'coverage':deepcopy(self.coverage),'scope':'downloaded-only'}
    def answer(self, ids, question):
        by_id={m['id']:m for m in self._mail}
        if not ids or any(i not in by_id for i in ids): raise ValueError('Select downloaded messages')
        answer=self.model.answer(deepcopy([by_id[i] for i in ids]),question)
        if not set(answer['source_ids'])<=set(ids): raise ValueError('Foreign citation')
        self.result=deepcopy(answer); self._last_used=self.clock()
        return answer
    def summarize(self, ids):
        by_id={m['id']:m for m in self._mail}
        if not ids or any(i not in by_id for i in ids): raise ValueError('Select downloaded messages')
        answer=self.model.summarize(deepcopy([by_id[i] for i in ids]))
        if not set(answer['source_ids'])<=set(ids): raise ValueError('Foreign citation')
        self.result=deepcopy(answer); self._last_used=self.clock()
        return answer
    def begin_operation(self):
        self._last_used=self.clock()
        op=(self._epoch,object()); self._operations.add(op); return op
    def cancel(self, op):
        self._operations.discard(op)
    def finish(self, op, result):
        if op not in self._operations: return False
        self._operations.remove(op); self.result=result; self._last_used=self.clock(); return True
    def load_model(self, path):
        if self._model!=path:
            if self._model is not None: self.model.unload()
            self.model.load(path); self._model=path
        self._last_used=self.clock()
    def unload_model(self):
        if self._model is not None: self.model.unload(); self._model=None
    def check_idle(self):
        if not self._operations and self.clock()-self._last_used>=300: self.unload_model()

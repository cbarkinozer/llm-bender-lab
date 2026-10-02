"""Read W&B key from SSH stdin, never echo or persist it."""
import json
import os
import sys
import wandb

key=sys.stdin.read().strip()
if not key:
    raise ValueError('Missing W&B key on stdin')
os.environ['WANDB_API_KEY']=key
api=wandb.Api()
viewer=api.viewer
print(json.dumps({'authenticated':bool(viewer),'entity':api.default_entity}))

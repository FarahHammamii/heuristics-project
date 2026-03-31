import os

from sentry_sdk import init


print(hasattr(init, 'solomon_randomise'))

print("="*50)
print("TEST PHASE 1: INITIALISATION")
print("="*50)
from test_phase1 import test_phase1
df1, df1_summary = test_phase1()

"""Run full data migration from litigation_context.db to product DB."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'src')

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from litigationos.db.connection import DatabaseManager
from litigationos.db.migrations import MigrationManager

SOURCE_DB = r'C:\Users\andre\LitigationOS\litigation_context.db'
TARGET_DB = r'C:\Users\andre\LitigationOS\11_CODE\litigationos\data\litigationos.db'

import os
os.makedirs(os.path.dirname(TARGET_DB), exist_ok=True)

source = DatabaseManager(SOURCE_DB)
target = DatabaseManager(TARGET_DB)
target.initialize()

mgr = MigrationManager(source, target)
mgr.migrate_all()

status = mgr.get_status()
for step, info in status.items():
    print(f'{step}: {info}')

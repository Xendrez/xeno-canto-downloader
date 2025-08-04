#!/usr/bin/env python3
"""
Update the original labels.csv file in place with Xeno-canto results
Creates a backup first
"""

import shutil
from datetime import datetime
from update_labels_with_results import update_labels_csv

# Create backup
backup_filename = f"labels_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
shutil.copy('labels.csv', backup_filename)
print(f"Created backup: {backup_filename}")

# Update the original file
update_labels_csv(input_file='labels.csv', output_file='labels.csv')
print("\nOriginal labels.csv has been updated.")
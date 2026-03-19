import os
dirs = [
    r'C:\Users\andre\LitigationOS\00_SYSTEM\autonomos',
    r'C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\sentinel',
    r'C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\inquisitor',
    r'C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\shared',
    r'C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\db',
    r'C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\tests',
]
for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f'Created: {d} (exists={os.path.isdir(d)})')
print('DONE')

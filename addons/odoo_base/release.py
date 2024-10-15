# -*- coding: utf-8 -*-

RELEASE_LEVELS = [ALPHA, BETA, RELEASE_CANDIDATE, FINAL] = ['alpha', 'beta', 'candidate', 'final']
RELEASE_LEVELS_DISPLAY = {ALPHA: ALPHA,
                          BETA: BETA,
                          RELEASE_CANDIDATE: 'rc',
                          FINAL: ''}

# version_info format: (MAJOR, MINOR, MICRO, RELEASE_LEVEL, SERIAL)
# inspired by Python's own sys.version_info, in order to be
# properly comparable using normal operators, for example:
#  (6,1,0,'beta',0) < (6,1,0,'candidate',1) < (6,1,0,'candidate',2)
#  (6,1,0,'candidate',2) < (6,1,0,'final',0) < (6,1,2,'final',0)

version_info = (1, 40, 1, FINAL, '-skit', '1.0')  # Each release cycle, update this version
release_date = '2024-10-07'  # YYYY-MM-DD [HH:MM]

# DO NOT TOUCH BELOW CODE
version = '.'.join(str(s) for s in version_info[:3]) + RELEASE_LEVELS_DISPLAY[version_info[3]] + str(version_info[4] or '') + version_info[5]
series = serie = major_version = '.'.join(str(s) for s in version_info[:2])

product_name = 'SearatesERP'
description = 'SearatesERP for Cargoes Community'
long_desc = '''
'''

url = 'https://searateserp.com'
author = 'Intech Creative Services Pvt. Ltd.'
author_email = 'connect@searateserp.com'
license = 'OPL'

nt_service_name = "SearatesERP-server-" + series.replace('~', '-')

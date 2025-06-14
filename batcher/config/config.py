"""Plug-in configuration.

Use `c` to access, create or modify configuration entries.
"""

import os


c.STDOUT_LOG_HANDLES = []
c.STDERR_LOG_HANDLES = ['file']

c.WARN_ON_INVALID_SETTING_VALUES = True

c.PLUGIN_NAME = 'batcher'
c.DOMAIN_NAME = 'batcher'
c.PLUGIN_TITLE = lambda: _('Batcher')
c.PLUGIN_VERSION = '1.1'
c.PLUGIN_VERSION_RELEASE_DATE = 'June 14, 2025'
c.AUTHOR_NAME = 'Kamil Burda'
c.COPYRIGHT_YEARS = '2023-2025'
c.PAGE_URL = 'https://kamilburda.github.io/batcher'
c.DOCS_URL = f'{c.PAGE_URL}/docs/usage'
c.LOCAL_DOCS_PATH = os.path.join(c.PLUGIN_DIRPATH, 'docs', 'usage', 'index.html')
c.REPOSITORY_USERNAME = 'kamilburda'
c.REPOSITORY_NAME = 'batcher'
c.REPOSITORY_URL = 'https://github.com/kamilburda/batcher'
c.BUG_REPORT_URL_LIST = [
  ('GitHub', 'https://github.com/kamilburda/batcher/issues')
]

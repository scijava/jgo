import jgo
import pathlib
import tempfile
import unittest

import logging
_logger = logging.getLogger(__name__)

class ExpansionTest(unittest.TestCase):

    def test_groovy_issue_46(self):
        shortcuts = {'groovy': 'org.codehaus.groovy:groovy-groovysh:org.codehaus.groovy.tools.shell.Main+commons-cli:commons-cli:1.3.1'}

        tmp_dir = tempfile.mkdtemp(prefix='jgo-test-cache-dir')
        m2_repo = pathlib.Path.home() / '.m2' / 'repository'

        primary_endpoint, workspace = jgo.resolve_dependencies(
            'groovy',
            cache_dir    = tmp_dir,
            m2_repo      = m2_repo,
            update_cache = True,
            shortcuts    = shortcuts,
            verbose      = 1)
        _logger.debug('Got primary_endpoint %s and workspace %s', primary_endpoint, workspace)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
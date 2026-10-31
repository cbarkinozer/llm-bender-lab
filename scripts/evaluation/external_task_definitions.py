"""Authored external-app task contracts, pytest targets and diagnostic faults.

No upstream test bodies are copied. Source snapshots are external references.
"""
from textwrap import dedent

TASKS = []


def task(app, suffix, module, contract, tests, rationale, faults):
    TASKS.append(dict(application=app, suffix=suffix, module=module,
                     contract=contract, tests=dedent(tests).lstrip(),
                     rationale=rationale, faults=faults))


task('litecli', 'sql-table-identifiers', 'litecli.packages.parseutils',
     'extract_tables(sql: str) returns (schema or None, table, alias or None) tuples in query order. '
     'Cover an empty query, schema-qualified JOINs and INSERT targets; do not treat selected or inserted columns as tables. INSERT alias values are unspecified. Nested subqueries are outside this task because the pinned upstream has a known limitation.', r'''
from litecli.packages.parseutils import extract_tables


def test_empty_and_columns_only():
    assert extract_tables('') == []
    assert extract_tables('SELECT 1 AS answer') == []


def test_qualified_join_and_aliases():
    assert extract_tables('SELECT u.id FROM main.users u JOIN orders o ON u.id=o.user_id') == [
        ('main', 'users', 'u'), (None, 'orders', 'o')]


def test_insert_target_excludes_columns():
    assert [(schema, table) for schema, table, alias in extract_tables(
        'INSERT INTO users (id, name) VALUES (1, 2)')] == [(None, 'users')]
''', 'Empty and column-only inputs prevent invented tables. Joins and INSERT column lists exercise structure rather than simple keyword matching.',
     [('always-empty', 'm.extract_tables = lambda sql: []'),
      ('lose-schema', 'original=m.extract_tables\nm.extract_tables=lambda sql: [(None,t,a) for s,t,a in original(sql)]')])

task('litecli', 'sql-destructive-detection', 'litecli.packages.parseutils',
     'is_destructive(sql: str) is true when any statement starts with DROP, SHUTDOWN, DELETE, TRUNCATE or ALTER, '
     'ignoring case and SQL comments. A SELECT mentioning those words inside a string is safe. Empty input is safe.', r'''
import pytest
from litecli.packages.parseutils import is_destructive


@pytest.mark.parametrize('sql', ['', 'SELECT 1', "SELECT 'delete from users'", '-- delete\nSELECT 2'])
def test_safe_statements(sql):
    assert is_destructive(sql) is False


@pytest.mark.parametrize('sql', ['DROP TABLE users', '-- comment\ndElEtE FROM users',
                                    'SELECT 1; ALTER TABLE users ADD COLUMN age INT', 'TRUNCATE users'])
def test_destructive_statements(sql):
    assert is_destructive(sql) is True
''', 'Safe strings and comments reject substring detectors; a later destructive statement rejects first-statement-only checks.',
     [('always-safe', 'm.is_destructive=lambda sql: False'),
      ('first-statement-only', "original=m.is_destructive\nm.is_destructive=lambda sql: original(sql.split(';')[0])")])

task('litecli', 'completion-last-word', 'litecli.packages.parseutils',
     'last_word(text, include="alphanum_underscore") returns the final completion token. Empty input or trailing '
     'whitespace returns an empty string. Default mode retains letters/digits/underscores; most_punctuations '
     'also retains dollar signs but splits on periods, commas, colons and parentheses.', r'''
import pytest
from litecli.packages.parseutils import last_word


@pytest.mark.parametrize('text,expected', [('', ''), ('abc ', ''), ('abc\t', ''),
                                           ('select user_id', 'user_id'), ('select $name', 'name')])
def test_default_tokens(text, expected):
    assert last_word(text) == expected


def test_punctuation_mode():
    assert last_word('select $name', include='most_punctuations') == '$name'
    assert last_word('table.column', include='most_punctuations') == 'column'
''', 'Trailing whitespace is a boundary, not a token to strip. The same dollar-prefixed input distinguishes punctuation modes.',
     [('strip-whitespace', 'original=m.last_word\nm.last_word=lambda text,include="alphanum_underscore": original(text.rstrip(),include)'),
      ('ignore-mode', 'original=m.last_word\nm.last_word=lambda text,include="alphanum_underscore": original(text)')])

task('litecli', 'path-completion', 'litecli.packages.filepaths',
     'parse_path(path) returns (directory, final component, negative length of component or zero). '
     'complete_path(candidate, prefix) returns a matching candidate, None for a mismatch, or joins ~ with candidate '
     'when prefix is ~. suggest_path lists entries in an existing directory or the parent of a partial path. '
     'Use native os.path semantics and compare directory contents without ordering.', r'''
import os
from litecli.packages.filepaths import parse_path, complete_path, suggest_path


def test_path_parsing_and_matching():
    path = os.path.join('folder', 'draft')
    assert parse_path(path) == ('folder', 'draft', -5)
    assert parse_path('') == ('', '', 0)
    assert complete_path('draft.txt', 'dra') == 'draft.txt'
    assert complete_path('draft.txt', 'other') is None
    assert complete_path('draft.txt', '~') == os.path.join('~', 'draft.txt')


def test_directory_and_partial_path(tmp_path):
    (tmp_path / 'alpha.txt').write_text('a', encoding='utf-8')
    (tmp_path / 'beta').mkdir()
    assert set(suggest_path(str(tmp_path))) == {'alpha.txt', 'beta'}
    assert set(suggest_path(str(tmp_path / 'alp'))) == {'alpha.txt', 'beta'}
''', 'Temporary directories avoid machine-specific files. A mismatch is the negative control for an always-return-candidate completer.',
     [('accept-mismatches', 'm.complete_path=lambda candidate,prefix: candidate'),
      ('omit-parent-fallback', 'original=m.suggest_path\nm.suggest_path=lambda path: original(path) if m.os.path.exists(path) else []')])

task('litecli', 'sqlite-query-execution', 'litecli.sqlexecute',
     'SQLExecute(database_path) connects to a temporary SQLite database. run(sql) yields '
     '(title, rows, headers, status) for each statement. SELECT preserves Unicode, column labels and row order '
     'specified by ORDER BY. Empty input yields one (None,None,None,None) tuple. Invalid SQL raises OperationalError. '
     'Use conn.execute(sql, parameters) for bound inserts; run accepts only a SQL string. Close conn in a finally block.', r'''
import pytest
from litecli.sqlexecute import SQLExecute, OperationalError


def test_bound_unicode_rows_and_headers(tmp_path):
    db = SQLExecute(str(tmp_path / 'demo.sqlite'))
    try:
        list(db.run('CREATE TABLE messages(id INTEGER, body TEXT)'))
        db.conn.execute('INSERT INTO messages VALUES (?, ?)', (2, '\u00e7ay'))
        db.conn.execute('INSERT INTO messages VALUES (?, ?)', (1, "O'Reilly"))
        title, rows, headers, status = list(db.run('SELECT body AS message FROM messages ORDER BY id'))[0]
        assert title is None
        assert rows == [("O'Reilly",), ('\u00e7ay',)]
        assert headers == ['message']
        assert status == '2 rows in set'
    finally:
        db.conn.close()


def test_empty_and_invalid_sql(tmp_path):
    db = SQLExecute(str(tmp_path / 'errors.sqlite'))
    try:
        assert list(db.run('  ')) == [(None, None, None, None)]
        with pytest.raises(OperationalError):
            list(db.run('SELECT FROM'))
    finally:
        db.conn.close()
''', 'Bound values include an apostrophe and Unicode; exact result assertions catch lost rows and headers. A separate error case checks propagation.',
     [('drop-result-rows', 'original=m.SQLExecute.get_result\ndef broken(self,cursor):\n t,r,h,s=original(self,cursor)\n return t,([] if r is not None else r),h,s\nm.SQLExecute.get_result=broken'),
      ('swallow-sql-errors', 'original=m.SQLExecute.run\ndef broken(self,sql):\n try: yield from original(self,sql)\n except m.OperationalError: yield (None,None,None,None)\nm.SQLExecute.run=broken')])

task('litecli', 'special-command-dispatch', 'litecli.packages.special.main',
     'parse_special_command(sql) returns command stripped of + or -, Verbosity and stripped argument. '
     'A + suffix means VERBOSE, no suffix NORMAL, - SUCCINCT. execute(cursor,sql) routes a registered PARSED_QUERY '
     'handler using cur, arg, verbose keyword arguments, supports case-insensitive commands, and raises '
     'CommandNotFound for unknown commands. COMMANDS is the registry; isolate it with monkeypatch.', r'''
import pytest
from litecli.packages.special import main as special


def test_parse_verbosity_and_argument():
    assert special.parse_special_command('demo+  two words ') == ('demo', special.Verbosity.VERBOSE, 'two words')
    assert special.parse_special_command('demo-') == ('demo', special.Verbosity.SUCCINCT, '')
    assert special.parse_special_command('demo') == ('demo', special.Verbosity.NORMAL, '')


def test_dispatch_and_unknown(monkeypatch):
    monkeypatch.setattr(special, 'COMMANDS', {})
    calls = []
    def handler(**kwargs):
        calls.append(kwargs)
        return [('done',)]
    special.register_special_command(handler, 'demo', '', 'Demo')
    cursor = object()
    assert special.execute(cursor, 'DEMO+ value') == [('done',)]
    assert calls == [{'cur': cursor, 'arg': 'value', 'verbose': True}]
    with pytest.raises(special.CommandNotFound):
        special.execute(cursor, 'missing-command')
''', 'A real registered handler checks argument routing. Isolating the registry prevents leakage into later tests; the unknown-command case rejects universal fallback.',
     [('never-dispatch', 'm.execute=lambda *args: []'),
      ('lose-verbosity', 'original=m.parse_special_command\ndef broken(sql):\n c,v,a=original(sql)\n return c,m.Verbosity.NORMAL,a\nm.parse_special_command=broken')])

task('tldr-python-client', 'language-selection', 'tldr',
     'get_language_code strips encoding and region except pt_PT, pt_BR and zh_TW; pt maps to pt_PT. '
     'get_language_list uses TLDR_LANGUAGE first, then LANGUAGE entries, then LANG if absent, then English. '
     'C/POSIX LANG disables ordinary locale candidates but still permits an explicit TLDR_LANGUAGE. '
     'Isolate LANG, LANGUAGE and TLDR_LANGUAGE.', r'''
import pytest
import tldr


@pytest.mark.parametrize('locale,expected', [('tr_TR.UTF-8', 'tr'), ('pt', 'pt_PT'),
                                             ('pt_BR.UTF-8', 'pt_BR'), ('zh_TW', 'zh_TW')])
def test_language_codes(locale, expected):
    assert tldr.get_language_code(locale) == expected


def test_language_priority(monkeypatch):
    monkeypatch.setenv('LANG', 'de_DE.UTF-8')
    monkeypatch.setenv('LANGUAGE', 'fr:de')
    monkeypatch.setenv('TLDR_LANGUAGE', 'pt_BR')
    assert tldr.get_language_list() == ['pt_BR', 'fr', 'de', 'en']
    monkeypatch.setenv('LANG', 'C')
    assert tldr.get_language_list() == ['pt_BR', 'en']
    monkeypatch.delenv('TLDR_LANGUAGE')
    assert tldr.get_language_list() == ['en']
''', 'Locale normalization and precedence are distinct checks. C locale provides a negative control for leaking inherited language preferences.',
     [('english-only', "m.get_language_list=lambda: ['en']"),
      ('erase-special-region', "m.get_language_code=lambda language: language.split('.')[0].split('_')[0]")])

task('tldr-python-client', 'cache-path-selection', 'tldr',
     'get_cache_dir prioritizes XDG_CACHE_HOME/tldr, then HOME/.cache/tldr, then Path.home()/.cache/tldr. '
     'get_cache_file_path(command,platform,language) appends pages/platform/command.md for None or en and '
     'pages.<language>/platform/command.md otherwise. All locations must be temporary.', r'''
from pathlib import Path
import tldr


def test_cache_root_precedence(monkeypatch, tmp_path):
    xdg, home, fallback = (tmp_path / name for name in ('xdg', 'home', 'fallback'))
    monkeypatch.setenv('XDG_CACHE_HOME', str(xdg))
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: fallback))
    assert tldr.get_cache_dir() == xdg / 'tldr'
    monkeypatch.delenv('XDG_CACHE_HOME')
    assert tldr.get_cache_dir() == home / '.cache' / 'tldr'
    monkeypatch.delenv('HOME')
    assert tldr.get_cache_dir() == fallback / '.cache' / 'tldr'


def test_language_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(tldr, 'get_cache_dir', lambda: tmp_path)
    for language in (None, 'en'):
        assert tldr.get_cache_file_path('git', 'linux', language) == tmp_path / 'pages/linux/git.md'
    assert tldr.get_cache_file_path('git', 'linux', 'tr') == tmp_path / 'pages.tr/linux/git.md'
''', 'Every cache-root branch is exercised. English and translated paths distinguish the default namespace from translated pages.',
     [('ignore-xdg', "m.get_cache_dir=lambda: m.Path(m.os.environ['HOME'])/'.cache'/'tldr'"),
      ('ignore-language', "original=m.get_cache_file_path\nm.get_cache_file_path=lambda command,platform,language,system_cache=False: original(command,platform,'en',system_cache)")])

task('tldr-python-client', 'cache-freshness', 'tldr',
     'have_recent_cache(command,platform,language) is true for an existing cache with age in hours <= MAX_CACHE_AGE, '
     'and false for an older or missing file. Control tldr.datetime.now(), MAX_CACHE_AGE and the cache path; '
     'use local-naive datetime consistently and no sleeps.', r'''
import os
from datetime import datetime
import tldr


def test_cache_age_boundary_and_missing(monkeypatch, tmp_path):
    now = datetime(2026, 1, 15, 12)
    class Clock(datetime):
        @classmethod
        def now(cls):
            return now
    cache = tmp_path / 'git.md'
    monkeypatch.setattr(tldr, 'datetime', Clock)
    monkeypatch.setattr(tldr, 'MAX_CACHE_AGE', 24)
    monkeypatch.setattr(tldr, 'get_cache_file_path', lambda *args: cache)
    assert tldr.have_recent_cache('git', 'linux', 'en') is False
    cache.write_bytes(b'page')
    for hours, expected in [(1, True), (24, True), (25, False)]:
        timestamp = now.timestamp() - hours * 3600
        os.utime(cache, (timestamp, timestamp))
        assert tldr.have_recent_cache('git', 'linux', 'en') is expected
''', 'A controlled clock and exact hour boundaries distinguish inclusive expiry from strict expiry. Missing and stale files reject always-fresh behavior.',
     [('always-fresh', 'm.have_recent_cache=lambda *args: True'),
      ('strict-expiry', 'original=m.have_recent_cache\ndef broken(*args):\n old=m.MAX_CACHE_AGE\n m.MAX_CACHE_AGE=old-0.001\n try: return original(*args)\n finally: m.MAX_CACHE_AGE=old\nm.have_recent_cache=broken')])

task('tldr-python-client', 'page-url', 'tldr',
     'get_page_url(command,platform,remote,language) builds remote[.language]/platform/quoted-command.md. '
     'None remote uses PAGES_SOURCE_LOCATION; en or None language adds no suffix. Supply roots without trailing slash. '
     'Spaces and non-ASCII command characters must be percent encoded.', r'''
import pytest
import tldr


@pytest.mark.parametrize('language,suffix', [(None, ''), ('en', ''), ('tr', '.tr')])
def test_page_url_language(monkeypatch, language, suffix):
    monkeypatch.setattr(tldr, 'PAGES_SOURCE_LOCATION', 'https://pages.example/pages')
    assert tldr.get_page_url('git status', 'linux', None, language) == (
        'https://pages.example/pages' + suffix + '/linux/git%20status.md')


def test_custom_root_and_unicode():
    assert tldr.get_page_url('caf\u00e9', 'common', 'https://offline.example/docs', 'fr') == (
        'https://offline.example/docs.fr/common/caf%C3%A9.md')
''', 'Literal expected URLs test language routing and encoding independently of the production encoder. No remote requests are needed.',
     [('no-encoding', 'm.quote=lambda text: text'),
      ('english-suffix', "original=m.get_page_url\nm.get_page_url=lambda command,platform,remote,language: original(command,platform,remote,'en')")])

task('tldr-python-client', 'cache-network-routing', 'tldr',
     'get_page_for_platform(command,platform,remote,language,only_use_cache=False,system_cache=False) returns '
     'byte lines. With USE_CACHE=True a fresh cache avoids network. Otherwise a successful urlopen download '
     'uses timeout=10 and is cached; a failed download falls back to an available stale cache. '
     'A cache-only miss raises CacheNotExist without networking; a failed download with no cached page '
     'propagates the download error. Patch urlopen, cache readers/writers and freshness; do not contact a real server.', r'''
from io import BytesIO
import pytest
import tldr


def test_fresh_cache_avoids_network(monkeypatch):
    monkeypatch.setattr(tldr, 'USE_CACHE', True)
    monkeypatch.setattr(tldr, 'have_recent_cache', lambda *args: True)
    monkeypatch.setattr(tldr, 'load_page_from_cache', lambda *args: b'cached\npage')
    def unexpected(*args, **kwargs):
        pytest.fail('Fresh cache must avoid network')
    monkeypatch.setattr(tldr, 'urlopen', unexpected)
    assert tldr.get_page_for_platform('git', 'linux', None, 'en') == [b'cached', b'page']


def test_download_then_cache_and_failure_fallback(monkeypatch):
    monkeypatch.setattr(tldr, 'USE_CACHE', True)
    monkeypatch.setattr(tldr, 'have_recent_cache', lambda *args: False)
    writes, requests = [], []
    def download(request, **kwargs):
        requests.append((request.full_url, kwargs['timeout']))
        return BytesIO(b'fresh\npage')
    monkeypatch.setattr(tldr, 'urlopen', download)
    monkeypatch.setattr(tldr, 'store_page_to_cache', lambda *args: writes.append(args))
    monkeypatch.setattr(tldr, 'load_page_from_cache', lambda *args: b'stale')
    assert tldr.get_page_for_platform('git', 'linux', 'https://pages.example', 'en') == [b'fresh', b'page']
    assert requests == [('https://pages.example/linux/git.md', 10)]
    assert writes == [(b'fresh\npage', 'git', 'linux', 'en')]
    def failed(*args, **kwargs):
        raise OSError('offline')
    monkeypatch.setattr(tldr, 'urlopen', failed)
    assert tldr.get_page_for_platform('git', 'linux', None, 'en') == [b'stale']
    assert len(writes) == 1
    monkeypatch.setattr(tldr, 'load_page_from_cache', lambda *args: None)
    with pytest.raises(OSError, match='offline'):
        tldr.get_page_for_platform('git', 'linux', None, 'en')


def test_cache_only_miss(monkeypatch):
    monkeypatch.setattr(tldr, 'USE_CACHE', True)
    monkeypatch.setattr(tldr, 'have_recent_cache', lambda *args: False)
    def unexpected(*args, **kwargs):
        pytest.fail('Cache-only mode must avoid network')
    monkeypatch.setattr(tldr, 'urlopen', unexpected)
    with pytest.raises(tldr.CacheNotExist):
        tldr.get_page_for_platform('git', 'linux', None, 'en', only_use_cache=True)
''', 'The successful download is a negative control for always using stale cache. Fresh-cache and cache-only paths independently forbid network use.',
     [('never-cache-download', 'original=m.get_page_for_platform\ndef broken(*args,**kwargs):\n writer=m.store_page_to_cache\n m.store_page_to_cache=lambda *args: None\n try: return original(*args,**kwargs)\n finally: m.store_page_to_cache=writer\nm.get_page_for_platform=broken'),
      ('ignore-cache-only', 'original=m.get_page_for_platform\ndef broken(command,platform,remote,language,only_use_cache=False,system_cache=False):\n return original(command,platform,remote,language,False,system_cache)\nm.get_page_for_platform=broken')])

task('tldr-python-client', 'platform-priority', 'tldr',
     'get_platform maps sys.platform prefixes: darwin to osx, win32 to windows, linux variants to linux, '
     'unknown platforms to linux. get_platform_list returns each supported platform once, with the current '
     'platform first and common included. The remaining order is unspecified.', r'''
import pytest
import tldr


@pytest.mark.parametrize('system,expected', [('darwin', 'osx'), ('win32', 'windows'),
                                             ('linux2', 'linux'), ('unknown-os', 'linux')])
def test_platform_mapping(monkeypatch, system, expected):
    monkeypatch.setattr(tldr.sys, 'platform', system)
    assert tldr.get_platform() == expected


def test_active_platform_first(monkeypatch):
    monkeypatch.setattr(tldr, 'get_platform', lambda: 'windows')
    platforms = tldr.get_platform_list()
    assert platforms[0] == 'windows'
    assert len(platforms) == len(set(platforms))
    assert set(platforms) == {'common', 'android', 'osx', 'freebsd', 'linux', 'netbsd', 'openbsd', 'sunos', 'windows'}
''', 'Platform cases include a fallback control. Membership and uniqueness cover the tail without imposing order from a set.',
     [('always-linux', "m.get_platform=lambda: 'linux'"),
      ('duplicate-active', 'original=m.get_platform_list\nm.get_platform_list=lambda: original()+[m.get_platform()]')])

task('posting', 'path-parameters', 'posting.urls',
     'extract_path_param_names(url) returns unique :name placeholders in path order, ignoring ::escaped tokens '
     'and query/fragment. substitute_path_params(url,params) replaces supplied path placeholders, retains unknown '
     'ones, unescapes :: to : in the path, and leaves query/fragment unchanged. Names start with letter or underscore.', r'''
from posting.urls import extract_path_param_names, substitute_path_params


def test_placeholder_names_and_negative_controls():
    url = 'https://example.test/:user/::literal/:item/:user?q=:ignored#x:ignored'
    assert extract_path_param_names(url) == ['user', 'item']
    assert extract_path_param_names('https://example.test/plain?q=:name') == []


def test_substitution_scope_and_missing_values():
    url = 'https://example.test/:user/::literal/:missing?q=:user#x:user'
    assert substitute_path_params(url, {'user': 'alice', 'literal': 'wrong'}) == (
        'https://example.test/alice/:literal/:missing?q=:user#x:user')
''', 'Escaped and query placeholders reject broad text replacement. A repeated name tests ordered uniqueness.',
     [('omit-deduplication', "m.extract_path_param_names=lambda url: [x.group(1) for x in m._PATH_PARAM_PATTERN.finditer(m.urlparse(url).path)]"),
      ('replace-query-too', "original=m.substitute_path_params\ndef broken(url,params):\n result=original(url,params)\n for key,value in params.items(): result=result.replace(':'+key,value)\n return result\nm.substitute_path_params=broken")])

task('posting', 'query-pair-merge', 'posting.urls',
     'extract_query_pairs(url) retains duplicate keys, blanks and ordering. merge_url_query_into_params(url, '
     'params) matches table (name,value,enabled) triples to URL occurrences in order. Nonempty table values win; '
     'empty table values use URL values; preserve disabled flags, unmatched URL rows (enabled=True), and '
     'unmatched table rows. Return URL with query removed, preserving path/fragment. With escape_dollars=True '
     'percent-encoded dollar signs decode to doubled dollars for later literal-template handling.', r'''
from posting.urls import extract_query_pairs, merge_url_query_into_params


def test_query_pairs_and_literal_dollars():
    assert extract_query_pairs('https://example.test/?a=1&a=&b=two+words') == [('a', '1'), ('a', ''), ('b', 'two words')]
    assert extract_query_pairs('https://example.test/?cost=%24x', escape_dollars=True) == [('cost', '$$x')]


def test_merge_by_occurrence_and_preserve_disabled_rows():
    params = [('a', '', False), ('a', 'override', True), ('tail', 'keep', False)]
    url, merged = merge_url_query_into_params('https://example.test/path?a=one&a=two&b=#frag', params)
    assert url == 'https://example.test/path#frag'
    assert merged == [('a', 'one', False), ('a', 'override', True), ('b', '', True), ('tail', 'keep', False)]
    assert params == [('a', '', False), ('a', 'override', True), ('tail', 'keep', False)]
''', 'Duplicate-key matching and disabled rows make dictionary collapse observable. The input list is checked for accidental mutation.',
     [('collapse-duplicates', 'original=m.extract_query_pairs\nm.extract_query_pairs=lambda url,**kwargs: list(dict(original(url,**kwargs)).items())'),
      ('enable-all-rows', 'original=m.merge_url_query_into_params\ndef broken(*args,**kwargs):\n url,rows=original(*args,**kwargs)\n return url,[(k,v,True) for k,v,e in rows]\nm.merge_url_query_into_params=broken')])

task('posting', 'request-filenames', 'posting.files',
     'is_valid_filename rejects empty/whitespace, native path separators, >255 characters, Windows device names '
     'with optional extension, dot-prefixed, dot-suffixed and double-dot names. Ordinary filenames are valid. '
     'get_unique_request_filename(name,directory) returns an unused .posting.yaml name; repeated collisions '
     'advance a two-digit -01/-02 suffix. It proposes a name without creating files. Test exact .posting.yaml '
     'collisions; mixed .yml extensions and numbered-input policy are outside this task.', r'''
import os
import pytest
from posting.files import is_valid_filename, get_unique_request_filename


@pytest.mark.parametrize('name', ['', '   ', 'CON.txt', '.hidden', 'end.', 'a..b', 'a' * 256, 'dir' + os.path.sep + 'file'])
def test_invalid_names(name):
    assert is_valid_filename(name) is False


def test_valid_names_and_collision_sequence(tmp_path):
    assert is_valid_filename('request-1.posting.yaml') is True
    name = 'request.posting.yaml'
    assert get_unique_request_filename(name, tmp_path) == name
    (tmp_path / name).touch()
    assert get_unique_request_filename(name, tmp_path) == 'request-01.posting.yaml'
    (tmp_path / 'request-01.posting.yaml').touch()
    assert get_unique_request_filename(name, tmp_path) == 'request-02.posting.yaml'
    assert {p.name for p in tmp_path.iterdir()} == {name, 'request-01.posting.yaml'}
''', 'Valid names prevent an always-reject validator. A second collision rejects implementations that always append -01 or create a file while proposing a name.',
     [('accept-all-names', 'm.is_valid_filename=lambda name: True'),
      ('ignore-collisions', 'm.get_unique_request_filename=lambda name,directory: name')])

task('posting', 'session-undo-redo', 'posting.session_variables',
     'SessionVariables starts with empty values. set(name,value) records an edit; revert(name) removes an '
     'override and returns True, or False if absent. undo()/redo() return the affected name, restoring prior '
     'override presence/value, or None when unavailable. A new editor edit clears redo. values is publicly '
     'readable; avoid private history inspection.', r'''
from posting.session_variables import SessionVariables


def test_revert_undo_redo_and_empty_history():
    state = SessionVariables()
    assert state.values == {}
    assert state.undo() is None
    assert state.redo() is None
    assert state.revert('missing') is False
    state.set('token', 'first')
    state.set('token', 'second')
    assert state.revert('token') is True
    assert state.values == {}
    assert state.undo() == 'token'
    assert state.values == {'token': 'second'}
    assert state.undo() == 'token'
    assert state.values == {'token': 'first'}
    assert state.redo() == 'token'
    assert state.values == {'token': 'second'}


def test_new_edit_invalidates_redo():
    state = SessionVariables()
    state.set('a', 'one')
    assert state.undo() == 'a'
    assert state.values == {}
    state.set('b', 'two')
    assert state.redo() is None
    assert state.values == {'b': 'two'}
''', 'Assertions cover state after each transition, not only returned names. A branched edit checks redo invalidation.',
     [('undo-no-op', 'm.SessionVariables.undo=lambda self: None'),
      ('retain-redo-on-edit', 'original=m.SessionVariables._record\ndef broken(self,name):\n redo=list(self._redo)\n original(self,name)\n self._redo=redo\nm.SessionVariables._record=broken')])

task('posting', 'session-history-limit', 'posting.session_variables',
     'SessionVariables retains the latest 50 editor edits. Direct script writes to values do not add history; '
     'a later editor edit snapshots that script value, including non-string types. Undoing all retained edits '
     'stops at the retained boundary. Use public set/undo/values only.', r'''
from posting.session_variables import SessionVariables


def test_fifty_edit_retention_boundary():
    state = SessionVariables()
    for index in range(55):
        state.set('key', str(index))
    for _ in range(50):
        assert state.undo() == 'key'
    assert state.values == {'key': '4'}
    assert state.undo() is None


def test_script_value_restored_without_type_coercion():
    state = SessionVariables()
    state.values['number'] = 42
    assert state.undo() is None
    state.set('number', 'editor text')
    assert state.undo() == 'number'
    assert state.values['number'] == 42
    assert type(state.values['number']) is int
''', 'Fifty undos distinguish a bounded history from an unbounded one. Direct script writes test a different provenance path and preserve value type.',
     [('unbounded-history', 'def broken(self,name):\n self._history.append(self._snapshot(name))\n self._redo.clear()\nm.SessionVariables._record=broken'),
      ('stringify-restored-values', 'original=m.SessionVariables._restore\ndef broken(self,change):\n name=original(self,change)\n if name in self.values: self.values[name]=str(self.values[name])\n return name\nm.SessionVariables._restore=broken')])

task('ddgr', 'unicode-safe-urls', 'ddgr',
     'make_safe_url(url) converts international domains to IDNA ASCII and percent-encodes Unicode/space '
     'in path, query, fragment and credentials. Preserve query = and & separators and explicit ports. '
     'Already safe ASCII URLs remain unchanged. IPv6, already-percent-encoded data and invalid ports are outside scope.', r'''
from ddgr import make_safe_url


def test_ascii_url_unchanged():
    url = 'https://example.test:8443/path?q=one&x=2#part'
    assert make_safe_url(url) == url


def test_unicode_domain_path_and_query():
    assert make_safe_url('https://m\u00fcnich.example/caf\u00e9?q=two words&x=\u00e7#r\u00e9sum\u00e9') == (
        'https://xn--mnich-kva.example/caf%C3%A9?q=two%20words&x=%C3%A7#r%C3%A9sum%C3%A9')


def test_credentials_and_port():
    assert make_safe_url('https://user name:p\u00e4ss@example.test:8443/a b') == (
        'https://user%20name:p%C3%A4ss@example.test:8443/a%20b')
''', 'ASCII is a preservation control. Separate Unicode domain and credential examples catch partial encoders without browser interaction.',
     [('identity-url', 'm.make_safe_url=lambda url: url'),
      ('drop-port', "original=m.make_safe_url\nm.make_safe_url=lambda url: original(url).replace(':8443','')")])

task('ddgr', 'search-pagination', 'ddgr',
     'DdgUrl(duration="",keywords=[...]) exposes query() dict keys page and curindex. Initially page=0, curindex=1. '
     'update_num(n) records the most recent result count; next_page increments page and advances positive '
     'curindex by that count. prev_page decrements page and negates a positive index; first_page resets '
     'page=0, curindex=1. prev_page or first_page at page zero raises ValueError. Do not inspect private attributes.', r'''
import pytest
from ddgr import DdgUrl


def test_pagination_transitions_and_reset():
    url = DdgUrl(duration='', keywords=['python'])
    assert (url.query()['page'], url.query()['curindex']) == (0, 1)
    url.update_num(10)
    url.next_page()
    assert (url.query()['page'], url.query()['curindex']) == (1, 11)
    url.next_page()
    assert (url.query()['page'], url.query()['curindex']) == (2, 21)
    url.prev_page()
    assert (url.query()['page'], url.query()['curindex']) == (1, -21)
    url.first_page()
    assert (url.query()['page'], url.query()['curindex']) == (0, 1)
    assert url.query()['q'] == 'python'


def test_first_page_boundaries():
    url = DdgUrl(duration='')
    with pytest.raises(ValueError):
        url.prev_page()
    with pytest.raises(ValueError):
        url.first_page()
    assert url.query()['page'] == 0
''', 'A successful navigation sequence prevents always-raise behavior. Boundary failures and reset assertions cover both ends of the state machine.',
     [('next-no-op', 'm.DdgUrl.next_page=lambda self: None'),
      ('allow-negative-page', 'def broken(self): self._page-=1\nm.DdgUrl.prev_page=broken')])

task('ddgr', 'result-serialization', 'ddgr',
     'Result(index,title,url,abstract,metadata=None).jsonizable_object() returns exactly title,url,abstract '
     'plus metadata when nonempty; index is omitted. urltable() maps the stringified index to URL. '
     'Serialization preserves Unicode and is JSON serializable; no rendering or browser opening is needed.', r'''
import json
from ddgr import Result


def test_plain_result_and_url_lookup():
    result = Result(3, 'caf\u00e9', 'https://example.test', 'summary')
    expected = {'title': 'caf\u00e9', 'url': 'https://example.test', 'abstract': 'summary'}
    assert result.jsonizable_object() == expected
    assert json.loads(json.dumps(result.jsonizable_object())) == expected
    assert result.urltable() == {'3': 'https://example.test'}


def test_optional_metadata():
    assert Result('4', 'Title', 'url', 'body', 'publisher').jsonizable_object() == {
        'title': 'Title', 'url': 'url', 'abstract': 'body', 'metadata': 'publisher'}
    assert 'metadata' not in Result(5, 'Title', 'url', 'body', '').jsonizable_object()
''', 'Exact key sets prevent index leakage and unconditional metadata fields. Round-trip JSON checks serialization without testing presentation.',
     [('drop-metadata', 'original=m.Result.jsonizable_object\ndef broken(self):\n result=original(self)\n result.pop("metadata",None)\n return result\nm.Result.jsonizable_object=broken'),
      ('numeric-index', 'm.Result.urltable=lambda self: {int(self.index):self.url}')])

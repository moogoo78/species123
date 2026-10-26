import os
import sqlite3
from pathlib import Path

from flask import g

DATA = Path(os.environ.get('SPECIES123_DATA', Path(__file__).resolve().parent.parent / 'data'))
DB_PATH = DATA / 'species123.sqlite'
CACHE_PATH = DATA / 'cache.sqlite'


def get_db():
    """Read-only connection to the imported TaiCOL snapshot (None if not imported yet)."""
    if 'db' not in g:
        if not DB_PATH.exists():
            return None
        con = sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)
        con.row_factory = sqlite3.Row
        g.db = con
    return g.db


def get_cache():
    """Writable side database for API responses (literature, photos, GBIF matches, TBIA specimens)."""
    if 'cache' not in g:
        con = sqlite3.connect(CACHE_PATH, timeout=5)
        con.execute('PRAGMA journal_mode=WAL')  # concurrent requests read while one writes
        con.execute('CREATE TABLE IF NOT EXISTS ref_cache (name_id INTEGER PRIMARY KEY, body TEXT, fetched_at REAL)')
        con.execute('CREATE TABLE IF NOT EXISTS photo_cache (name TEXT PRIMARY KEY, body TEXT, fetched_at REAL)')
        con.execute('CREATE TABLE IF NOT EXISTS gbif_cache (name TEXT PRIMARY KEY, body TEXT, fetched_at REAL)')
        con.execute('CREATE TABLE IF NOT EXISTS wiki_cache (name TEXT PRIMARY KEY, body TEXT, fetched_at REAL)')
        con.execute('CREATE TABLE IF NOT EXISTS thumb_cache (inat_id TEXT PRIMARY KEY, body TEXT, fetched_at REAL)')
        con.execute('CREATE TABLE IF NOT EXISTS tbia_cache (taxon_id TEXT PRIMARY KEY, body TEXT, fetched_at REAL)')
        g.cache = con
    return g.cache


def close_db(exc=None):
    for key in ('db', 'cache'):
        con = g.pop(key, None)
        if con is not None:
            con.close()

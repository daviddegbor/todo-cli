
import subprocess, sys
from pathlib import Path
import pytest

SCRIPT = str(Path(__file__).resolve().parent.parent / 'checklist.py')

def run(args, env=None):
    proc = subprocess.Popen([sys.executable, SCRIPT] + args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            env=env)
    out, err = proc.communicate()
    return proc.returncode, out.decode('utf-8'), err.decode('utf-8')

def test_list_empty(tmp_path):
    code, out, err = run(['--file', str(tmp_path / 'list.json')])
    assert code == 0
    assert 'Checklist is empty.' in out
    assert err == ''

def test_add_and_list(tmp_path):
    store = tmp_path / 'list.json'
    code, out, err = run(['--file', str(store), 'add', 'Buy', 'milk'])
    assert code == 0
    assert "Added: 'Buy milk'" in out
    assert '1. Buy milk' in out
    # Persisted listing
    code, out, err = run(['--file', str(store)])
    assert '1. Buy milk' in out

def test_rm(tmp_path):
    store = tmp_path / 'list.json'
    run(['--file', str(store), 'add', 'A'])
    run(['--file', str(store), 'add', 'B'])
    code, out, err = run(['--file', str(store), 'rm', '1'])
    assert code == 0
    assert "Removed: 'A' (was #1)" in out
    assert '1. B' in out

def test_mv(tmp_path):
    store = tmp_path / 'list.json'
    run(['--file', str(store), 'add', 'A'])
    run(['--file', str(store), 'add', 'B'])
    run(['--file', str(store), 'add', 'C'])
    code, out, err = run(['--file', str(store), 'mv', '3', '1'])
    assert code == 0
    assert "Moved: 'C' from #3 to #1" in out
    code, out, err = run(['--file', str(store)])
    assert '1. C' in out and '2. A' in out and '3. B' in out

def test_help_prints_docstring():
    code, out, err = run(['--help'])
    assert code == 0
    assert 'Simple command-line checklist app.' in out

def test_errors(tmp_path):
    store = tmp_path / 'list.json'
    code, out, err = run(['--file', str(store), 'rm'])
    assert code == 2 and "Error: 'rm' requires exactly one index." in err
    code, out, err = run(['--file', str(store), 'mv', '1'])
    assert code == 2 and "Error: 'mv' requires src_idx and dst_idx." in err
    run(['--file', str(store), 'add', 'X'])
    code, out, err = run(['--file', str(store), 'rm', '2'])
    assert code == 2 and 'Error: item_idx out of range.' in err

@pytest.mark.xfail(reason='update not implemented yet')
def test_update_placeholder(tmp_path):
    store = tmp_path / 'list.json'
    run(['--file', str(store), 'add', 'Old'])
    code, out, err = run(['--file', str(store), 'update', '1', 'New'])
    assert code == 0

@pytest.mark.xfail(reason='swap not implemented yet')
def test_swap_placeholder(tmp_path):
    store = tmp_path / 'list.json'
    run(['--file', str(store), 'add', 'A'])
    run(['--file', str(store), 'add', 'B'])
    code, out, err = run(['--file', str(store), 'swap', '1', '2'])
    assert code == 0

@pytest.mark.xfail(reason='prio not implemented yet')
def test_prio_placeholder(tmp_path):
    store = tmp_path / 'list.json'
    run(['--file', str(store), 'add', 'Task'])
    code, out, err = run(['--file', str(store), 'prio', '1', 'high'])
    assert code == 0

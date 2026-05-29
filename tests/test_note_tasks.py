"""extract_tasks_with_lines + set_task_state precise write-back."""
from markdown_parser import MarkdownParser

SAMPLE = "intro\n- [ ] alpha\n- [x] beta\ntext\n- [ ] alpha\n"


def test_extract_with_lines():
    mp = MarkdownParser()
    tasks = mp.extract_tasks_with_lines(SAMPLE)
    assert tasks == [(1, False, "alpha"), (2, True, "beta"), (4, False, "alpha")]


def test_set_task_state_targets_exact_line():
    mp = MarkdownParser()
    # complete the FIRST 'alpha' (line 1), not the duplicate on line 4
    out = mp.set_task_state(SAMPLE, 1, True)
    lines = out.split('\n')
    assert lines[1] == "- [x] alpha"
    assert lines[4] == "- [ ] alpha"  # untouched duplicate


def test_set_task_state_uncheck():
    mp = MarkdownParser()
    out = mp.set_task_state(SAMPLE, 2, False)
    assert out.split('\n')[2] == "- [ ] beta"


def test_set_task_state_noop_on_nontask_line():
    mp = MarkdownParser()
    assert mp.set_task_state(SAMPLE, 0, True) == SAMPLE

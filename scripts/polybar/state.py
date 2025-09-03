import inspect
import os

def get_statefile_name():
    """
    Determine the filename of the calling script file and generate a statefile name.
    """
    caller_frame_info = inspect.stack()[3]
    caller_filepath = caller_frame_info.filename
    caller_filepath_basename = os.path.splitext(
        os.path.basename(caller_filepath)
    )[0]

    return os.path.join(
        '/tmp',
        f'{os.path.basename(caller_filepath_basename)}-state'
    )

def read_state():
    """
    Read state from file, default to 0 if missing or invalid.
    """
    if os.path.exists(get_statefile_name()):
        try:
            with open(get_statefile_name(), "r") as f:
                return int(f.read().strip())
        except ValueError:
            return 0
    return 0

def write_state(state):
    """
    Write state to file.
    """
    with open(get_statefile_name(), "w") as f:
        f.write(str(state))

def next_state(n, backward=False):
    """
    Cycle through states 0..n-1 forward or backward.
    """
    state = read_state()
    if backward:
        state = (state - 1) % n
    else:
        state = (state + 1) % n
    write_state(state)
    return state

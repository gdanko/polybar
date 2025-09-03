import inspect
import os

def read_state(statefile_name: str=''):
    """
    Read state from file, default to 0 if missing or invalid.
    """
    if os.path.exists(statefile_name):
        try:
            with open(statefile_name, "r") as f:
                return int(f.read().strip())
        except ValueError:
            write_state(statefile_name=statefile_name, state_number=0)
            return 0
    write_state(statefile_name=statefile_name, state_number=0)
    return 0

def write_state(statefile_name: str='', state_number: int=0):
    """
    Write state to file.
    """
    with open(statefile_name, 'w') as f:
        f.write(str(state_number))

def next_state(statefile_name: str='', mode_count: int=0, backward: bool=False):
    """
    Cycle through states 0..n-1 forward or backward.
    """
    state_number = read_state(statefile_name=statefile_name)

    if backward:
        state_number = (state_number - 1) % mode_count
    else:
        state_number = (state_number + 1) % mode_count

    write_state(statefile_name=statefile_name, state_number=state_number)
    return state_number

from .core import *
import colorama
colorama.init()

###################
###################
#  Terminal mode  #
###################
###################


def _print_states(states):
    print('UNLOCK_SEQUENCES:')
    for reward_level, state in enumerate(states, start=1):
        if state.failed:
            print(colorama.Fore.RED + ' '.join(state.seq) + f' REWARD: v{reward_level} (FAILED)' + colorama.Style.RESET_ALL)
        elif state.success:
            print(colorama.Fore.GREEN + ' '.join(state.seq) + f' REWARD: v{reward_level} (COMPLETE)' + colorama.Style.RESET_ALL)
        else:
            for index, combo in enumerate(state.seq, start=1):
                if index <= state._solved_count:
                    print(colorama.Fore.GREEN + combo, end=' ')
                else:
                    print(colorama.Style.RESET_ALL + colorama.Style.BRIGHT + combo, end=' ')
            print(colorama.Style.RESET_ALL)


def _color_for_tiles(tiles: Sequence[Tile], node: Node):
    for t in tiles:
        if t in node.buffer:
            yield colorama.Fore.CYAN + t.val + colorama.Style.RESET_ALL
        elif t in node.choices:
            yield colorama.Style.BRIGHT + colorama.Fore.YELLOW + t.val + colorama.Style.RESET_ALL
        else:
            yield t.val


def _print_matrix(node):
    # print row values
    for row in node.grid.rows:
        print("| ", end='')
        print(*_color_for_tiles(row, node), sep=' | ', end=" |\n")
    # print board separator
    seps = ["_"] * len(node.grid.columns)
    print("__", end='')
    print(*seps, sep='___', end='__\n')

def _print_buffer(buff, max_size):
    print('CURRENT BUFFER:')
    for i in range(1, max_size+1):
        if i <= len(buff.state):
            print(colorama.Fore.CYAN + str(buff.state[i-1]) + colorama.Style.RESET_ALL, end=' ')
        else:
            print([], end=' ')
    print()


def _validate_node(node: Node) -> bool:
    if node.is_complete:
        return True
    children = node.children
    for child in children:
        if child.is_complete:
            return True
    else:
        return any(_validate_node(child) for child in children)

def play(grid, seq, max_size=8):
    node = Node(grid=Grid(grid), unlock_sequences=seq, buffer_state=Buffer(), max_size=max_size)
    if _validate_node(node) is not True:
        raise ValueError("Invalid grid no winning moves!~")
    while node.children:
        _print_states(node.sequence_states)
        _print_matrix(node)
        _print_buffer(node.buffer, max_size=max_size)

        choices = node.children
        for index, n in enumerate(choices):
            print(index, n.last_selection)
        choice = int(input('Choose one: '))
        # TODO: validate input
        node = choices[choice]
        if node.is_complete:
            _print_states(node.sequence_states)
            _print_matrix(node)
            _print_buffer(node.buffer, max_size=max_size)
            print("YOU WIN!")
            return
    print('You suck :(')

def _solve(node: Node):
    solutions = []
    if node.is_complete:
        solutions.append(node.buffer.state)
    for child in node.children:
        solutions.extend(_solve(child))
    return solutions


def solve_grid(grid, seq, max_size):
    node = Node(grid=Grid(grid), unlock_sequences=seq, buffer_state=Buffer(), max_size=max_size)
    for t in _solve(node)[0]:
        print(t.val, (t.col, t.row))


if __name__ == '__main__':
    # solve_grid(EXAMPLE_MATRIX, EXAMPLE_UNLOCK_SEQUENCES, 8)
    play(EXAMPLE_MATRIX, EXAMPLE_UNLOCK_SEQUENCES)

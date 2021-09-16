from typing import Sequence, Literal, Union, Optional
from collections import Counter

EXAMPLE_MATRIX = [
    ["1C", "E9", "1C", "55", "1C"],
    ["E9", "55", "1C", "1C", "BD"],
    ["55", "BD", "1C", "BD", "55"],
    ["55", "1C", "55", "55", "1C"],
    ["E9", "1C", "1C", "1C", "55"],
]

EXAMPLE_UNLOCK_SEQUENCES = (
    ('55', '1C',),
    ('1C', '1C', 'E9'),
    ('BD', 'E9', '55'),
)


class Tile:
    __slots__ = ['val', 'row', 'col']

    def __init__(self, val: str, row: int, col: int):
        self.val = val
        self.row = row
        self.col = col

    def __eq__(self, other: Union['Tile']):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash((self.row, self.col))

    def __repr__(self):
        return f'{self.__class__.__name__}(val={self.val!r}, row={self.row!r}, col={self.col!r})'

    def __str__(self):
        return str(self.val)


class Buffer:
    __slots__ = ['state', '_buff_set']

    def __init__(self, state: Optional[Sequence[Tile]] = None):
        self.state = tuple(state) if state is not None else tuple()
        self._buff_set = set(self.state)

    def __contains__(self, item):
        return item in self._buff_set

    def add(self, other: Tile):
        return Buffer(self.state + (other,))

    def __iter__(self):
        for i in self.state:
            yield i

    def __getitem__(self, item):
        return self.state[item]

    def __len__(self):
        return len(self.state)

    def __repr__(self):
        return f'{self.__class__.__name__}(state={self.state!r})'


class Grid:
    __slots__ = ['rows', 'columns']

    def __init__(self, matrix):
        self.rows = []
        for row_index, row in enumerate(matrix):
            r = []
            for col_index, val in enumerate(row):
                tile = Tile(val, row_index, col_index)
                r.append(tile)
            self.rows.append(r)
        self.columns = [[] for _ in range(len(self.rows))]
        for index, col in enumerate(self.columns):
            for row in self.rows:
                for tile in row:
                    if tile.col == index:
                        col.append(tile)

    def __getitem__(self, item):
        return self.rows[item]

    def __repr__(self):
        return repr(self.rows)

    def get_col(self, index):
        return self.columns[index]

    def get_row(self, index):
        return self.rows[index]


class SequenceState:
    def __init__(self, seq: Sequence[str], buff: Buffer, max_size: int):
        self.seq = seq
        self.failed = False
        self.success = False
        self._solved_count = 0
        first = seq[0]
        for index, tile in enumerate(buff, start=0):
            if tile.val == first:
                self._solved_count = 1
                break
        else:
            return
        for index, tile in enumerate(buff[index + 1 :], start=index):
            if tile.val == self.seq[self._solved_count]:
                self._solved_count += 1
                if self._solved_count == len(seq):
                    self.success = True
                    return
            elif max_size < self._solved_count + self.remaining:
                self.failed = True
                return

    @property
    def remaining(self):
        return len(self) - self._solved_count

    def __len__(self):
        return len(self.seq)


SelectionType = Union[Literal['row', 'col'], str]


class Node:
    def __init__(
        self,
        grid: Grid,
        buffer_state: Buffer,
        max_size: int,
        unlock_sequences: Sequence[Sequence[str]],
        selection_type: SelectionType = 'row',
    ):

        self.sequence_states = [SequenceState(seq, buffer_state, max_size=max_size) for seq in unlock_sequences]

        self._children = None
        self._choices = None
        self.buffer = buffer_state
        if buffer_state:
            self.last_selection = buffer_state[-1]
        else:
            self.last_selection = None
        self.unlock_sequences = unlock_sequences
        self.max_size = max_size
        self.selection_type = selection_type
        if selection_type == 'row':
            self.next_selection_type = 'col'
        else:
            self.next_selection_type = 'row'
        self.grid = grid
        self.children

    @property
    def children(self) -> Sequence['Node']:
        if self._children is not None:
            return self._children
        children = []
        for candidate in self.next_candidates or []:
            node = Node(
                grid=self.grid,
                buffer_state=self.buffer.add(candidate),
                max_size=self.max_size,
                unlock_sequences=self.unlock_sequences,
                selection_type=self.next_selection_type,
            )
            children.append(node)
        self._children = children
        return children

    @property
    def sequence_index(self):
        return len(self.buffer) + 1

    @property
    def next_unlocks(self) -> Counter:
        """
        Returns the counts of next values we're looking for at the current index in each unlock sequence

        For example, on the first round of the ``EXAMPLE_UNLOCK_SEQUENCES``, this would return:

        {
          '55': 1,
          '1C': 1,
          'BD': 1
        }

        """
        unlock_tiles = Counter()
        unlock_index = self.sequence_index
        for seq in self.unlock_sequences:
            if unlock_index > len(seq) - 1:
                continue
            unlock_tiles[seq[unlock_index]] += 1
        return unlock_tiles

    @property
    def prime_candidates(self) -> Union[None, Sequence[Tile]]:
        """
        Candidates who are included in a next unlock, ordered by the number of unlocks the choice would unlock
        """
        unlock_counts = self.next_unlocks
        if not unlock_counts:
            return None
        choices = self.choices
        return sorted([c for c in choices if c in unlock_counts], key=unlock_counts.get, reverse=True)

    @property
    def choices(self) -> Sequence[Tile]:
        """
        Returns the possible tiles we have to choose from, filtering out any previously selected tiles
        """
        if self._choices is not None:
            return self._choices
        last_selection = self.last_selection
        if not last_selection:
            return self.grid[0]
        if self.selection_type == 'row':
            elements = self.grid.get_row(last_selection.row)
        else:
            elements = self.grid.get_col(last_selection.col)
        choices = [i for i in elements if i not in self.buffer]
        self._choices = choices
        return choices

    @property
    def next_candidates(self) -> Union[None, Sequence[Tile]]:
        """
        Like ``choices``, but try to optimize things
        """
        curr_size = len(self.buffer)
        max_size = self.max_size
        if curr_size == max_size:
            return None
        if curr_size == max_size - 1:
            return self.prime_candidates or None
        return self.choices

    @property
    def is_complete(self):
        return all(state.success for state in self.sequence_states)

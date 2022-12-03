import argparse
import pycosat
import datetime

class Base(object):

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def get_cell_edges(self, cell_id):
        assert 0 <= cell_id < (self.height * self.width)

        cell_row = cell_id // self.width
        cell_col = cell_id % self.width
        num_horizontal = self.height * (self.width + 1)
        # Cạnh ngang
        upper_edge = cell_id
        lower_edge = upper_edge + self.width
        # Cạnh dọc
        left_edge = num_horizontal + ((cell_row * (self.width + 1)) + cell_col)
        right_edge = left_edge + 1
        return [upper_edge, lower_edge, left_edge, right_edge]

    def get_corner_edges(self, corner_id):
        assert 0 <= corner_id < (self.width + 1) * (self.height + 1)
        col = corner_id % (self.width + 1)
        row = corner_id // (self.width + 1)
        left_edge = None
        right_edge = None
        up_edge = None
        down_edge = None
        H = self.width * (self.height + 1)
        if col < self.width:
            right_edge = (self.width * row) + col
        if col > 0:
            left_edge = (self.width * row) + col - 1
        if row > 0:
            up_edge = H + corner_id - (self.width + 1)
        if row < self.height:
            down_edge = H + corner_id
        edges = [edge
                 for edge in [left_edge, right_edge, up_edge, down_edge]
                 if edge is not None]
        return edges

    def get_adjacent_edges(self, edge_id):
        vert_edges = self.height * (self.width + 1)
        hori_edges = self.width * (self.height + 1)
        num_edges = vert_edges + hori_edges
        num_corners = (self.width + 1) * (self.height + 1)
        assert 0 <= edge_id < num_edges
        a, b = [corner_id
                for corner_id in range(num_corners)
                if edge_id in self.get_corner_edges(corner_id)]
        edges_a = [edge
                   for edge in self.get_corner_edges(a)
                   if edge != edge_id]
        edges_b = [edge
                   for edge in self.get_corner_edges(b)
                   if edge != edge_id]
        return edges_a + edges_b


class CellConstraints(Base):

    def __init__(self, cells, width, height):
        super().__init__(width, height)
        self.cells = cells
        self.height = height
        self.width = width
        self.constraints = []

    def zero(self, e1, e2, e3, e4):
        return [[-e1], [-e2], [-e3], [-e4]]

    def one(self, e1, e2, e3, e4):
        return [
            [-e1, -e2], [-e1, -e3], [-e1, -e4],
            [-e2, -e3], [-e2, -e4], [-e3, -e4],
            [e1, e2, e3, e4]
        ]

    def two(self, e1, e2, e3, e4):
        return [
            [e2, e3, e4], [e1, e3, e4],
            [e1, e2, e4], [e1, e2, e3],
            [-e2, -e3, -e4], [-e1, -e3, -e4],
            [-e1, -e2, -e4], [-e1, -e2, -e3]
        ]

    def three(self, e1, e2, e3, e4):
        return [
            [e1, e2], [e1, e3], [e1, e4],
            [e2, e3], [e2, e4], [e3, e4],
            [-e1, -e2, -e3, -e4]
        ]

    def solve(self):
        cnf_builder = [self.zero, self.one, self.two, self.three]
        cell_id = -1
        for row in range(self.height):
            for col in range(self.width):
                cell_id += 1
                cell_value = self.cells[row][col]
                assert cell_value in [None, 0, 1, 2, 3]
                if cell_value is None:
                    pass
                else:
                    assert 0 <= cell_value <= 3
                    edges = [1+e for e in self.get_cell_edges(cell_id)]
                    clauses = cnf_builder[cell_value](*edges)
                    self.constraints += clauses


class LoopConstraints(Base):

    def __init__(self, cells, width, height):
        super().__init__(width, height)
        self.cells = cells
        self.width = width
        self.height = height
        self.constraints = []

    def two(self, e1, e2):
        return [[-e1, e2], [e1, -e2]]

    def three(self, e1, e2, e3):
        return [
            [-e1, -e2, -e3],
            [-e1, e2, e3],
            [e1, -e2, e3],
            [e1, e2, -e3]
        ]

    def four(self, e1, e2, e3, e4):
        return [
            [-e1, e2, e3, e4],
            [e1, -e2, e3, e4],
            [e1, e2, -e3, e4],
            [e1, e2, e3, -e4],
            [-e1, -e2, -e3],
            [-e1, -e2, -e4],
            [-e1, -e3, -e4],
            [-e2, -e3, -e4]
        ]

    def solve(self):
        num_corners = (self.width + 1) * (self.height + 1)
        constraint_fn = [None, None, self.two, self.three, self.four]
        for corner_id in range(num_corners):
            edges = [1+e for e in self.get_corner_edges(corner_id)]
            clauses = constraint_fn[len(edges)](*edges)
            self.constraints += clauses


class Drawer(object):

    def __init__(self, cells, width, height):
        self.cells = cells
        self.width = width
        self.height = height
        self.num_row = 4 * (self.height + 1) + 1
        self.num_col = 4 * (self.width + 1) + 1
        self.g = g = [[' ' for cols in range(
            self.num_col)] for rows in range(self.num_row)]

    def horizontal_edge(self, edge):
        col_f = edge % self.width
        row_l = edge // self.width
        y = 4 * row_l
        x1 = 4 * col_f
        x2 = 4 * (col_f + 1)
        for x in range(x1, x2+1):
            self.g[y][x] = '*'

    def vertical_edge(self, edge):
        row_f = edge // (self.width + 1)
        col_l = edge % (self.width + 1)
        y1 = 4 * row_f
        y2 = 4 * (row_f + 1)
        x = 4 * col_l
        for y in range(y1, y2+1):
            self.g[y][x] = '*'

    def draw_numbers(self):
        for row_index, row in enumerate(self.cells):
            for col_index, val in enumerate(row):
                if val is not None:
                    y = 4 * row_index + 2
                    x = 4 * col_index + 2
                    self.g[y][x] = str(val)

    def draw(self, solution):
        self.draw_numbers()
        horizontal_limit = self.height * (self.width + 1)
        horizontals = [e - 1
                       for e in solution
                       if e <= horizontal_limit]
        verticals = [e - horizontal_limit - 1
                     for e in solution
                     if e > horizontal_limit]
        for h_edge in horizontals:
            self.horizontal_edge(edge=h_edge)
        for v_edge in verticals:
            self.vertical_edge(edge=v_edge)
        gs = '\n'.join([''.join(g_row) for g_row in self.g])
        print(gs)


class SlitherLink(Base):

    def __init__(self, input_filename):
        if input_filename is not None:
            self.init(filename=input_filename)
        else:
            raise Exception('Input file is empty')

    def init(self, filename):
        with open(filename) as fin:
            self.cells = [[None if char == '.' else int(char)
                          for char in line.strip()]
                          for line in fin]
        self.width = len(self.cells[0])
        self.height = len(self.cells)
        self.filename = filename
        self.loop_constraints = LoopConstraints(
            self.cells, self.width, self.height)
        self.cell_constraints = CellConstraints(
            self.cells, self.width, self.height)
        self.drawer = Drawer(self.cells, self.width, self.height)

    def sat_solver(self):
        constraints = self.cell_constraints.constraints + self.loop_constraints.constraints
        start_time = datetime.datetime.now()
        for solution in pycosat.itersolve(constraints):
            print("Processing...")
            test_solution = [edge for edge in solution if edge > 0]
            result = self.validate(test_solution)
            if result:
                self.solution = test_solution
                break
        delta_time = datetime.datetime.now() - start_time
        print(
            f'{self.filename} __ Process time: {delta_time} __ Clauses: {len(constraints)}')

    def solve(self):
        self.cell_constraints.solve()
        self.loop_constraints.solve()
        self.sat_solver()
        self.drawer.draw(self.solution)

    def validate(self, solution):
        """Xác thực chỉ có một chu trình duy nhất"""
        if solution is []:
            return False
        solution = [edge - 1 for edge in solution]
        far_edges = solution[1:]
        start = [solution[0]]
        while far_edges != []:
            nbrs = [nbr
                    for edge in start
                    for nbr in self.get_adjacent_edges(edge)
                    if nbr in far_edges]
            if nbrs == [] and far_edges != []:
                return False
            far_edges = [edge for edge in far_edges if edge not in nbrs]
            start = nbrs
        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='Tệp tin đầu vào')
    args = parser.parse_args()
    slither = SlitherLink(args.file)
    slither.solve()

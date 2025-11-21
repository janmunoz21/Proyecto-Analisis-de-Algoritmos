from collections import deque

class NumberlinkSolver:
    def __init__(self, filepath):
        self.rows = 0
        self.cols = 0
        self.grid = []
        self.paths = {}
        self.load_board(filepath)

    def load_board(self, filepath):
        with open(filepath, 'r') as f:
            linea_dim = f.readline().split()
            if not linea_dim or len(linea_dim) != 2:
                raise ValueError("Dimensiones inválidas o archivo vacío.")

            self.rows = int(linea_dim[0])
            self.cols = int(linea_dim[1])
            raw_lines = f.readlines()

            self.grid = []
            self.paths = {}

            for r in range(self.rows):
                row_data = []
                line_content = raw_lines[r].rstrip('\n').ljust(self.cols, ' ')
                for c in range(self.cols):
                    ch = line_content[c]
                    row_data.append(ch)
                    if ch != ' ':
                        if ch not in self.paths:
                            self.paths[ch] = []
                        self.paths[ch].append((r, c))
                self.grid.append(row_data)

        for label, coords in self.paths.items():
            if len(coords) != 2:
                raise ValueError(
                    f"Etiqueta '{label}' incompleta o con más de dos puntos de conexión."
                )

    def _is_board_full(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == ' ':
                    return False
        return True

    def _check_connectivity(self):
        """
        Comprueba que todas las celdas vacías estén en una sola región conectada.
        """
        visited = [[False]*self.cols for _ in range(self.rows)]
        start = None
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == ' ':
                    start = (r, c)
                    break
            if start:
                break

        if not start:
            return True

        queue = deque([start])
        visited[start[0]][start[1]] = True

        while queue:
            r, c = queue.popleft()
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if not visited[nr][nc] and self.grid[nr][nc] == ' ':
                        visited[nr][nc] = True
                        queue.append((nr,nc))

        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == ' ' and not visited[r][c]:
                    return False
        return True

    def solve(self, callback=None):
        """
        Interfaz pública: intenta resolver el tablero. Si retorna True, la grid queda
        con la solución. El callback (si se pasa) se llama como callback(r,c,text,color_code)
        cada vez que se coloca/quita una celda intermedia.
        """
        tasks = [(label, pts[0], pts[1]) for label, pts in self.paths.items()]
        return self._backtrack_dynamic(tasks, callback)

    # Generador de caminos (DFS). Devuelve lista de caminos (cada uno es lista de celdas)
    # limit controla la explosión combinatoria
    def _generate_paths(self, start, end, label, limit=3000):
        paths = []

        def dfs(current, path, visited_local):
            if len(paths) >= limit:
                return
            if current == end:
                paths.append(path[:])
                return

            r, c = current
            # expandir en orden consistente
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r + dr, c + dc
                pos = (nr, nc)
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    cell = self.grid[nr][nc]
                    if pos in visited_local:
                        continue
                    # solo se permite avanzar a celdas vacías o al objetivo final
                    if pos != end and cell != ' ':
                        continue
                    visited_local.add(pos)
                    path.append(pos)
                    dfs(pos, path, visited_local)
                    path.pop()
                    visited_local.remove(pos)

        dfs(start, [start], set([start]))
        return paths

    # Backtracking DINÁMICO:
    def _backtrack_dynamic(self, remaining_tasks, callback):
        if not remaining_tasks:
            return self._is_board_full()

        # calcular (n_paths, index, paths_list) para cada tarea
        candidates = []
        for i, (label, start, end) in enumerate(remaining_tasks):
            paths = self._generate_paths(start, end, label, limit=2000)
            candidates.append((len(paths), i, paths))

        # ordenar por pocos caminos primero
        candidates.sort(key=lambda x: x[0])

        # probar cada tarea en orden de más restringida a menos
        for npaths, idx, paths in candidates:
            label, start, end = remaining_tasks[idx]

            # si no hay caminos posibles, esta rama falla rápido
            if npaths == 0:
                continue

            # ordenar rutas por longitud (probar cortas primero)
            paths.sort(key=len)

            for path in paths:
                # comprobar si la ruta choque con celdas ocupadas
                placed = []
                conflict = False
                for (r, c) in path:
                    if (r, c) == start or (r, c) == end:
                        continue
                    if self.grid[r][c] != ' ':
                        conflict = True
                        break
                if conflict:
                    continue

                # colocar la ruta (solo las intermedias)
                for (r, c) in path:
                    if (r, c) not in (start, end):
                        self.grid[r][c] = label
                        placed.append((r, c))
                        if callback:
                            callback(r, c, label, color_code=label)

                # podar: si la conectividad de espacios libres queda rota, revertir
                if not self._check_connectivity():
                    for (r, c) in placed:
                        self.grid[r][c] = ' '
                        if callback:
                            callback(r, c, ' ', color_code=None)
                    continue

                # recursión con la tarea actual removida
                next_tasks = remaining_tasks[:idx] + remaining_tasks[idx+1:]
                if self._backtrack_dynamic(next_tasks, callback):
                    return True

                # revertir la colocación
                for (r, c) in placed:
                    self.grid[r][c] = ' '
                    if callback:
                        callback(r, c, ' ', color_code=None)

        return False

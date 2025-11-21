import tkinter as tk
from tkinter import messagebox, filedialog
from solver import NumberlinkSolver


class NumberlinkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Numberlink Solver - Proyecto 2025")
        self.cell_size = 60
        self.solver = None
        self.colors = {}

        self.top_frame = tk.Frame(root)
        self.top_frame.pack(pady=10)

        self.btn_load = tk.Button(
            self.top_frame,
            text="Cargar Archivo",
            command=self.load_file
        )
        self.btn_load.pack(side=tk.LEFT, padx=5)

        self.btn_solve = tk.Button(
            self.top_frame,
            text="Resolver Animado",
            command=self.start_solving,
            state=tk.DISABLED
        )
        self.btn_solve.pack(side=tk.LEFT, padx=5)

        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(padx=20, pady=20)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack()

        self.status_label = tk.Label(
            root,
            text="Carga un archivo para comenzar",
            font=("Arial", 10)
        )
        self.status_label.pack(pady=5)

    def load_file(self):
        filename = filedialog.askopenfilename(
            initialdir=".",
            title="Selecciona archivo de tablero",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )

        if filename:
            try:
                self.solver = NumberlinkSolver(filename)
                self.init_grid_ui()
                self.btn_solve.config(state=tk.NORMAL)
                self.status_label.config(
                    text=f"Tablero {self.solver.rows}x{self.solver.cols} cargado."
                )
            except Exception as e:
                messagebox.showerror(
                    "Error", f"No se pudo cargar el archivo:\n{e}"
                )

    def get_color(self, tag):
        if tag is None or str(tag).strip() == '':
            return "white"

        if tag not in self.colors:
            base_colors = [
                "#FFADAD", "#FFD6A5", "#FDFFB6", "#CAFFBF", "#9BF6FF",
                "#A0C4FF", "#BDB2FF", "#FFC6FF", "#FF6F61", "#6B5B95"
            ]
            idx = len(self.colors) % len(base_colors)
            self.colors[tag] = base_colors[idx]

        return self.colors[tag]

    def init_grid_ui(self):
        self.canvas.delete("all")
        rows = self.solver.rows
        cols = self.solver.cols

        width = cols * self.cell_size
        height = rows * self.cell_size
        self.canvas.config(width=width, height=height)

        initial_grid = [row[:] for row in self.solver.grid]

        for r in range(rows):
            for c in range(cols):
                val = initial_grid[r][c]
                x1 = c * self.cell_size
                y1 = r * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                color = "white"
                text = ""
                is_fixed = False

                if val != ' ':
                    color = self.get_color(val)
                    text = val
                    is_fixed = True

                tag_id = f"cell_{r}_{c}"
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline="black",
                    tags=tag_id
                )

                if text:
                    self.canvas.create_text(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        text=text,
                        font=("Arial", 16, "bold")
                    )

                if is_fixed:
                    self.canvas.create_rectangle(
                        x1 + 2, y1 + 2, x2 - 2, y2 - 2,
                        width=2
                    )

    def update_cell_visual(self, r, c, text, color_code):
        is_fixed = False
        original_label = None

        for label, coords in self.solver.paths.items():
            if (r, c) in coords:
                is_fixed = True
                original_label = label
                break

        if is_fixed:
            fill_color = self.get_color(original_label)
            display_text = original_label
        else:
            fill_color = self.get_color(color_code) if color_code and color_code != ' ' else "white"
            display_text = text if text and str(text).strip() != '' else ''

        x1 = c * self.cell_size
        y1 = r * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size

        items = self.canvas.find_overlapping(x1 + 1, y1 + 1, x2 - 1, y2 - 1)
        for item in items:
            self.canvas.delete(item)

        tag_id = f"cell_{r}_{c}"
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=fill_color,
            outline="black",
            tags=tag_id
        )

        if is_fixed:
            self.canvas.create_rectangle(
                x1 + 2, y1 + 2, x2 - 2, y2 - 2,
                width=2
            )

        if display_text:
            self.canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=display_text,
                font=("Arial", 14)
            )

        self.root.update()

    def start_solving(self):
        if not self.solver:
            return
        self.btn_solve.config(state=tk.DISABLED)
        self.status_label.config(text="Resolviendo...", fg="blue")
        self.init_grid_ui()
        self.root.after(100, self._run_solver_logic)

    def _run_solver_logic(self):
        success = self.solver.solve(callback=self.update_cell_visual)
        if success:
            self.status_label.config(text="¡Solución Encontrada!", fg="green")
            messagebox.showinfo("Éxito", "El tablero ha sido resuelto.")
        else:
            self.status_label.config(text="No se encontró solución.", fg="red")
            messagebox.showwarning(
                "Falló",
                "El algoritmo no encontró un camino válido que cubra todo el tablero."
            )
        self.btn_solve.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = NumberlinkApp(root)
    root.mainloop()

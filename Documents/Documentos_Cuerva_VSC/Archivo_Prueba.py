import tkinter as tk
from tkinter import messagebox
import numpy as np

class ConnectFour:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("4 en Raya - Connect Four")
        self.root.geometry("700x600")
        self.root.configure(bg="#2c3e50")
        
        # Configuración del juego
        self.rows = 6
        self.cols = 7
        self.board = np.zeros((self.rows, self.cols))
        self.current_player = 1  # 1 para jugador 1 (rojo), 2 para jugador 2 (amarillo)
        
        # Colores
        self.colors = {
            0: "#34495e",  # Vacío - gris oscuro
            1: "#e74c3c",  # Jugador 1 - rojo
            2: "#f1c40f"   # Jugador 2 - amarillo
        }
        
        self.setup_ui()
        self.create_board()
        
    def setup_ui(self):
        # Título
        title_label = tk.Label(
            self.root, 
            text="🔴 4 EN RAYA 🟡", 
            font=("Arial", 24, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=10)
        
        # Indicador de turno
        self.turn_label = tk.Label(
            self.root, 
            text="Turno: Jugador 1 (🔴)", 
            font=("Arial", 16),
            bg="#2c3e50",
            fg="white"
        )
        self.turn_label.pack(pady=5)
        
        # Frame para el tablero
        self.board_frame = tk.Frame(self.root, bg="#3498db", bd=5, relief="raised")
        self.board_frame.pack(pady=20)
        
        # Botones para reiniciar
        button_frame = tk.Frame(self.root, bg="#2c3e50")
        button_frame.pack(pady=10)
        
        restart_btn = tk.Button(
            button_frame,
            text="🔄 Nueva Partida",
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            command=self.restart_game,
            padx=20,
            pady=10
        )
        restart_btn.pack(side=tk.LEFT, padx=10)
        
        quit_btn = tk.Button(
            button_frame,
            text="❌ Salir",
            font=("Arial", 12, "bold"),
            bg="#c0392b",
            fg="white",
            command=self.root.quit,
            padx=20,
            pady=10
        )
        quit_btn.pack(side=tk.LEFT, padx=10)
        
    def create_board(self):
        self.buttons = []
        for row in range(self.rows):
            button_row = []
            for col in range(self.cols):
                btn = tk.Button(
                    self.board_frame,
                    width=8,
                    height=4,
                    font=("Arial", 16, "bold"),
                    bg=self.colors[0],
                    command=lambda c=col: self.make_move(c),
                    relief="raised",
                    bd=3
                )
                btn.grid(row=row, column=col, padx=2, pady=2)
                button_row.append(btn)
            self.buttons.append(button_row)
    
    def make_move(self, col):
        # Buscar la fila más baja disponible en la columna
        for row in range(self.rows-1, -1, -1):
            if self.board[row][col] == 0:
                self.board[row][col] = self.current_player
                self.update_button(row, col)
                
                # Verificar si hay ganador
                if self.check_winner(row, col):
                    self.show_winner()
                    return
                
                # Verificar empate
                if self.is_board_full():
                    self.show_tie()
                    return
                
                # Cambiar turno
                self.switch_player()
                return
        
        # Columna llena
        messagebox.showwarning("Columna llena", "Esta columna está llena. Elige otra.")
    
    def update_button(self, row, col):
        player = int(self.board[row][col])
        self.buttons[row][col].configure(
            bg=self.colors[player],
            text="●",
            fg="white" if player == 1 else "black"
        )
    
    def switch_player(self):
        self.current_player = 3 - self.current_player  # Alterna entre 1 y 2
        player_symbol = "🔴" if self.current_player == 1 else "🟡"
        self.turn_label.config(text=f"Turno: Jugador {self.current_player} ({player_symbol})")
    
    def check_winner(self, row, col):
        player = self.board[row][col]
        
        # Direcciones: horizontal, vertical, diagonal /, diagonal \
        directions = [
            (0, 1),   # horizontal
            (1, 0),   # vertical
            (1, 1),   # diagonal \
            (1, -1)   # diagonal /
        ]
        
        for dr, dc in directions:
            count = 1  # Contar la ficha actual
            
            # Contar en una dirección
            r, c = row + dr, col + dc
            while (0 <= r < self.rows and 0 <= c < self.cols and 
                   self.board[r][c] == player):
                count += 1
                r, c = r + dr, c + dc
            
            # Contar en la dirección opuesta
            r, c = row - dr, col - dc
            while (0 <= r < self.rows and 0 <= c < self.cols and 
                   self.board[r][c] == player):
                count += 1
                r, c = r - dr, c - dc
            
            if count >= 4:
                return True
        
        return False
    
    def is_board_full(self):
        return not any(0 in row for row in self.board)
    
    def show_winner(self):
        player_symbol = "🔴" if self.current_player == 1 else "🟡"
        messagebox.showinfo(
            "¡Ganador!", 
            f"¡Felicidades! Ganó el Jugador {self.current_player} ({player_symbol})!"
        )
        self.disable_board()
    
    def show_tie(self):
        messagebox.showinfo("Empate", "¡Es un empate! El tablero está lleno.")
    
    def disable_board(self):
        for row in self.buttons:
            for btn in row:
                btn.configure(state="disabled")
    
    def restart_game(self):
        self.board = np.zeros((self.rows, self.cols))
        self.current_player = 1
        self.turn_label.config(text="Turno: Jugador 1 (🔴)")
        
        # Limpiar botones
        for row in range(self.rows):
            for col in range(self.cols):
                self.buttons[row][col].configure(
                    bg=self.colors[0],
                    text="",
                    state="normal"
                )
    
    def run(self):
        self.root.mainloop()

# Ejecutar el juego
if __name__ == "__main__":
    game = ConnectFour()
    game.run()
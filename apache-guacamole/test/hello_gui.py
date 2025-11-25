import tkinter as tk
root = tk.Tk()
root.title("Hello from GUI Pod")
label = tk.Label(root, text="Hello from pod!", font=("Arial", 24))
label.pack(padx=20, pady=20)
root.mainloop()


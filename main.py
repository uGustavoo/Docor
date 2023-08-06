import os
import shutil
import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from PIL import ImageTk, Image
import fitz


# ______________________________ Classes do Sistema Principal ______________________________ #

class App(tk.Tk):
    WINDOW_WIDTH = 1366
    WINDOW_HEIGHT = 768

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title('')
        self.geometry(f'{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}')
        self.largura_tela = self.winfo_screenwidth()
        self.altura_tela = self.winfo_screenheight()
        self.posicao_x = (self.largura_tela - 1366) // 2
        self.posicao_y = (self.altura_tela - 768) // 2
        self.geometry("+{}+{}".format(self.posicao_x, self.posicao_y))
        self.resizable(width=False, height=False)
        self.iconbitmap("Imagens/icon.ico")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for Page in (Main, Tela2):
            page_name = Page.__name__
            frame = Page(parent=container, controller=self)
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")
            frame.configure(background="white")

        self.show_frame(Main.__name__)

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()


class Main(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.base_folder = r"D:\Documentos\Base"
        self.documents = []
        self.current_folder = None
        self.current_page = 0
        self.total_pages = 0
        self.selected_button = None
        self.zoom_factor = 0.55
        self.drag_data = {'x': 0, 'y': 0, 'item': None}

        # __________ Cabeçalho __________ #

        self.frame_cabecalho = Frame(self)
        self.frame_cabecalho.place(x=0, y=0, width=1366, height=56)
        self.frame_cabecalho.configure(relief='flat', borderwidth="2", background="#252530")

        self.logo_img = ImageTk.PhotoImage(Image.open("Imagens/logo_lg.png"))
        self.logo_label = Label(self.frame_cabecalho, image=self.logo_img, bg="#252530")
        self.logo_label.pack(side=LEFT, padx=10, pady=5)

        self.close_img = ImageTk.PhotoImage(Image.open("Imagens/close.png"))
        self.close_button = Button(self.frame_cabecalho, image=self.close_img, bg="#252530", bd=0, cursor='hand2',
                                   command=self.close_window)
        self.close_button.pack(side=RIGHT, padx=10, pady=5)

        self.fullscreen_img = ImageTk.PhotoImage(Image.open("Imagens/icon_fullscreen.png"))
        self.screen_img = ImageTk.PhotoImage(Image.open("Imagens/icon_screen.png"))
        self.fullscreen_button = Button(self.frame_cabecalho, image=self.fullscreen_img, bg="#252530", bd=0,
                                        cursor='hand2', command=self.fullscreen)
        self.fullscreen_button.pack(side=RIGHT, padx=10, pady=5)

        self.linha = Label(self)
        self.linha.place(x=683, y=100, width=1, height=625)
        self.linha.configure(background="#252530", compound='left', disabledforeground="#252530", border=0,
                             font=('Calibri', 14, 'bold'), foreground="#252530")

        # _________ Campo Esquerdo (Pesquisa e Seleção) _________ #

        self.frame_esquerdo = Frame(self, width=683, height=712, background="white")
        self.frame_esquerdo.place(x=0, y=56)

        self.label_docdata = Label(self.frame_esquerdo, text="Dados do Documento")
        self.label_docdata.configure(fg='black', border=0, bg='white', foreground="#6B6B6B",
                                     activeforeground="#BFC0C2", activebackground="white",
                                     font=('Calibri', 18))
        self.label_docdata.place(x=195, y=30)

        self.logo_search = ImageTk.PhotoImage(Image.open("Imagens/icon_search.png"))
        self.label_search = Label(self.frame_esquerdo, image=self.logo_search, bg="white")
        self.label_search.place(x=205, y=97)

        def on_enter(e):
            if self.entry_search.get() == "Informe a Matrícula":
                self.entry_search.delete(0, "end")

        def on_leave(e):
            nome = self.entry_search.get()
            if nome == "":
                self.entry_search.insert(0, "Informe a Matrícula")

        self.entry_search = Entry(self.frame_esquerdo, width=30, fg='#8A8C8F', border=0, bg='white',
                                  font=('calibri', 14))
        self.entry_search.place(x=235, y=98)
        self.entry_search.insert(0, 'Informe a Matrícula')
        self.entry_search.bind('<FocusIn>', on_enter)
        self.entry_search.bind('<FocusOut>', on_leave)
        self.entry_search.bind('<KeyRelease>', self.search_folders)

        Frame(self.frame_esquerdo, width=345, height=2, bg="black").place(x=195, y=127)

        self.listbox_results = tk.Listbox(self.frame_esquerdo, width=25, height=1, justify=CENTER, font=100)
        self.listbox_results.place(x=255, y=145)

        self.listbox_results.bind('<<ListboxSelect>>', self.show_subfolders_in_buttons)

        self.label_selecione = Label(self.frame_esquerdo, text="")
        self.label_selecione.configure(fg='black', border=0, bg='white', foreground="#6B6B6B",
                                       activeforeground="#BFC0C2", activebackground="white",
                                       font=('Calibri', 13))
        self.label_selecione.place(x=205, y=190)

        self.icon_folder = ImageTk.PhotoImage(Image.open("Imagens/icon_folder.png"))
        self.subfolders_buttons_frame = tk.Frame(self.frame_esquerdo, background="white")
        self.subfolders_buttons_frame.place(x=195, y=230)

        self.label_version = Label(self.frame_esquerdo, text="Versão 1.0")
        self.label_version.configure(border=0, bg='white', foreground="#252530",
                                     activeforeground="#BFC0C2", activebackground="white",
                                     font=('Calibri', 12))
        self.label_version.place(x=25, y=670)

        # _________ Campo Direito (Visualização) _________ #

        self.frame_direito = Frame(self, width=681, height=712, background="white")
        self.frame_direito.place(x=685, y=56)

        self.label_docview = Label(self.frame_direito, text="Visualização dos Documentos")
        self.label_docview.configure(fg='black', border=0, bg='white', foreground="#6B6B6B",
                                     activeforeground="#BFC0C2", activebackground="white",
                                     font=('Calibri', 18))
        self.label_docview.place(x=150, y=30)

        self.label_info = tk.Label(self.frame_direito, text="", background="white", foreground="#6B6B6B",
                                   font=("Helvetica", 10))
        self.label_info.place(x=190, y=90)

        self.canvas = tk.Canvas(self.frame_direito, width=325, height=450)
        self.canvas.place(x=150, y=115)

        self.left_image = ImageTk.PhotoImage(Image.open("Imagens/icon_left.png"))
        self.button_prev_page = tk.Button(self.frame_direito, text="<", cursor='hand2', font=18, foreground="#232323",
                                          relief="flat", background="white", image=self.left_image,
                                          command=self.show_previous_page)
        self.button_prev_page.place(x=245, y=585)

        self.label_page_number = tk.Label(self.frame_direito, text="", relief="flat", background="white",
                                          foreground="#232323", font=("Helvetica", 12))
        self.label_page_number.place(x=300, y=582)

        self.right_image = ImageTk.PhotoImage(Image.open("Imagens/icon_right.png"))
        self.button_next_page = tk.Button(self.frame_direito, text=">", cursor='hand2', font=18, foreground="#232323",
                                          relief="flat", background="white", image=self.right_image,
                                          command=self.show_next_page)
        self.button_next_page.place(x=380, y=585)

        self.button_abrir = Button(self.frame_direito, text="Abrir", width=12, height=1, background="#E97300",
                                   relief="flat", cursor='hand2', font="bold", command=self.open_pdf,
                                   foreground="white")
        self.button_abrir.place(x=190, y=620)

        self.button_local = Button(self.frame_direito, text="Local", width=12, height=1, background="#1F8A0D",
                                   relief="flat", command=self.open_folder_in_file_explorer,
                                   cursor='hand2', font="bold",
                                   foreground="white")
        self.button_local.place(x=330, y=620)

        self.in_image = ImageTk.PhotoImage(Image.open("Imagens/icon_zoom_in.png"))
        self.button_zoom_in = Button(self.frame_direito, image=self.in_image, bg="white", relief="flat", cursor='hand2',
                                     command=self.zoom_in)
        self.button_zoom_in.place(x=500, y=125)

        self.out_image = ImageTk.PhotoImage(Image.open("Imagens/icon_zoom_out.png"))
        self.button_zoom_out = Button(self.frame_direito, image=self.out_image, bg="white", relief="flat",
                                      cursor='hand2', command=self.zoom_out)
        self.button_zoom_out.place(x=500, y=165)

        self.out_download = ImageTk.PhotoImage(Image.open("Imagens/icon_download.png"))
        self.button_download = Button(self.frame_direito, image=self.out_download, bg="white", relief="flat",
                                      cursor='hand2', command=self.download_pdf)
        self.button_download.place(x=500, y=205)

        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # __________ Funções __________ #

    def on_canvas_press(self, event):
        self.drag_data['item'] = self.canvas.find_closest(event.x, event.y)[0]
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y

    def on_canvas_motion(self, event):
        if self.drag_data['item']:
            dx = event.x - self.drag_data['x']
            dy = event.y - self.drag_data['y']
            self.canvas.move(self.drag_data['item'], dx, dy)
            self.drag_data['x'] = event.x
            self.drag_data['y'] = event.y

    def on_canvas_release(self, event):
        self.drag_data['item'] = None

    def zoom_in(self):
        self.zoom_factor *= 1.25
        self.show_page()

    def zoom_out(self):
        self.zoom_factor /= 1.25
        self.show_page()

    def open_pdf(self):
        if self.current_folder and self.current_page < len(self.documents):
            file_path = self.documents[self.current_page]
            os.startfile(file_path)  # Open the PDF using the default system viewer

    def download_pdf(self):
        if self.current_folder and self.current_page < len(self.documents):
            file_path = self.documents[self.current_page]
            save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")],
                                                     title="Save PDF As")  # Ask user for save location
            if save_path:
                shutil.copyfile(file_path, save_path)

    def open_folder_in_file_explorer(self):
        if self.current_folder:
            os.startfile(self.current_folder)

    def search_folders(self, event):
        query = self.entry_search.get().lower()
        if self.base_folder:
            subfolders = [folder for folder in os.listdir(self.base_folder) if
                          os.path.isdir(os.path.join(self.base_folder, folder))]
            search_results = [folder for folder in subfolders if query in folder.lower()]
            self.update_results_list(search_results)

    def update_results_list(self, results=None):
        self.listbox_results.delete(0, tk.END)
        if results:
            for folder in results:
                self.listbox_results.insert(tk.END, folder)

    def clear_canvas(self):
        self.canvas.delete("all")

    def show_subfolders_in_buttons(self, event):
        selected_index = self.listbox_results.curselection()
        if selected_index:
            selected_folder = self.listbox_results.get(selected_index[0])
            folder_path = os.path.join(self.base_folder, selected_folder)
            self.scan_documents(folder_path)
            self.show_subfolders_buttons(folder_path)
            self.entry_search.delete(0, tk.END)
            self.clear_canvas()

    def update_selected_button(self, selected_button):
        for button in self.subfolders_buttons_frame.winfo_children():
            button.configure(bg="#252530", foreground="white")
        selected_button.configure(bg="#A50034", foreground="white")
        self.selected_button = selected_button

    def button_enter(self, event):
        event.widget.configure(bg="#A50034", foreground="white")

    def button_leave(self, event):
        if self.selected_button is None or event.widget != self.selected_button:
            event.widget.configure(bg="#252530", foreground="white")

    def show_subfolders_buttons(self, folder_path):
        for widget in self.subfolders_buttons_frame.winfo_children():
            widget.destroy()

        subfolders = [folder for folder in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, folder))]
        for folder in subfolders:
            btn = tk.Button(self.subfolders_buttons_frame, text=folder, width=320, height=50, background="#252530",
                            anchor='w', foreground="white", relief="flat", font=18, cursor='hand2', padx=10,
                            compound='left', image=self.icon_folder,
                            command=lambda f=folder: self.show_documents_in_folder(folder_path, f))
            btn.pack(side=tk.TOP, pady=10, padx=10)

            btn.bind("<Button-1>", lambda event, button=btn: self.update_selected_button(button))
            btn.bind("<Enter>", self.button_enter)
            btn.bind("<Leave>", self.button_leave)

            self.label_selecione.configure(text="Selecione uma das pastas abaixo:")

    def scan_documents(self, folder_path):
        self.documents.clear()
        for root, _, files in os.walk(folder_path):
            for filename in files:
                if filename.endswith(".pdf"):
                    file_path = os.path.join(root, filename)
                    self.documents.append(file_path)

    def show_documents_in_folder(self, folder_path, subfolder_name):
        folder_path = os.path.join(folder_path, subfolder_name)
        self.scan_documents(folder_path)
        if self.documents:
            self.current_folder = folder_path
            self.current_page = 0
            self.show_pdf(self.documents[self.current_page])

    def show_pdf(self, file_path):
        try:
            self.pdf_viewer.close()
        except AttributeError:
            pass

        self.pdf_viewer = fitz.open(file_path)
        self.total_pages = self.pdf_viewer.page_count
        self.current_page = 0
        self.show_page()

    def show_page(self):
        page = self.pdf_viewer[self.current_page]
        image = page.get_pixmap(matrix=fitz.Matrix(self.zoom_factor, self.zoom_factor))
        photo = tk.PhotoImage(data=image.tobytes("ppm"))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.canvas.image = photo

        self.update_page_info()

    def update_page_info(self):
        if self.current_folder:
            current_page_number = self.current_page + 1
            parts = self.current_folder.split(os.path.sep)
            folder_name = parts[-1]
            parent_folder_name = parts[-2] if len(
                parts) > 1 else ""

            pdf_name = os.path.basename(self.documents[self.current_page])

            if parent_folder_name:
                display_text = f"{parent_folder_name} > {folder_name} > {pdf_name}"
            else:
                display_text = folder_name

            self.label_info.config(text=display_text)
            self.label_page_number.config(text=f"{current_page_number} / {self.total_pages}")

    def show_previous_page(self):
        if self.current_folder and self.current_page > 0:
            self.current_page -= 1
            file_path = self.documents[self.current_page]
            self.show_pdf(file_path)

    def show_next_page(self):
        if self.current_folder and self.current_page < len(self.documents) - 1:
            self.current_page += 1
            file_path = self.documents[self.current_page]
            self.show_pdf(file_path)

    def close_window(self):
        resposta = messagebox.askquestion("Fechar", "Tem certeza que deseja fechar o Docor?")
        if resposta == "yes":
            self.controller.destroy()
        else:
            pass

    def fullscreen(self):
        if self.controller.attributes("-fullscreen"):
            self.controller.attributes("-fullscreen", False)
            self.controller.attributes("-topmost", False)
            self.fullscreen_button.configure(image=self.fullscreen_img)
        else:
            self.controller.attributes("-fullscreen", True)
            self.controller.attributes("-topmost", True)
            self.fullscreen_button.configure(image=self.screen_img)


class Tela2(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller


if __name__ == "__main__":
    app = App()
    app.mainloop()

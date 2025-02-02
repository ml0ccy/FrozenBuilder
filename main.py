import customtkinter as ctk
import json
from PIL import Image  # Для работы с изображениями

# Установка темы по умолчанию
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class GUIBuilder(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GUI Builder")
        self.geometry("1000x700")

        # Словарь для хранения соответствия: id окна холста -> виджет
        self.windows = {}

        # Панель инструментов
        self.create_toolbar()

        # Контейнер для холста и скроллбаров
        self.create_canvas()

        # Панель свойств
        self.create_properties_panel()

    def create_toolbar(self):
        """Создает панель инструментов."""
        self.toolbar = ctk.CTkFrame(self, height=60, corner_radius=10)
        self.toolbar.pack(fill="x", pady=10, padx=10)

        buttons = [
            ("Button", "icons/button.png", self.add_button_widget),
            ("Label", "icons/label.png", self.add_label_widget),
            ("Save", "icons/save.png", self.save_project),
            ("Load", "icons/load.png", self.load_project),
        ]

        for text, icon_path, command in buttons:
            # Загружаем изображение с помощью Pillow
            try:
                image = Image.open(icon_path)
            except FileNotFoundError:
                print(f"Файл иконки не найден: {icon_path}")
                image = None

            btn = ctk.CTkButton(
                self.toolbar,
                text=text,
                image=ctk.CTkImage(light_image=image, size=(20, 20)) if image else None,
                compound="left",
                command=command,
                corner_radius=8,
                height=40,
                width=120,
            )
            btn.pack(side="left", padx=10)

    def create_canvas(self):
        """Создает холст с прокруткой и сеткой."""
        self.canvas_frame = ctk.CTkFrame(self, corner_radius=10)
        self.canvas_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.canvas = ctk.CTkCanvas(self.canvas_frame, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.vbar = ctk.CTkScrollbar(self.canvas_frame, orientation="vertical", command=self.canvas.yview)
        self.vbar.pack(side="right", fill="y")

        self.hbar = ctk.CTkScrollbar(self, orientation="horizontal", command=self.canvas.xview)
        self.hbar.pack(side="bottom", fill="x")

        self.canvas.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)
        self.canvas.bind("<Configure>", lambda event: self.update_canvas_scrollregion())

        # Добавление сетки
        self.draw_grid()

    def draw_grid(self):
        """Рисует сетку на холсте."""
        grid_size = 20
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        for x in range(0, canvas_width, grid_size):
            self.canvas.create_line(x, 0, x, canvas_height, fill="#444444", dash=(2, 2))
        for y in range(0, canvas_height, grid_size):
            self.canvas.create_line(0, y, canvas_width, y, fill="#444444", dash=(2, 2))

    def create_properties_panel(self):
        """Создает панель свойств."""
        self.properties_panel = ctk.CTkFrame(self, width=250, corner_radius=10)
        self.properties_panel.pack(side="right", fill="y", padx=10, pady=10)

        self.property_label = ctk.CTkLabel(self.properties_panel, text="Свойства", font=("Arial", 16, "bold"))
        self.property_label.pack(pady=10)

    def add_button_widget(self):
        """Добавляет кнопку на холст."""
        self.add_widget("CTkButton", "Button")

    def add_label_widget(self):
        """Добавляет метку на холст."""
        self.add_widget("CTkLabel", "Label")

    def add_widget(self, widget_type, default_text):
        """Общий метод для добавления виджета."""
        text_var = ctk.StringVar(value=default_text)
        if widget_type == "CTkButton":
            widget = ctk.CTkButton(
                self.canvas,
                textvariable=text_var,
                compound="center",
                corner_radius=8,
                fg_color="#1f6aa5",
            )
        elif widget_type == "CTkLabel":
            widget = ctk.CTkLabel(
                self.canvas,
                textvariable=text_var,
                compound="center",
                corner_radius=8,
                fg_color="#2b2b2b",
            )
        else:
            return

        widget.text_var = text_var

        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        req_width = widget.winfo_reqwidth()
        req_height = widget.winfo_reqheight()
        x = (canvas_width - req_width) // 2
        y = (canvas_height - req_height) // 2

        window_id = self.canvas.create_window(x, y, window=widget, anchor="nw")
        self.windows[window_id] = widget

        self.bind_widget_events(widget, window_id)
        self.update_canvas_scrollregion()

    def bind_widget_events(self, widget, window_id):
        """Привязывает события к виджету."""
        widget.bind("<Button-1>", lambda event: self.start_drag(event, window_id))
        widget.bind("<B1-Motion>", lambda event: self.drag(event, window_id))
        widget.bind("<ButtonRelease-1>", lambda event: self.end_drag(event, window_id))
        widget.bind("<Double-Button-1>", lambda event: self.show_properties(event, window_id))
        widget.bind("<Button-3>", lambda event: self.delete_widget(event, window_id))

    def start_drag(self, event, window_id):
        """Начало перетаскивания виджета."""
        widget = self.windows.get(window_id)
        if widget is None:
            return
        widget._drag_offset_x = event.x
        widget._drag_offset_y = event.y

    def drag(self, event, window_id):
        """Перетаскивание виджета."""
        widget = self.windows.get(window_id)
        if widget is None:
            return

        canvas_x = self.canvas.canvasx(event.x_root - self.canvas.winfo_rootx())
        canvas_y = self.canvas.canvasy(event.y_root - self.canvas.winfo_rooty())
        new_x = canvas_x - widget._drag_offset_x
        new_y = canvas_y - widget._drag_offset_y

        self.canvas.coords(window_id, new_x, new_y)
        self.update_canvas_scrollregion()

    def end_drag(self, event, window_id):
        """Завершение перетаскивания."""
        pass

    def show_properties(self, event, window_id):
        """Отображение свойств виджета."""
        self.clear_properties_panel()
        widget = self.windows.get(window_id)
        if not widget:
            return

        # Текст
        text_label = ctk.CTkLabel(self.properties_panel, text="Текст:")
        text_label.pack(pady=(10, 0))

        text_entry = ctk.CTkEntry(self.properties_panel)
        text_entry.insert(0, widget.text_var.get())
        text_entry.pack(pady=(0, 10))
        text_entry.bind("<Return>", lambda e: widget.text_var.set(text_entry.get()))

        # Цвет фона
        color_label = ctk.CTkLabel(self.properties_panel, text="Цвет фона:")
        color_label.pack(pady=(10, 0))

        color_entry = ctk.CTkEntry(self.properties_panel)
        color_entry.insert(0, "#1f6aa5" if isinstance(widget, ctk.CTkButton) else "#2b2b2b")
        color_entry.pack(pady=(0, 10))
        color_entry.bind("<Return>", lambda e: widget.configure(fg_color=color_entry.get()))

    def delete_widget(self, event, window_id):
        """Удаляет виджет."""
        self.canvas.delete(window_id)
        if window_id in self.windows:
            del self.windows[window_id]
        self.clear_properties_panel()
        self.update_canvas_scrollregion()

    def clear_properties_panel(self):
        """Очищает панель свойств."""
        for child in self.properties_panel.winfo_children():
            child.destroy()

    def save_project(self):
        """Сохраняет проект в файл."""
        data = []
        for window_id, widget in self.windows.items():
            pos = self.canvas.coords(window_id)
            data.append({
                "type": widget.__class__.__name__,
                "x": pos[0],
                "y": pos[1],
                "properties": {
                    "text": widget.text_var.get() if hasattr(widget, "text_var") else None,
                }
            })
        with open("project.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_project(self):
        """Загружает проект из файла."""
        try:
            with open("project.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            for window_id in list(self.windows.keys()):
                self.canvas.delete(window_id)
                del self.windows[window_id]

            for item in data:
                if item["type"] == "CTkButton":
                    text_var = ctk.StringVar(value=item["properties"]["text"])
                    widget = ctk.CTkButton(self.canvas, textvariable=text_var, compound="center")
                    widget.text_var = text_var
                elif item["type"] == "CTkLabel":
                    text_var = ctk.StringVar(value=item["properties"]["text"])
                    widget = ctk.CTkLabel(self.canvas, textvariable=text_var, compound="center")
                    widget.text_var = text_var
                else:
                    continue

                window_id = self.canvas.create_window(item["x"], item["y"], window=widget, anchor="nw")
                self.windows[window_id] = widget
                self.bind_widget_events(widget, window_id)

            self.update_canvas_scrollregion()
        except FileNotFoundError:
            pass

    def update_canvas_scrollregion(self):
        """Обновляет область прокрутки холста."""
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)
        else:
            self.canvas.configure(scrollregion=(0, 0, self.canvas.winfo_width(), self.canvas.winfo_height()))

if __name__ == "__main__":
    app = GUIBuilder()
    app.mainloop()

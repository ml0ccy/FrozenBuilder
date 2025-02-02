import customtkinter as ctk
import json

class GUIBuilder(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GUI Builder")
        self.geometry("800x600")

        # Словарь для хранения соответствия: id окна холста -> виджет
        self.windows = {}

        # Панель инструментов
        self.toolbar = ctk.CTkFrame(self, height=50)
        self.toolbar.pack(fill="x")

        self.add_button = ctk.CTkButton(self.toolbar, text="Button", command=self.add_button_widget)
        self.add_button.pack(side="left", padx=5)

        self.add_label = ctk.CTkButton(self.toolbar, text="Label", command=self.add_label_widget)
        self.add_label.pack(side="left", padx=5)

        self.save_button = ctk.CTkButton(self.toolbar, text="Сохранить", command=self.save_project)
        self.save_button.pack(side="left", padx=5)

        self.load_button = ctk.CTkButton(self.toolbar, text="Загрузить", command=self.load_project)
        self.load_button.pack(side="left", padx=5)

        # Контейнер для холста и скроллбаров
        self.canvas_frame = ctk.CTkFrame(self)
        self.canvas_frame.pack(side="left", fill="both", expand=True)

        # Холст для размещения виджетов
        self.canvas = ctk.CTkCanvas(self.canvas_frame)
        self.canvas.pack(side="left", fill="both", expand=True)

        # Вертикальный скроллбар
        self.vbar = ctk.CTkScrollbar(self.canvas_frame, orientation="vertical", command=self.canvas.yview)
        self.vbar.pack(side="right", fill="y")
        # Горизонтальный скроллбар
        self.hbar = ctk.CTkScrollbar(self, orientation="horizontal", command=self.canvas.xview)
        self.hbar.pack(side="bottom", fill="x")

        self.canvas.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)
        self.canvas.bind("<Configure>", lambda event: self.update_canvas_scrollregion())

        # Панель свойств
        self.properties_panel = ctk.CTkFrame(self, width=200)
        self.properties_panel.pack(side="right", fill="y")
        self.property_label = ctk.CTkLabel(self.properties_panel, text="Свойства")
        self.property_label.pack()

        self.update_canvas_scrollregion()

    def add_button_widget(self):
        text_var = ctk.StringVar(value="Button")
        button = ctk.CTkButton(self.canvas, textvariable=text_var, compound="center")
        button.text_var = text_var

        # Центрируем виджет в области холста
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        req_width = button.winfo_reqwidth()
        req_height = button.winfo_reqheight()
        x = (canvas_width - req_width) // 2
        y = (canvas_height - req_height) // 2

        # Создаём окно на холсте для кнопки
        window_id = self.canvas.create_window(x, y, window=button, anchor="nw")
        self.windows[window_id] = button
        # Сохраняем id окна и привязываем события непосредственно к виджету:
        button.canvas_window_id = window_id
        button.bind("<Button-1>", lambda event, wid=window_id: self.start_drag(event, wid))
        button.bind("<B1-Motion>", lambda event, wid=window_id: self.drag(event, wid))
        button.bind("<ButtonRelease-1>", lambda event, wid=window_id: self.end_drag(event, wid))
        button.bind("<Double-Button-1>", lambda event, wid=window_id: self.show_properties(event, wid))
        button.bind("<Button-3>", lambda event, wid=window_id: self.delete_widget(event, wid))

        self.update_canvas_scrollregion()

    def add_label_widget(self):
        text_var = ctk.StringVar(value="Label")
        label = ctk.CTkLabel(self.canvas, textvariable=text_var, compound="center")
        label.text_var = text_var

        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        req_width = label.winfo_reqwidth()
        req_height = label.winfo_reqheight()
        x = (canvas_width - req_width) // 2
        y = (canvas_height - req_height) // 2

        window_id = self.canvas.create_window(x, y, window=label, anchor="nw")
        self.windows[window_id] = label
        label.canvas_window_id = window_id
        label.bind("<Button-1>", lambda event, wid=window_id: self.start_drag(event, wid))
        label.bind("<B1-Motion>", lambda event, wid=window_id: self.drag(event, wid))
        label.bind("<ButtonRelease-1>", lambda event, wid=window_id: self.end_drag(event, wid))
        label.bind("<Double-Button-1>", lambda event, wid=window_id: self.show_properties(event, wid))
        label.bind("<Button-3>", lambda event, wid=window_id: self.delete_widget(event, wid))

        self.update_canvas_scrollregion()

    # При нажатии внутри виджета (Button-1) сохраняем смещение от точки клика до верхнего левого угла виджета
    def start_drag(self, event, window_id):
        widget = self.windows.get(window_id)
        if widget is None:
            return
        # event.x и event.y – координаты относительно виджета
        widget._drag_offset_x = event.x
        widget._drag_offset_y = event.y

    # При перемещении вычисляем новые координаты окна на холсте,
    # используя глобальные координаты курсора, позицию холста на экране и сохранённое смещение
    def drag(self, event, window_id):
        widget = self.windows.get(window_id)
        if widget is None:
            return
        # Определяем координаты курсора относительно холста:
        canvas_x = self.canvas.canvasx(event.x_root - self.canvas.winfo_rootx())
        canvas_y = self.canvas.canvasy(event.y_root - self.canvas.winfo_rooty())
        new_x = canvas_x - widget._drag_offset_x
        new_y = canvas_y - widget._drag_offset_y
        self.canvas.coords(window_id, new_x, new_y)
        self.update_canvas_scrollregion()

    def end_drag(self, event, window_id):
        # По окончании перемещения можно выполнить дополнительные действия, если необходимо.
        pass

    def show_properties(self, event, window_id):
        self.clear_properties_panel()
        widget = self.windows.get(window_id)
        if widget and isinstance(widget, (ctk.CTkButton, ctk.CTkLabel)):
            text_label = ctk.CTkLabel(self.properties_panel, text="Текст:")
            text_label.pack(pady=(10, 0))
            text_entry = ctk.CTkEntry(self.properties_panel)
            text_entry.insert(0, widget.text_var.get())
            text_entry.pack(pady=(0, 10))
            text_entry.bind("<Return>", lambda e: widget.text_var.set(text_entry.get()))

    def delete_widget(self, event, window_id):
        self.canvas.delete(window_id)
        if window_id in self.windows:
            del self.windows[window_id]
        self.clear_properties_panel()
        self.update_canvas_scrollregion()

    def clear_properties_panel(self):
        for child in self.properties_panel.winfo_children():
            child.destroy()

    def save_project(self):
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
        try:
            with open("project.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            # Удаляем существующие объекты
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
                widget.canvas_window_id = window_id
                widget.bind("<Button-1>", lambda event, wid=window_id: self.start_drag(event, wid))
                widget.bind("<B1-Motion>", lambda event, wid=window_id: self.drag(event, wid))
                widget.bind("<ButtonRelease-1>", lambda event, wid=window_id: self.end_drag(event, wid))
                widget.bind("<Double-Button-1>", lambda event, wid=window_id: self.show_properties(event, wid))
                widget.bind("<Button-3>", lambda event, wid=window_id: self.delete_widget(event, wid))
            self.update_canvas_scrollregion()
        except FileNotFoundError:
            pass

    def update_canvas_scrollregion(self):
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)
        else:
            self.canvas.configure(scrollregion=(0, 0, self.canvas.winfo_width(), self.canvas.winfo_height()))

if __name__ == "__main__":
    app = GUIBuilder()
    app.mainloop()

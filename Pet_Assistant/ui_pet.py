import os
import tkinter as tk
from tkinter import messagebox


STATES = ("waking_up", "idle", "listening", "talking", "error", "muted")


class PetWindow:
    def __init__(
        self,
        image_paths=None,
        width=150,
        height=150,
        x=1700,
        y=900,
        transparent_color="black",
        on_exit=None,
        on_toggle_mic=None,
    ):
        self.root = tk.Tk()
        self.width = width
        self.height = height
        self.transparent_color = transparent_color
        self.on_exit = on_exit
        self.on_toggle_mic = on_toggle_mic
        self.images = {}
        self.state = "waking_up"
        self._drag_offset = (0, 0)
        self._mic_muted = False

        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", transparent_color)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.configure(bg=transparent_color)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Escape>", self.close)

        self.label = tk.Label(self.root, bg=transparent_color, bd=0, highlightthickness=0)
        self.label.pack(fill="both", expand=True)
        self.label.bind("<ButtonPress-1>", self._start_drag)
        self.label.bind("<B1-Motion>", self._drag)
        self.label.bind("<Button-3>", self._show_context_menu)

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Silenciar micrófono", command=self._toggle_mic)
        self.menu.add_command(label="Acerca de", command=self._show_about)
        self.menu.add_separator()
        self.menu.add_command(label="Salir", command=self.close)

        self._load_images(image_paths or {})
        self.update_state("waking_up")

    def set_close_callback(self, callback):
        self.on_exit = callback

    def update_state(self, state):
        normalized = str(state).strip().lower()
        if normalized not in self.images:
            normalized = "idle"

        self.state = normalized
        self.label.configure(image=self.images[normalized])

    def set_mic_muted(self, muted):
        self._mic_muted = muted
        self.menu.entryconfigure(
            0,
            label="Activar micrófono" if muted else "Silenciar micrófono",
        )
        self.update_state("muted" if muted else "idle")

    def after(self, delay_ms, callback):
        return self.root.after(delay_ms, callback)

    def after_cancel(self, after_id):
        self.root.after_cancel(after_id)

    def mainloop(self):
        self.root.mainloop()

    def destroy(self):
        self.root.destroy()

    def get_position(self):
        return {"x": self.root.winfo_x(), "y": self.root.winfo_y()}

    def close(self, event=None):
        if self.on_exit:
            self.on_exit()
        else:
            self.destroy()

    def _load_images(self, image_paths):
        for state in STATES:
            path = image_paths.get(state)
            image = self._load_image(path, state) if path else None
            self.images[state] = image or self._create_fallback_image(state)

    def _load_image(self, path, state):
        if not path or not os.path.exists(path):
            return None

        try:
            image = tk.PhotoImage(file=path)
        except tk.TclError:
            return None

        if image.width() > self.width * 2 or image.height() > self.height * 2:
            return self._crop_sprite_sheet(image, state)

        return image

    def _crop_sprite_sheet(self, sheet, state):
        rects = {
            "waking_up": (130, 55, 390, 345),
            "idle": (390, 55, 650, 345),
            "listening": (640, 385, 910, 685),
            "talking": (640, 700, 910, 1000),
        }
        rect = rects.get(state)
        if rect is None:
            return None

        cropped = tk.PhotoImage(width=rect[2] - rect[0], height=rect[3] - rect[1])
        try:
            self.root.tk.call(
                cropped,
                "copy",
                sheet,
                "-from",
                rect[0],
                rect[1],
                rect[2],
                rect[3],
                "-to",
                0,
                0,
            )
        except tk.TclError:
            return None

        if cropped.width() > self.width or cropped.height() > self.height:
            return cropped.subsample(
                max(1, cropped.width() // self.width),
                max(1, cropped.height() // self.height),
            )

        return cropped

    def _create_fallback_image(self, state):
        colors = {
            "waking_up": "#d0b040",
            "idle": "#5050c8",
            "listening": "#00c864",
            "talking": "#c85050",
            "error": "#ff3030",
            "muted": "#808080",
        }
        image = tk.PhotoImage(width=self.width, height=self.height)
        image.put(self.transparent_color, to=(0, 0, self.width, self.height))

        center_x = self.width // 2
        center_y = self.height // 2
        radius = min(self.width, self.height) // 3
        color = colors.get(state, colors["idle"])

        for y in range(self.height):
            for x in range(self.width):
                if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius**2:
                    image.put(color, (x, y))

        if state == "listening":
            self._draw_listening_waves(image, center_x, center_y, radius)
        elif state == "talking":
            self._draw_talking_marks(image, center_x, center_y, radius)
        elif state == "error":
            self._draw_error_mark(image, center_x, center_y, radius)

        return image

    def _draw_listening_waves(self, image, center_x, center_y, radius):
        wave_color = "#3aa0ff"
        for offset in (8, 16, 24):
            left_x = center_x - radius - offset
            right_x = center_x + radius + offset
            for y in range(center_y - 28, center_y + 29):
                if abs(y - center_y) in range(offset - 4, offset + 5):
                    image.put(wave_color, (max(0, left_x), y))
                    image.put(wave_color, (min(self.width - 1, right_x), y))

    def _draw_talking_marks(self, image, center_x, center_y, radius):
        mark_color = "#ffd040"
        for offset in range(0, 18):
            y = center_y - 8 + offset
            image.put(mark_color, (min(self.width - 1, center_x + radius + offset), y))
            image.put(mark_color, (max(0, center_x - radius - offset), y))

    def _draw_error_mark(self, image, center_x, center_y, radius):
        mark_color = "#ffffff"
        for offset in range(-20, 21):
            x1 = center_x + offset
            y1 = center_y + offset
            x2 = center_x + offset
            y2 = center_y - offset
            if 0 <= x1 < self.width and 0 <= y1 < self.height:
                image.put(mark_color, (x1, y1))
            if 0 <= x2 < self.width and 0 <= y2 < self.height:
                image.put(mark_color, (x2, y2))

    def _start_drag(self, event):
        self._drag_offset = (event.x, event.y)

    def _drag(self, event):
        x = self.root.winfo_pointerx() - self._drag_offset[0]
        y = self.root.winfo_pointery() - self._drag_offset[1]
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def _show_context_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def _toggle_mic(self):
        self._mic_muted = not self._mic_muted
        if self.on_toggle_mic:
            self.on_toggle_mic(self._mic_muted)
        self.set_mic_muted(self._mic_muted)

    def _show_about(self):
        messagebox.showinfo(
            "Acerca de Catvis",
            "Catvis\nAsistente local offline para Windows.",
        )

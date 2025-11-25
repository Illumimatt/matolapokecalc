import os
import sys
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from src.api import get_pokemon_data, get_all_names_list
from src.calculations import calculate_stat, ALL_NATURES, get_nature_multiplier, get_ev_from_target_stat

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class CombinationViewer(ctk.CTkToplevel):
    def __init__(self, parent, stat_name, target_stat, base, level, nature_mod, is_hp):
        super().__init__(parent)
        self.title(f"Combinações: {stat_name.upper()} = {target_stat}")
        self.geometry("350x450")
        self.minsize(300, 400)
        
        ctk.CTkLabel(self, text=f"Como atingir {target_stat} de {stat_name.upper()}?", 
                     font=("Arial", 14, "bold")).pack(pady=10)
        
        ctk.CTkLabel(self, text=f"Base: {base} | Nível: {level} | Nature: {nature_mod}", 
                     text_color="gray", font=("Arial", 11)).pack()

        header = ctk.CTkFrame(self, height=30)
        header.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(header, text="Seu IV", width=100, font=("Arial", 12, "bold")).pack(side="left", expand=True)
        ctk.CTkLabel(header, text="EV Necessário", width=100, font=("Arial", 12, "bold")).pack(side="left", expand=True)

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=280, height=300)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.calculate_combinations(target_stat, base, level, nature_mod, is_hp)

    def calculate_combinations(self, target, base, level, nature_mod, is_hp):
        found_any = False
        for iv in range(31, -1, -1):
            needed_ev = get_ev_from_target_stat(target, base, iv, level, nature_mod, is_hp)
            
            calc_stat = calculate_stat(base, iv, needed_ev, level, nature_mod, is_hp)
            while calc_stat < target and needed_ev <= 252:
                needed_ev += 4
                calc_stat = calculate_stat(base, iv, needed_ev, level, nature_mod, is_hp)
            
            if calc_stat > target: continue

            if 0 <= needed_ev <= 252:
                found_any = True
                self.add_row(iv, needed_ev)

        if not found_any:
            ctk.CTkLabel(self.scroll_frame, text="Impossível atingir este valor\ncom esta Natureza/Nível.", 
                         text_color="#ff5555").pack(pady=20)

    def add_row(self, iv, ev):
        row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row.pack(fill="x", pady=2)
        color = "white"
        if iv == 31: color = "#00ff00"
        if ev == 0: color = "#55aaff"
        ctk.CTkLabel(row, text=str(iv), width=100, text_color=color).pack(side="left", expand=True)
        ctk.CTkLabel(row, text=str(ev), width=100, text_color=color).pack(side="left", expand=True)


class PokeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Matola Poke Calculator")
        
        self.geometry("1200x700")
        self.resizable(True, True)
        self.minsize(1050, 600)

        try:
            self.iconbitmap(resource_path("favicon.ico"))
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o ícone: {e}")
        self.current_image_keep_alive = None 

        self.all_pokemon_names = get_all_names_list() 
        self.current_pokemon = None
        self.nature_var = ctk.StringVar(value="Hardy")
        self.stats_widgets = {} 
        self.is_updating = False 

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1) 
        self.grid_columnconfigure(2, weight=3) 
        self.grid_rowconfigure(0, weight=1)

        self.left_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.left_frame.grid(row=0, column=0, sticky="nswe")
        self.setup_left_panel()

        self.center_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray17"))
        self.center_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=20)
        self.setup_calculator_ui()

        self.right_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        self.right_frame.grid(row=0, column=2, sticky="nswe", padx=(5, 20), pady=20)
        self.setup_chart_ui()

    def setup_left_panel(self):
        self.left_frame.grid_rowconfigure(4, weight=1)

        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self.update_suggestions)

        self.search_entry = ctk.CTkEntry(self.left_frame, placeholder_text="Pokémon...", textvariable=self.search_var)
        self.search_entry.pack(pady=(20, 5), padx=20, fill="x")
        self.search_entry.bind("<Return>", self.trigger_search)

        self.suggestion_frame = ctk.CTkScrollableFrame(self.left_frame, width=210, height=150, fg_color="#2b2b2b")
        
        ctk.CTkButton(self.left_frame, text="Buscar", command=self.trigger_search).pack(pady=5, padx=20, fill="x")

        self.image_label = ctk.CTkLabel(self.left_frame, text="", width=200, height=200)
        self.image_label.pack(pady=10)
        
        self.info_container = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.info_container.pack(fill="both", expand=True)

        self.name_label = ctk.CTkLabel(self.info_container, text="---", font=("Arial", 22, "bold"))
        self.name_label.pack()
        self.type_label = ctk.CTkLabel(self.info_container, text="", text_color="gray")
        self.type_label.pack()

    def setup_calculator_ui(self):
        controls = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        controls.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(controls, text="Lv.").pack(side="left")
        self.level_entry = ctk.CTkEntry(controls, width=40)
        self.level_entry.insert(0, "50")
        self.level_entry.pack(side="left", padx=5)
        self.level_entry.bind("<KeyRelease>", self.on_component_change)

        ctk.CTkLabel(controls, text="Nature:").pack(side="left", padx=(15, 5))
        
        pretty_natures = []
        name_map = {"hp":"HP", "atk":"Atk", "def":"Def", "spa":"SpA", "spd":"SpD", "spe":"Spe"}
        for name, data in ALL_NATURES.items():
            if data['up']:
                up_txt = name_map.get(data['up'], data['up'])
                down_txt = name_map.get(data['down'], data['down'])
                label = f"{name} (+{up_txt} -{down_txt})"
            else:
                label = name 
            pretty_natures.append(label)
        pretty_natures.sort()
        
        self.nature_menu = ctk.CTkOptionMenu(controls, variable=self.nature_var, values=pretty_natures, width=160, command=self.on_component_change)
        self.nature_menu.set("Hardy")
        self.nature_menu.pack(side="left")

        self.total_ev_label = ctk.CTkLabel(controls, text="EVs: 0/510", font=("Arial", 12, "bold"))
        self.total_ev_label.pack(side="right", padx=10)
        
        ctk.CTkLabel(self.center_frame, text="*Clique Direito no Final para ver combinações", 
                     text_color="gray", font=("Arial", 10)).pack(pady=(0,5))

        grid_frame = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        grid_frame.grid_columnconfigure(3, weight=1)

        headers = ["Stat", "Base", "IV", "EV Slider", "EV", "Final"]
        for col, text in enumerate(headers):
            ctk.CTkLabel(grid_frame, text=text, font=("Arial", 11, "bold")).grid(row=0, column=col, padx=2, pady=5)

        labels = ["hp", "atk", "def", "spa", "spd", "spe"]
        
        for i, stat in enumerate(labels):
            row = i + 1
            ctk.CTkLabel(grid_frame, text=stat.upper()).grid(row=row, column=0, padx=5, pady=8)
            
            base_lbl = ctk.CTkLabel(grid_frame, text="0", width=30, text_color="gray")
            base_lbl.grid(row=row, column=1)
            
            iv_entry = ctk.CTkEntry(grid_frame, width=35)
            iv_entry.insert(0, "31")
            iv_entry.grid(row=row, column=2, padx=2)
            iv_entry.bind("<KeyRelease>", self.on_component_change)

            slider = ctk.CTkSlider(grid_frame, from_=0, to=252, width=120, number_of_steps=252)
            slider.set(0)
            slider.grid(row=row, column=3, padx=5, sticky="ew")
            slider.configure(command=lambda val, s=stat: self.on_slider_change(val, s))

            ev_entry = ctk.CTkEntry(grid_frame, width=35)
            ev_entry.insert(0, "0")
            ev_entry.grid(row=row, column=4, padx=2)
            ev_entry.bind("<KeyRelease>", lambda event, s=stat: self.on_ev_entry_change(event, s))

            final_entry = ctk.CTkEntry(grid_frame, width=50, border_color="#1f6aa5")
            final_entry.insert(0, "---")
            final_entry.grid(row=row, column=5, padx=2)
            final_entry.bind("<KeyRelease>", lambda event, s=stat: self.on_stat_entry_change(event, s))
            final_entry.bind("<Button-3>", lambda event, s=stat: self.open_combination_viewer(s))

            self.stats_widgets[stat] = {
                "base": base_lbl,
                "iv": iv_entry,
                "slider": slider,
                "ev": ev_entry,
                "final": final_entry
            }

    def open_combination_viewer(self, stat_name):
        if not self.current_pokemon: return
        try:
            target_val = int(self.stats_widgets[stat_name]["final"].get())
            base = int(self.stats_widgets[stat_name]["base"].cget("text"))
            level = int(self.level_entry.get())
            nature_name = self.nature_var.get().split()[0]
            nature_mod = get_nature_multiplier(nature_name, stat_name)
            is_hp = (stat_name == "hp")
            CombinationViewer(self, stat_name, target_val, base, level, nature_mod, is_hp)
        except ValueError: pass

    def setup_chart_ui(self):
        self.fig = plt.Figure(figsize=(5, 5), dpi=100, facecolor="#2b2b2b")
        self.ax = self.fig.add_subplot(111, polar=True)
        self.ax.set_facecolor("#2b2b2b")
        self.ax.spines['polar'].set_visible(False)
        self.ax.grid(color='#444444', linestyle='--')
        
        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=self.right_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_chart(self, base_stats, final_stats):
        self.ax.clear()
        categories = ['HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe']
        
        base_values = [base_stats[c.lower()] for c in categories]
        base_values_closed = base_values + base_values[:1]
        final_values = [final_stats[c.lower()] for c in categories]
        final_values_closed = final_values + final_values[:1]
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles_closed = angles + angles[:1]

        self.ax.set_facecolor("#2b2b2b")
        self.ax.set_xticks(angles)
        self.ax.set_xticklabels(categories, color="white", size=10, weight="bold")
        self.ax.tick_params(axis='y', colors='#2b2b2b') 
        self.ax.grid(color='#444444', linestyle='--')
        self.ax.spines['polar'].set_visible(False)

        self.ax.plot(angles_closed, base_values_closed, color='#00ffff', linewidth=1, linestyle='--', alpha=0.6)
        self.ax.fill(angles_closed, base_values_closed, color='#00ffff', alpha=0.1)

        self.ax.plot(angles_closed, final_values_closed, color='#ffd700', linewidth=2, linestyle='solid')
        self.ax.fill(angles_closed, final_values_closed, color='#ffd700', alpha=0.4)

        for angle, val in zip(angles, final_values):
            self.ax.text(angle, val * 1.15, str(val), color='white', size=11, fontweight='bold', ha='center', va='center')

        max_final = max(final_values) if final_values else 0
        max_base = max(base_values) if base_values else 0
        max_val = max(max_final, max_base)

        self.ax.set_ylim(0, max_val * 1.3 if max_val > 0 else 100)
        self.chart_canvas.draw()

    def on_component_change(self, event=None):
        if self.is_updating: return
        self.calculate_forward()

    def on_slider_change(self, value, stat_name):
        if self.is_updating: return
        self.is_updating = True
        val = int(value)
        self.stats_widgets[stat_name]["ev"].delete(0, "end")
        self.stats_widgets[stat_name]["ev"].insert(0, str(val))
        self.is_updating = False
        self.calculate_forward()

    def on_ev_entry_change(self, event, stat_name):
        if self.is_updating: return
        self.is_updating = True
        try:
            val_str = self.stats_widgets[stat_name]["ev"].get()
            val = int(val_str) if val_str else 0
            self.stats_widgets[stat_name]["slider"].set(val)
        except ValueError: pass
        self.is_updating = False
        self.calculate_forward()

    def on_stat_entry_change(self, event, stat_name):
        if self.is_updating: return
        self.calculate_reverse(stat_name)

    def calculate_forward(self):
        if not self.current_pokemon: return
        self.is_updating = True 

        total_ev = 0
        current_evs = {}
        for stat, w in self.stats_widgets.items():
            try:
                val = int(w["ev"].get())
                if val > 252: val = 252
                if val < 0: val = 0
            except: val = 0
            current_evs[stat] = val
            total_ev += val
        
        if total_ev > 510:
            overshoot = total_ev - 510
            focused = self.focus_get()
            target = None
            for stat, w in self.stats_widgets.items():
                if focused == w["ev"]._entry: 
                    target = stat
                    break
            if not target: target = "spe" 
            new_val = max(0, current_evs[target] - overshoot)
            current_evs[target] = new_val
            total_ev = 510

        self.total_ev_label.configure(text=f"EVs: {total_ev}/510", text_color="#55aaff" if total_ev == 510 else "white")

        try: level = int(self.level_entry.get())
        except: level = 50
        
        nature_name = self.nature_var.get().split()[0]
        
        base_stats_map = {}
        final_stats_map = {}

        for stat, w in self.stats_widgets.items():
            base = int(w["base"].cget("text"))
            base_stats_map[stat] = base

            try: iv = int(w["iv"].get())
            except: iv = 0
            ev = current_evs[stat]
            
            if w["ev"].get() != str(ev):
                w["ev"].delete(0, "end"); w["ev"].insert(0, str(ev))
            w["slider"].set(ev)

            nature_mod = get_nature_multiplier(nature_name, stat)
            final = calculate_stat(base, iv, ev, level, nature_mod, stat=="hp")
            final_stats_map[stat] = final
            
            if self.focus_get() != w["final"]._entry:
                w["final"].delete(0, "end"); w["final"].insert(0, str(final))
            
            if nature_mod > 1.0: w["final"].configure(text_color="#00ff00")
            elif nature_mod < 1.0: w["final"].configure(text_color="#ff5555")
            else: w["final"].configure(text_color="white")

        self.update_chart(base_stats_map, final_stats_map)
        self.is_updating = False

    def calculate_reverse(self, stat_changed):
        if not self.current_pokemon: return
        self.is_updating = True
        try:
            target_val = int(self.stats_widgets[stat_changed]["final"].get())
            level = int(self.level_entry.get())
            base = int(self.stats_widgets[stat_changed]["base"].cget("text"))
            iv = int(self.stats_widgets[stat_changed]["iv"].get())
            
            nature_name = self.nature_var.get().split()[0]
            nature_mod = get_nature_multiplier(nature_name, stat_changed)
            
            needed = get_ev_from_target_stat(target_val, base, iv, level, nature_mod, stat_changed=="hp")
            if needed < 0: needed = 0
            if needed > 252: needed = 252 
            
            self.stats_widgets[stat_changed]["ev"].delete(0, "end")
            self.stats_widgets[stat_changed]["ev"].insert(0, str(needed))
            self.stats_widgets[stat_changed]["slider"].set(needed)
            
            self.is_updating = False 
            self.calculate_forward()
        except ValueError:
            self.is_updating = False

    def update_suggestions(self, *args):
        txt = self.search_var.get().lower().strip()
        for w in self.suggestion_frame.winfo_children(): w.destroy()
        if not txt: 
            self.suggestion_frame.place_forget(); return
        matches = [n for n in self.all_pokemon_names if n.startswith(txt)][:10]
        if matches:
            self.suggestion_frame.place(x=20, y=55)
            self.suggestion_frame.lift()
            for n in matches:
                ctk.CTkButton(self.suggestion_frame, text=n.capitalize(), anchor="w", fg_color="transparent", 
                              command=lambda name=n: self.select_suggestion(name)).pack(fill="x")
        else: self.suggestion_frame.place_forget()

    def select_suggestion(self, name):
        self.search_var.set(name); self.suggestion_frame.place_forget(); self.trigger_search()

    def trigger_search(self, event=None):
        name = self.search_entry.get()
        self.suggestion_frame.place_forget()
        if not name: return

        self.name_label.configure(text="Buscando...")
        self.update_idletasks()

        self.image_label.configure(image="", text="") 
        self.current_image_keep_alive = None

        data = get_pokemon_data(name)
        
        if data:
            self.current_pokemon = data
            self.name_label.configure(text=f"#{data['id']} {data['name']}")
            self.type_label.configure(text=" / ".join(data['types']).upper())
            
            if data['image']:
                new_img = ctk.CTkImage(light_image=data['image'], dark_image=data['image'], size=(200, 200))
                self.current_image_keep_alive = new_img 
                self.image_label.configure(image=new_img, text="")
            else:
                self.image_label.configure(image="", text="Sem Imagem")
            
            for stat, w in self.stats_widgets.items():
                w["base"].configure(text=str(data['stats'].get(stat, 0)))
            self.calculate_forward()
        else:
            self.name_label.configure(text="Não Encontrado")
            self.image_label.configure(image="", text="?")
            self.current_image_keep_alive = None
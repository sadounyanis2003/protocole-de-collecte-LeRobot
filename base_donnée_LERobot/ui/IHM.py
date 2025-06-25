import customtkinter as ctk
import tkinter.messagebox as messagebox
from utils.file_utils import read_jsonl, append_jsonl, get_next_task_index
from pathlib import Path
from PIL import Image, ImageTk

TASKS_PATH = Path("meta/tasks.jsonl")


class TaskSelector(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sélection ou Création de Tâche – LeRobot DB")
        self.geometry("1200x1400")
        #ctk.set_appearance_mode("Light")
        #ctk.set_default_color_theme("green")
        self.configure(bg_color="#F0F0F0")  

        # Logo Renault
        logo_image = ctk.CTkImage(Image.open("ui/logo_renault.png"), size=(300, 200))
        ctk.CTkLabel(self, image=logo_image, text="").pack(pady=(20, 10))

        # Noms des créateurs
        ctk.CTkLabel(self, text="Made by : BAKALEM Dounia & SADOUN Yanis", text_color="gray").pack(pady=(0, 20))

        self.grid_columnconfigure(0, weight=1)

        # Titre principal
        ctk.CTkLabel(self, text="Gestion des Tâches", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=15)

        # Encadré liste tâches
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(list_frame, text="Tâches existantes :", anchor="w").pack(pady=(10, 5), padx=10, anchor="w")
        self.task_listbox = ctk.CTkTextbox(list_frame, height=200)
        self.task_listbox.pack(padx=10, pady=5, fill="x")
        self.task_listbox.configure(state="disabled")

        # Chargement tâches
        self.tasks = read_jsonl(TASKS_PATH)
        self.refresh_task_list()

        # Sélection tâche ou création
        ctk.CTkLabel(self, text="Sélectionnez une tâche existante ou créez-en une nouvelle :").pack(pady=(15, 5))
        values = [t["task_id"] for t in self.tasks] + ["<Nouvelle tâche>"]
        self.task_select = ctk.CTkComboBox(self, values=values, width=300, height=35)
        self.task_select.pack(pady=5)
        self.task_select.set("Sélectionner une tâche")
        self.task_select.bind("<<ComboboxSelected>>", self.on_task_selected)

        # Champs de saisie
        fields_frame = ctk.CTkFrame(self)
        fields_frame.pack(pady=20, padx=20, fill="x")

        self.task_id_entry     = ctk.CTkEntry(fields_frame, placeholder_text="ID de la tâche", height=35)
        self.description_entry = ctk.CTkEntry(fields_frame, placeholder_text="Description", height=35)
        self.criteria_entry    = ctk.CTkEntry(fields_frame, placeholder_text="Critère de réussite", height=35)
        self.difficulty_entry  = ctk.CTkEntry(fields_frame, placeholder_text="Difficulté", height=35)
        self.objects_entry     = ctk.CTkEntry(fields_frame, placeholder_text="Objets (séparés par des virgules)", height=35)

        for w in (self.task_id_entry, self.description_entry,
                  self.criteria_entry, self.difficulty_entry, self.objects_entry):
            w.pack(pady=8, padx=10, fill="x")

        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.pack(pady=10)

        # Bouton Valider
        self.validate_button = ctk.CTkButton(self, text="Valider", command=self.validate_task, height=40)
        self.validate_button.pack(pady=15)

        # État courant
        self.current_task = None
        self.selected_task_id = None

        # Centrer la fenêtre sur l'écran
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def refresh_task_list(self):
        self.task_listbox.configure(state="normal")
        self.task_listbox.delete("0.0", "end")
        for t in self.tasks:
            line = (
                f'{t["task_id"]} : {t["description"]} '
                f'(Difficulté: {t.get("difficulty", "-")}, Objets: {", ".join(t.get("objects_involved", []))})\n'
            )
            self.task_listbox.insert("end", line)
        self.task_listbox.configure(state="disabled")

    def clear_fields(self):
        for w in (self.task_id_entry, self.description_entry,
                  self.criteria_entry, self.difficulty_entry, self.objects_entry):
            w.configure(state="normal")
            w.delete(0, "end")

    def fill_fields(self, task):
        for widget, text in [
            (self.task_id_entry, task["task_id"]),
            (self.description_entry, task["description"]),
            (self.criteria_entry, task.get("success_criteria", "")),
            (self.difficulty_entry, task.get("difficulty", "")),
            (self.objects_entry, ", ".join(task.get("objects_involved", []))),
        ]:
            widget.insert(0, text)
            widget.configure(state="disabled")

    def on_task_selected(self, event):
        task_id = self.task_select.get()
        if task_id == "<Nouvelle tâche>":
            self.current_task = None
            self.clear_fields()
            self.status_label.configure(text="Création d'une nouvelle tâche")
        else:
            task = next((t for t in self.tasks if t["task_id"] == task_id), None)
            if task:
                self.current_task = task
                self.clear_fields()
                self.fill_fields(task)
                messagebox.showinfo("Tâche sélectionnée", f"Tâche '{task_id}' sélectionnée. Démarrage immédiat.")
                self.selected_task_id = task_id
                self.destroy()
            else:
                self.current_task = None
                self.status_label.configure(text="")

    def validate_task(self):
        task_id_selection = self.task_select.get()

        if task_id_selection != "<Nouvelle tâche>":
            if not task_id_selection or task_id_selection == "Sélectionner une tâche":
                messagebox.showerror("Erreur", "Veuillez sélectionner une tâche existante ou créer une nouvelle.")
                return

            self.selected_task_id = task_id_selection
            messagebox.showinfo("Succès", f"Tâche existante '{self.selected_task_id}' sélectionnée.")
            self.destroy()
            return

        # Création nouvelle tâche
        task_id     = self.task_id_entry.get().strip()
        description = self.description_entry.get().strip()
        criteria    = self.criteria_entry.get().strip()
        difficulty  = self.difficulty_entry.get().strip()
        objects     = [o.strip() for o in self.objects_entry.get().split(',') if o.strip()]

        if not task_id or not description:
            messagebox.showerror("Erreur", "Les champs 'ID de la tâche' et 'Description' sont obligatoires.")
            return

        if any(t["task_id"] == task_id for t in self.tasks):
            messagebox.showerror("Erreur", "Ce task_id existe déjà.")
            return

        new_task = {
            "task_index": get_next_task_index(),
            "task_id": task_id,
            "description": description,
            "success_criteria": criteria,
            "difficulty": difficulty,
            "objects_involved": objects
        }
        append_jsonl(TASKS_PATH, new_task)
        self.tasks.append(new_task)
        self.refresh_task_list()
        messagebox.showinfo("Succès", f"Nouvelle tâche '{task_id}' ajoutée.")
        self.selected_task_id = task_id
        self.destroy()


def lancer_ihm_task():
    app = TaskSelector()
    app.mainloop()
    return app.selected_task_id

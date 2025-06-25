import customtkinter as ctk
from ui.IHM import lancer_ihm_task
from ui.episode_recorder import lancer_collecteur
from utils.file_utils import init_info_json

if __name__ == "__main__":
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")
    init_info_json()

    while True:
        # Lancer la fenêtre de sélection/création de tâche
        task_id = lancer_ihm_task()

        if not task_id:
            print("Aucune tâche sélectionnée, fin du programme.")
            break

        relancer_episode = True
        while relancer_episode:
            relancer_episode = lancer_collecteur(task_id)

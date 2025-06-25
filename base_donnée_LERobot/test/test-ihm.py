import customtkinter as ctk
import jsonlines

class RecipeSelector(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sélecteur de Recette")

        # Lire les recettes existantes
        self.recipe_list = self.load_recipes("recipes.jsonl")
        self.recipe_ids = [r["recipe_id"] for r in self.recipe_list]
        self.recipe_ids.append("➕ Nouvelle recette")

        # Menu déroulant
        self.option_menu = ctk.CTkOptionMenu(self, values=self.recipe_ids, command=self.on_select)
        self.option_menu.pack(pady=10)

        # Champ pour nouvelle recette
        self.new_recipe_entry = ctk.CTkEntry(self, placeholder_text="Nom de la nouvelle recette")
        self.new_recipe_entry.pack(pady=10)
        self.new_recipe_entry.configure(state="disabled")  # Désactivé tant que pas sélectionné

        # Bouton valider
        self.confirm_button = ctk.CTkButton(self, text="Valider", command=self.on_confirm)
        self.confirm_button.pack(pady=10)

    def load_recipes(self, path):
        recipes = []
        try:
            with jsonlines.open(path) as reader:
                for obj in reader:
                    recipes.append(obj)
        except FileNotFoundError:
            pass
        return recipes

    def on_select(self, choice):
        if choice == "➕ Nouvelle recette":
            self.new_recipe_entry.configure(state="normal")
        else:
            self.new_recipe_entry.delete(0, "end")
            self.new_recipe_entry.configure(state="disabled")

    def on_confirm(self):
        selected = self.option_menu.get()
        if selected == "➕ Nouvelle recette":
            new_name = self.new_recipe_entry.get().strip()
            if new_name:
                print(f"Nouvelle recette à créer : {new_name}")
                # Ici tu pourrais écrire dans `recipes.jsonl`
            else:
                print("Erreur : champ vide.")
        else:
            print(f"Recette sélectionnée : {selected}")


if __name__ == "__main__":
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    app = RecipeSelector()
    app.mainloop()

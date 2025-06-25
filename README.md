# Protocole de collecte – LeRobot

Ce dépôt contient un exemple minimal de protocole utilisé pour collecter des données robotiques. Il s’appuie sur **LeRobot**, une plateforme de collecte d’épisodes composée d’un bras robotique UR et de caméras RealSense. Les scripts fournis permettent d’enregistrer les données, de les organiser et de stocker les métadonnées nécessaires à l’exploitation du jeu de données.

Ce document décrit l’organisation du dépôt, les différents fichiers de configuration ainsi que le format des données.

## Organisation du dépôt

- `config/config.yaml` – paramètres généraux de la collecte (type de robot, fréquence, caméras, version…).
- `meta/` – métadonnées du jeu de données :
  - `info.json` – résumé global (nombre d’épisodes, version, etc.).
  - `episodes.jsonl` – description de chaque épisode enregistré.
  - `tasks.jsonl` – liste des tâches disponibles.
- `data/` – dossiers contenant les fichiers `.parquet` avec les données brutes (un fichier par épisode ou par chunk).
- `images/` et `videos/` – enregistrements visuels optionnels associés aux épisodes.
- `ui/` – interfaces graphiques permettant de sélectionner une tâche puis de démarrer la collecte.
- `utils/` – fonctions utilitaires pour la gestion des fichiers.

La configuration par défaut crée un premier *chunk* nommé `chunk-000` pour stocker les épisodes. Les chemins exacts peuvent être modifiés dans `config.yaml`.

## Fichiers de configuration

### `config/config.yaml`

Ce fichier définit les paramètres généraux de la collecte :

```yaml
robot_type: UR10            # modèle du robot utilisé
fps: 20                     # fréquence d’enregistrement des données
control_frequency: 20       # fréquence de contrôle du robot
cameras:
  - id: 234322303360        # numéro de série RealSense associée à la pince
    position: gripper
  - id: 242422302403        # caméra fixe de scène
    position: static_scene
codebase_version: v2.1
```

### `meta/info.json`

Ce fichier contient un résumé global du jeu de données. Les champs principaux sont :

- `codebase_version` (*string*, obligatoire) – version du format de dataset.
- `robot_type` (*string*, obligatoire) – modèle de robot utilisé.
- `total_episodes` (*int*, obligatoire) – nombre d’épisodes collectés.
- `total_frames` (*int*, obligatoire) – nombre total de trames.
- `fps` (*int/float*, obligatoire) – fréquence d’enregistrement des données.
- `splits` (*object*, obligatoire) – découpage *train/val/test* des épisodes.
- `features` (*object*, obligatoire) – description des colonnes présentes dans les fichiers `.parquet`.
- `camera_keys` (*array*, obligatoire) – clés des flux caméra utilisés.
- `total_tasks`, `total_videos`, `total_chunks`, `chunks_size`, `data_path` et `video_path` sont optionnels et décrivent respectivement le nombre de tâches, de vidéos, la structure des *chunks*, et le gabarit des chemins où sont stockées les données.

### `meta/tasks.jsonl`

Chaque ligne décrit une tâche disponible :

```json
{"task_id": "ouvrir_tiroir", "description": "Ouvrir le tiroir", "success_criteria": "tiroir entièrement ouvert", "difficulty": "facile", "objects_involved": ["tiroir"]}
```

- `task_id` – identifiant unique utilisé dans les épisodes.
- `description` – phrase en langage naturel décrivant l’action à réaliser.
- `success_criteria` – condition permettant de déterminer la réussite de la tâche.
- `difficulty` – niveau de difficulté (libre).
- `objects_involved` – objets manipulés ou observés.

### `meta/episodes.jsonl`

Chaque ligne correspond à un épisode enregistré :

```json
{"episode_index": 0, "tasks": ["ouvrir_tiroir"], "length": 120, "success": true, "cameras": ["cam_gripper", "cam_scene"]}
```

- `episode_index` – numéro séquentiel de l’épisode.
- `tasks` – liste des tâches associées.
- `length` – nombre de frames dans le fichier `.parquet` correspondant.
- `success` – booléen indiquant la réussite de l’épisode.
- `cameras` – caméras utilisées pendant l’enregistrement.

## Format des données `.parquet`

Chaque fichier `.parquet` représente un épisode (ou un chunk d’épisodes) et contient une ligne par frame. Les colonnes par défaut sont :

- `action` – commande envoyée au robot.
- `timestamp` – temps écoulé depuis le début de l’épisode.
- `robot_obs` – observations brutes du robot (joints, efforts…).
- `cameras` – dictionnaire des chemins vers les images RGB et profondeur par caméra.
- `ee_pose` – position et orientation de l’effecteur.
- `ee_velocity` – vitesse de l’effecteur.
- `gripper_state` – état de la pince.
- `task_id` – identifiant de la tâche enregistrée.

Exemple de structure pour le champ `cameras` :

```json
{
  "rgb_eye": "images/chunk-000/000001/rgb_cam_gripper/000000.png",
  "rgb_env": "images/chunk-000/000001/rgb_cam_scene/000000.png",
  "depth_eye": "images/chunk-000/000001/depth_cam_gripper/000000.png",
  "depth_env": "images/chunk-000/000001/depth_cam_scene/000000.png"
}
```

## Lancer la collecte

1. Installer les dépendances listées dans `requirements.txt` (ROS 2, `pyrealsense2`, `pyarrow`, etc.).
2. Exécuter `python main.py` pour lancer l’interface graphique.
3. Sélectionner ou créer une tâche, puis démarrer l’enregistrement d’un épisode.
4. À la fin de l’épisode, les données sont enregistrées dans `data/`, les images/vidéos dans `images/` ou `videos/`, et les métadonnées mises à jour dans `meta/`.

Les fonctions utilitaires de `utils/file_utils.py` permettent de lire et mettre à jour les fichiers JSON/JSONL, tandis que `utils/video_utils.py` gère l’encodage vidéo.

## Lecture des données

Les fichiers `.parquet` peuvent être chargés avec `pandas` :

```python
import pandas as pd

# Chargement d’un épisode
df = pd.read_parquet("data/chunk-000/000001.parquet")
print(df.head())
```

Les métadonnées (tâches et épisodes) peuvent être lues grâce aux fonctions fournies dans `utils/file_utils.py`.

## Licence

Ce dépôt est fourni à titre d’exemple et ne contient qu’un jeu de données minimal pour illustrer la structure de **LeRobot**. Adaptez-le à vos besoins pour la collecte ou l’exploitation de vos propres données.


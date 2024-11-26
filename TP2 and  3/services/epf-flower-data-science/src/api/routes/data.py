import os
import json
import zipfile
import kaggle
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pathlib import Path
from pydantic import BaseModel, Field

# Charger les informations sur les datasets à partir du fichier JSON
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # 3 niveaux pour arriver à la racine du projet
DATASETS_FILE = BASE_DIR  / 'config' / 'data.json'
print("DATASETS_FILE", DATASETS_FILE)
# Vérifier si le fichier JSON existe
if not DATASETS_FILE.exists():
    raise Exception(f"Le fichier {DATASETS_FILE} est manquant!")

with open(DATASETS_FILE, 'r') as f:
    datasets_info = json.load(f)

# Créer le routeur FastAPI
router = APIRouter()

# Dossier où nous allons stocker les données
DATA_DIR = Path(__file__).resolve().parent.parent.parent / 'src' / 'data'

# Assurez-vous que le dossier existe
DATA_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/download-dataset/{dataset_name}")
async def download_dataset(dataset_name: str):
    # Vérifier si le dataset existe dans le fichier JSON
    if dataset_name not in datasets_info:
        raise HTTPException(status_code=404, detail="Dataset non trouvé dans le fichier JSON.")
    
    dataset_info = datasets_info[dataset_name]
    dataset_path = DATA_DIR / f"{dataset_name}.zip"
    
    # Télécharger le dataset depuis Kaggle
    if not dataset_path.exists():
        try:
            print(f"Téléchargement du dataset {dataset_name}...")
            kaggle.api.dataset_download_files(dataset_info["url"], path=str(DATA_DIR), unzip=False)
            print(f"Téléchargement terminé pour {dataset_name}.")
            
            # Décompresser le fichier zip
            with zipfile.ZipFile(dataset_path, 'r') as zip_ref:
                zip_ref.extractall(DATA_DIR)
            
            # Supprimer le zip après extraction
            os.remove(dataset_path)
            print(f"Décompression du dataset {dataset_name} terminée.")
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement ou de l'extraction du dataset {dataset_name}: {str(e)}")
    
    return {"message": f"Dataset {dataset_name} téléchargé et extrait avec succès!"}





# Pydantic model pour valider les données du nouveau dataset
class Dataset(BaseModel):
    name: str = Field(..., description="Le nom du dataset")
    url: str = Field(..., description="L'URL du dataset sur Kaggle")

@router.post("/add-dataset")
async def add_dataset(dataset: Dataset):
    # Vérifier si le dataset existe déjà dans le fichier JSON
    if dataset.name in datasets_info:
        raise HTTPException(status_code=400, detail="Ce dataset existe déjà dans le fichier de configuration.")
    
    # Ajouter le dataset au fichier JSON
    datasets_info[dataset.name] = {
        "name": dataset.name,
        "url": dataset.url
    }
    
    # Mettre à jour le fichier JSON
    try:
        with open(DATASETS_FILE, 'w') as f:
            json.dump(datasets_info, f, indent=4)
        
        return {"message": f"Le dataset {dataset.name} a été ajouté avec succès!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajout du dataset: {str(e)}")



@router.post("/modify-dataset")
async def modify_dataset(action: str, dataset_name: str, dataset: Dataset = None):
    # Charger les datasets actuels
    if action not in ['update', 'delete']:
        raise HTTPException(status_code=400, detail="Action non valide. Utilisez 'add', 'update' ou 'delete'.")

    
    elif action == 'update':
        # Mettre à jour un dataset existant
        datasets_info[dataset_name].update({
            "name": dataset.name,
            "url": dataset.url
        })
        return {"message": f"Le dataset {dataset_name} a été mis à jour avec succès!"}
    
    elif action == 'delete':
        # Supprimer un dataset existant
        del datasets_info[dataset_name]
        return {"message": f"Le dataset {dataset_name} a été supprimé avec succès!"}

    # Mettre à jour le fichier JSON
    try:
        with open(DATASETS_FILE, 'w') as f:
            json.dump(datasets_info, f, indent=4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour du fichier JSON: {str(e)}")




# Architecture — Backend Litigo

Litigo est un backend Python pour automatiser une partie de la due diligence TPLF
(`Third Party Litigation Funding`). L'objectif est de recevoir ou analyser une
décision juridique, extraire des informations structurées, identifier des
entreprises potentiellement victimes, les analyser, sélectionner les meilleures
opportunités, puis générer un rapport professionnel.

Référence d'inspiration :
https://github.com/LouisPages/2026ParisFinTech/tree/main/backend

## 1. Objectif Du Backend

Le backend expose une API FastAPI qui doit progressivement supporter ce flux :

```text
Upload / réception d'une décision juridique
        ↓
Extraction de données judiciaires structurées
        ↓
Exécution du pipeline agentique
        ↓
Recherche d'entreprises candidates
        ↓
Sélection des meilleures opportunités TPLF
        ↓
Génération d'un rapport téléchargeable
```

## 2. Structure Actuelle Du Projet

```text
backend/
  api/v1/routes/       Routes HTTP groupées par version d'API
  cache/               Fichiers de cache générés pendant les analyses
  models/              Schémas Pydantic pour valider les formes de données
  pipeline/            Workflow LangGraph et orchestration
  pipeline/nodes/      Étapes individuelles du pipeline agentique
  services/            Logique backend réutilisable
  tools/               Outils externes et intégrations
  config.py            Chargement de la configuration et des variables d'env
  main.py              Point d'entrée FastAPI
  requirements.txt     Dépendances Python
  test_llm.py          Test simple de connexion Gemini
```

## 3. Rôle Des Dossiers

`api/` contient les routes HTTP. Une route répond à des questions comme :
quelle URL existe, quelle méthode HTTP elle utilise, et quelle réponse elle
renvoie.

`models/` contient les schémas. Un schéma définit la forme exacte d'une donnée.
Par exemple, une réponse de statut de job doit toujours contenir `status`,
`progress_pct` et `message`.

`pipeline/` contient le workflow principal. C'est ici que LangGraph reliera les
étapes entre elles.

`pipeline/nodes/` contient un fichier par étape du pipeline : analyse du
document, sourcing d'entreprises, recherche, sélection, rédaction du rapport,
génération du document.

`services/` contient la logique réutilisable qui n'est pas directement une route
HTTP : gestion des jobs, extraction de texte, cache, génération de rapports.

`tools/` contient les wrappers autour de systèmes externes : Gemini Grounding,
futures APIs financières, ou fournisseurs de données entreprises.

`cache/` stocke des données générées à l'exécution. Ce n'est pas du code source,
donc son contenu doit généralement être ignoré par git.

## 4. Notes Sur Les Packages Python

Un dossier Python devient importable de façon explicite lorsqu'il contient un
fichier `__init__.py`.

Exemple :

```text
api/v1/routes/health.py
```

peut être importé avec :

```py
from api.v1.routes import health
```

`__pycache__` est différent. On ne le crée pas à la main. Python le crée
automatiquement quand des fichiers Python sont importés, exécutés ou compilés.

Commande utile :

```sh
uv run python -m compileall .
```

## 5. Stratégie De Dépendances

Ce backend utilise `requirements.txt`, comme le backend de référence.

On utilise `uv` comme outil d'environnement et d'exécution :

```sh
uv venv
uv pip install -r requirements.txt
uv run python test_llm.py
uv run uvicorn main:app --reload
```

`requirements.txt` décrit ce dont l'application a besoin. `uv` installe et lance
ces dépendances rapidement.

## 6. Point D'entrée Runtime

`main.py` est le point d'entrée FastAPI.

En local ou sur Railway, Uvicorn chargera :

```sh
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Ce qui signifie :

```text
main.py -> le fichier Python
app     -> l'objet FastAPI dans ce fichier
```

## 7. API Cible

Les endpoints doivent être construits petit à petit :

```text
GET  /api/v1/health
POST /api/v1/analysis/upload
POST /api/v1/analysis/start
GET  /api/v1/analysis/{job_id}/status
GET  /api/v1/analysis/{job_id}/result
GET  /api/v1/analysis/{job_id}/stream
```

On commence par `/health`, car cela prouve que le backend démarre correctement
avant d'ajouter la logique complexe du pipeline.

## 8. Pipeline Cible

Le pipeline final ressemblera à ceci :

```text
document_analyzer
        ↓
company_sourcing
        ↓
company_research
        ↓
selection_agent
        ↓
report_writer
        ↓
document_generator
```

Chaque étape reçoit un état structuré et renvoie des modifications de cet état.

## 9. Pourquoi Utiliser Des Schémas / Models

Les schémas évitent de faire circuler des dictionnaires aléatoires partout dans
le backend.

Moins bien :

```py
return {"thing": "maybe", "data": 123}
```

Mieux :

```py
class AnalysisStatusResponse(BaseModel):
    status: str
    progress_pct: float
    message: str
```

Les schémas aident pour la validation, l'autocomplétion, la documentation API,
l'intégration frontend et le débogage.

## 10. Déploiement Railway

Railway doit déployer le service backend depuis le dossier `backend/`.

Commande de production attendue :

```sh
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Les variables comme `GOOGLE_API_KEY` doivent être configurées dans Railway, pas
écrites en dur dans les fichiers Python.

## 11. Roadmap De Développement

1. Endpoint de santé `/health`
2. Endpoint d'upload de document
3. Service d'extraction de texte
4. Service de gestion des jobs
5. Premier modèle d'état du pipeline
6. Node `document_analyzer`
7. Node `company_sourcing`
8. Node `company_research`
9. Node `report_writer`
10. Déploiement Railway

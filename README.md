# Alteris project

## Description du projet
Alteris est une application web full-stack pour le suivi des apprentis (promotions, semestres, livrables, journaux, entretiens, juries) avec gestion des roles (apprenti, tuteur, maitre, enseignants, coordination, admin).

## Instructions d'installation
Prerequis:
- Node.js (LTS)
- Python 3.11+
- MongoDB local

Backend:
1. Ouvrir un terminal dans `backend`.
2. Creer un environnement virtuel Python et l'activer.
3. Installer les dependances: `pip install -r requirements.txt`

Frontend:
1. Ouvrir un terminal dans `frontend`.
2. Installer les dependances: `npm install`

## Instructions d'execution
Backend (tous les microservices):
1. Depuis `backend`: `python run_all_apis.py`

Frontend:
1. Depuis `frontend`: `npm run dev`
2. Acceder a l'application: http://localhost:5173

Notes:
- Les services FastAPI exposent leurs docs sur `/docs`.
- Verifier les URLs dans `frontend/src/config.ts` si besoin.

## Comptes de test
/

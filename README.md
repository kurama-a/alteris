# Alteris project

## Description
Alteris est une application web full-stack pour le suivi des apprentis : promotions, semestres, livrables, journaux, entretiens et jurys, avec gestion des roles (apprenti, tuteur, maitre, enseignants, coordination, admin).

## Installation
Prerequis :
- Node.js (LTS)
- Python 3.11+
- MongoDB local

Backend :
1. Ouvrir un terminal dans `backend`.
2. Creer et activer un environnement virtuel.
3. Installer les dependances : `pip install -r requirements.txt`

Frontend :
1. Ouvrir un terminal dans `frontend`.
2. Installer les dependances : `npm install`

MongoDB (optionnel) :
1. Ouvrir un terminal.
2. Restaurer le dump :
   `mongorestore --db alternance_db --drop ./dump_mongo/alternance_db`

## Execution
Backend (tous les microservices) :
- Depuis `backend` : `python run_all_apis.py`

Frontend :
- Depuis `frontend` : `npm run dev`
- Ouvrir : http://localhost:5173

Notes :
- Les docs FastAPI sont disponibles sur `/docs`.
- Verifier les URLs dans `frontend/src/config.ts` si besoin.

## Guide utilisateur (rapide)
Connexion :
1. Aller sur http://localhost:5173.
2. Se connecter avec le role adapte.

Navigation :
- Accueil : calendrier, livrables, deadlines.
- Journal : documents par semestre, commentaires, telechargements.
- Entretiens : planifier, suivre, valider.
- Jurys : consulter les jurys programmes et leurs documents.
- Admin : utilisateurs, promotions, parametres.

Actions courantes :
- Apprenti : Journal -> semestre -> Deposer.
- Tuteur/Maitre : Entretiens -> Accepter/Refuser ; Journal -> commenter.
- Admin/Coordination/Responsable : gestion des promotions et utilisateurs.

## Comptes de test
Si le dump Mongo est importe, vous pouvez utiliser :

Administrateur :
- pierre.delarue123@admin.fr
- Admin123!56

Apprenti :
- jean.dupont123@reseaualternance.fr
- 9E2o78dYjp

Apprenti :
- arthur.adrien@reseaualternant.fr
- Apprenti123

Maitre d'apprentissage :
- maitre.test78@maitre.reseaualternance.fr
- MCOpTJVg67

Tuteur pedagogique :
- paul.paul@tuteurpedagogique.fr
- MCOpTJVg67

Coordinatrice :
- priscilliajova@coordinatrice.com
- securePassword123

Professeur :
- henryleprof@professeur.com
- securePassword123

## Captures d'ecran
Page de connexion :
![Login](/captures/Login.png)

Page d'accueil :
![Accueil](/captures/accueil.png)

Journal :
![Journal](/captures/Journal.png)

Entretiens :
![Entretiens](/captures/Entretiens.png)

Jurys :
![Jury](/captures/Juries.png)

Administration :
![Admin](/captures/Admin.png)

Exemple de promotion :
![Promotions](/captures/Promotions.png)

# Servants d’autel · Paroisse Saint François d’Assise

Application Django en **temps réel** (WebSockets, Django Channels).
Quand un membre du bureau modifie une donnée (paiement, présence, servant…), tous les autres appareils connectés la voient immédiatement.

- **Visiteurs (servants)** : page d’accueil publique, programme d’activités, annonces, formulaires WhatsApp. Lecture seule.
- **Membres du bureau** : connexion par nom d’utilisateur et mot de passe, accès à toute l’application, synchronisée en direct.
- **Administrateur** : crée les comptes dans `/admin/` et consulte le **journal des paiements** (qui a modifié quoi, quand).

## Déployer sur Render (gratuit pour tester)

1. Mettez ce dossier sur **GitHub** (nouveau dépôt, privé de préférence).
2. Sur [render.com](https://render.com) : **New → Blueprint**, choisissez le dépôt. Render lit `render.yaml` et crée :
   le site web, la base **PostgreSQL** et le **Redis** (Key Value) qui relaie les messages en temps réel.
3. Quand Render demande les variables, renseignez :
   - `DJANGO_SUPERUSER_USERNAME` : votre nom d’utilisateur administrateur
   - `DJANGO_SUPERUSER_EMAIL` : votre e-mail
   - `DJANGO_SUPERUSER_PASSWORD` : un mot de passe solide (8 caractères minimum)
4. Attendez la fin du déploiement, puis ouvrez l’adresse `https://....onrender.com`.
5. Cliquez sur **Espace bureau** et connectez-vous. Dans le tableau de bord : **Gérer les comptes** pour créer ceux du Trésorier et des autres membres.

Au premier démarrage, la liste des servants et le programme 2026-2027 sont chargés automatiquement (une seule fois).

### À savoir sur l’offre gratuite de Render
- Le site **s’endort après environ 15 minutes sans visite** : la première ouverture peut prendre une minute.
- La base PostgreSQL **gratuite expire après 30 jours**. Pour des paiements réels, passez à une offre payante de base de données avant ce délai.
Vérifiez les conditions actuelles sur render.com/pricing.

## Lancer en local (test sur ordinateur)

```bash
python -m venv venv && source venv/bin/activate      # Windows : venv\Scripts\activate
pip install -r requirements.txt
export DEBUG=1                                         # Windows : set DEBUG=1
python manage.py migrate
python manage.py seed
python manage.py createsuperuser
python manage.py runserver
```
Ouvrez http://127.0.0.1:8000 (ouvrez-le dans deux fenêtres pour voir la synchronisation).

## Comment ça marche
- `core/consumers.py` : le serveur WebSocket. Il envoie toutes les données à la connexion, enregistre chaque modification en base, puis la diffuse aux autres appareils.
- Les listes de présence sont modifiées **membre par membre** côté serveur : deux personnes qui cochent en même temps ne s’écrasent pas.
- Hors ligne, l’écran se bloque en lecture seule et se reconnecte tout seul, pour éviter des paiements enregistrés de travers.
- `templates/app.html` : toute l’interface (écran d’accueil animé, programme, annonces, formulaires, bureau).

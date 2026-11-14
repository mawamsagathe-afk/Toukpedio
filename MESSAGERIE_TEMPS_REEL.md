# Messagerie temps réel TOUKPEDIO

## Installation locale

Depuis la racine du projet :

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

En mode développement, Channels utilise par défaut sa couche mémoire. Elle
permet de tester les WebSockets sur un seul processus, mais ne convient pas à
plusieurs processus ou serveurs.

## Redis et production

Lancer Redis localement avec Docker pour tester la couche Redis :

```powershell
docker run --name toukpedio-redis -p 6379:6379 -d redis:7-alpine
```

Configurer les variables d'environnement de production :

```text
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<clé secrète générée et conservée hors du dépôt>
DJANGO_ALLOWED_HOSTS=app.example.com
REDIS_URL=redis://redis.example.internal:6379/0
```

Utiliser un Redis privé, protégé par authentification et TLS lorsque le
fournisseur le permet. Ne pas exposer Redis à Internet. En production, la
configuration refuse de démarrer sans `DJANGO_SECRET_KEY` et `REDIS_URL`.

L'application doit être servie par un serveur ASGI pour accepter les
WebSockets, par exemple :

```powershell
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

Le proxy HTTPS doit transmettre les connexions `Upgrade: websocket` et servir
le site en HTTPS afin que le navigateur utilise `wss://`.

## Comptes, confidentialité et limites

- Les comptes parents sont les utilisateurs disposant d'un profil `Parent`.
- Les professionnels disponibles sont les comptes actifs avec `is_staff=True`
  (le projet ne possède pas encore de rôles distincts médecin/infirmier).
- Une conversation est accessible uniquement à son parent et au professionnel
  auquel elle est attribuée. Un autre compte staff ne peut pas la lire.
- Les messages texte sont conservés dans la base. Le navigateur échappe le
  contenu comme du texte et non comme du HTML.
- La boîte de réception et les conversations reçoivent les nouveaux messages
  via WebSocket. Les notifications du navigateur nécessitent l'autorisation de
  l'utilisateur et une page de messagerie ouverte. Il ne s'agit pas de
  notifications push lorsque le navigateur est fermé.
- Les pièces jointes ne sont pas activées : elles nécessitent un stockage privé
  protégé et contrôlé, qui n'est pas configuré dans le projet.
- La messagerie ne remplace pas un service d'urgence ni un dossier médical.

# Déploiement sur Vercel

Le projet utilise la détection Django de Vercel : `manage.py` est à la racine
et `ASGI_APPLICATION = "config.asgi.application"` est déclaré dans les réglages.
Aucun `vercel.json` ni commande de build personnalisée n'est nécessaire.
Vercel construit les fichiers statiques lorsque `STATIC_ROOT` est configuré.

## Services à configurer

Dans **Project Settings > Environment Variables**, ajouter les variables
suivantes pour les environnements Preview et Production :

| Variable | Valeur |
| --- | --- |
| `DJANGO_SECRET_KEY` | Une clé Django aléatoire, différente de toute clé locale |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_ALLOWED_HOSTS` | `*` (ou les noms de domaine séparés par des virgules) |
| `DATABASE_URL` | URL d'une base PostgreSQL persistante |
| `REDIS_URL` | URL d'un service Redis accessible par Vercel |

La clé peut être générée avec :

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Le projet refuse de démarrer sur Vercel sans `DATABASE_URL` : SQLite et le
système de fichiers d'une Function ne fournissent pas de stockage persistant.
L'URL PostgreSQL doit être accessible depuis Vercel et utiliser TLS en
production. `REDIS_URL` est nécessaire à la messagerie Channels. Vercel prend
en charge ASGI et les WebSockets ; un Redis externe est requis pour partager
les messages entre les instances.

Les fichiers téléversés dans `media/` ne sont pas persistants sur Vercel. Avant
d'activer les téléversements en production, configurer un stockage objet
externe et faire pointer Django vers ce stockage.

## Déployer

1. Importer le dépôt Git dans Vercel et garder la racine du projet par défaut.
2. Ajouter les variables ci-dessus avant le premier déploiement.
3. Déployer. Vercel détecte Django, utilise `config.asgi:application` et
   collecte les fichiers statiques dans `staticfiles/`.
4. Pour initialiser ou mettre à jour le schéma, récupérer les variables de
   Production puis lancer les migrations depuis le projet :

```powershell
vercel env pull .env.local --environment=production
python manage.py migrate
```

Les clés et URL contenues dans `.env.local` ne doivent pas être ajoutées au
dépôt. Les variables locales déjà définies dans le terminal ont priorité sur
les valeurs chargées depuis les fichiers `.env`.

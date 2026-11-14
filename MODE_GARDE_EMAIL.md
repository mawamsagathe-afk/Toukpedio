# Envoi de la fiche Mode de garde

La création d'une fiche Mode de garde nécessite une adresse e-mail valide pour
la personne qui garde l'enfant. Le lien personnel est un UUID aléatoire unique,
valable pendant `MODE_GARDE_TOKEN_VALIDITY_DAYS` (7 jours par défaut). Le parent
peut le révoquer depuis le détail de la fiche. L'URL publique ne permet que la
lecture des informations explicitement sélectionnées dans la fiche et n'expose
aucun lien vers les autres dossiers de l'enfant.

## Configuration

Renseignez dans le fichier `.env` non commité les paramètres SMTP déjà utilisés
par Django :

```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=adresse-expediteur@example.com
EMAIL_HOST_PASSWORD=mot-de-passe-application
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
DEFAULT_FROM_EMAIL=adresse-expediteur@example.com
MODE_GARDE_TOKEN_VALIDITY_DAYS=7
```

Remplacez les paramètres d'hôte et de port par ceux du fournisseur SMTP choisi.
Pour Gmail, utilisez un mot de passe d'application si votre compte le requiert ;
ne placez jamais le mot de passe du compte ou d'application dans le code.

Après déploiement, appliquez :

```powershell
python manage.py migrate
python manage.py check
python manage.py test sante.test_mode_garde_email
```

En production, servez TOUKPEDIO exclusivement en HTTPS et configurez le
serveur proxy pour que Django reconnaisse correctement les requêtes HTTPS. Le
lien envoyé par e-mail est un secret d'accès temporaire à la fiche.

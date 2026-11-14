# Rappels de vaccination

TOUKPEDIO réutilise l'adresse `User.email` du parent et le numéro
`Enfant.telephone_parent`. Le consentement WhatsApp est conservé par dossier
d'enfant et reste désactivé par défaut, y compris pour les dossiers existants.
Les échéances J-3, J-1 et J0 sont créées pour les vaccins à venir et sont
dédupliquées par vaccin, canal et délai.

## Configuration

Copiez `.env.example` vers `.env` et renseignez les identifiants SMTP sans les
commiter. Le champ `EMAIL_HOST_PASSWORD` reste uniquement dans l'environnement.
L'e-mail est envoyé à l'adresse du compte parent renseignée dans le formulaire
de l'enfant.

Pour WhatsApp, configurez `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` et
`WHATSAPP_API_VERSION`. Créez et faites approuver dans WhatsApp Business un
modèle statique, sans variable ni donnée médicale, dont le texte informe le
parent qu'un rappel TOUKPEDIO est disponible dans l'application. Renseignez son
nom exact dans `WHATSAPP_TEMPLATE_NAME` et son code de langue dans
`WHATSAPP_TEMPLATE_LANGUAGE`. Aucun message WhatsApp n'est envoyé sans numéro,
consentement explicite, configuration et acceptation retournée par l'API.

## Exécution planifiée

Après `python manage.py migrate`, vérifiez l'échéancier avec :

```powershell
.\.venv\Scripts\python.exe manage.py send_vaccination_reminders --dry-run
```

Le mode `--dry-run` ne crée aucun rappel et n'envoie rien. Pour envoyer les
rappels dus, exécutez :

```powershell
.\.venv\Scripts\python.exe manage.py send_vaccination_reminders
```

Dans le Planificateur de tâches Windows, créez une tâche quotidienne exécutant
`<racine-du-projet>\.venv\Scripts\python.exe` avec l'argument
`manage.py send_vaccination_reminders` et `<racine-du-projet>` comme dossier
de démarrage. Programmez-la à une heure adaptée au fuseau `TIME_ZONE` de
Django. Le résultat et les éventuelles erreurs sont enregistrés dans
`VaccinationRappel`; le nombre d'échecs est également indiqué par la commande.

Les e-mails de test automatisés utilisent le backend local en mémoire de
Django et ne contactent aucun serveur SMTP.

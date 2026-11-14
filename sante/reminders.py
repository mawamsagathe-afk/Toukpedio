import json
import re
from urllib import error as urllib_error
from urllib import request as urllib_request

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Vaccination, VaccinationRappel
from .vaccination_calendar import programmer_rappels_pour_vaccination


def _normaliser_telephone(telephone):
    if not telephone:
        return ""

    valeur = str(telephone).strip()
    chiffres = re.sub(r"\D", "", valeur)
    if not chiffres:
        return ""

    if valeur.startswith("00"):
        chiffres = chiffres[2:]
    if len(chiffres) == 9:
        chiffres = f"237{chiffres}"

    if not 8 <= len(chiffres) <= 15:
        return ""
    return chiffres


def _message_rappel(reminder):
    vaccination = reminder.vaccination
    enfant = vaccination.enfant
    parent = enfant.parent
    return (
        f"Bonjour {parent.username},\n\n"
        f"Nous vous rappelons que {enfant.prenom} {enfant.nom} a une vaccination prévue :\n"
        f"- Vaccin : {vaccination.nom_vaccin}\n"
        f"- Dose : {vaccination.dose or 'Non précisée'}\n"
        f"- Date prévue : {vaccination.date_prevue.isoformat() if vaccination.date_prevue else 'à confirmer'}\n\n"
        "Merci de bien vouloir respecter le calendrier de vaccination.\n\n"
        "Ceci est un rappel automatique TOUKPEDIO."
    )


def send_email_reminder(reminder):
    if reminder.canal != "email":
        return False

    user = reminder.vaccination.enfant.parent
    recipient = (user.email or "").strip()
    if not recipient:
        raise ValueError("Aucune adresse email connue pour ce parent.")

    subject = "Rappel de vaccination TOUKPEDIO"
    message = _message_rappel(reminder)
    sent = send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        fail_silently=False,
    )
    if sent != 1:
        raise RuntimeError("Le backend e-mail n'a pas confirmé l'envoi.")

    reminder.statut = "envoye"
    reminder.date_tentative = timezone.now()
    reminder.resultat = f"Email envoyé à {recipient}"
    reminder.nombre_tentatives += 1
    reminder.save(update_fields=["statut", "date_tentative", "resultat", "nombre_tentatives", "updated_at"])
    return True


def send_whatsapp_reminder(reminder):
    if reminder.canal != "whatsapp":
        return False

    enfant = reminder.vaccination.enfant
    if not enfant.whatsapp_consent:
        reminder.statut = "annule"
        reminder.date_tentative = timezone.now()
        reminder.resultat = "Annulé : le parent n'a pas consenti aux rappels WhatsApp."
        reminder.save(
            update_fields=["statut", "date_tentative", "resultat", "updated_at"]
        )
        return False

    token = getattr(settings, "WHATSAPP_TOKEN", "")
    phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")
    if not token or not phone_number_id:
        raise ValueError("Configuration WhatsApp manquante (WHATSAPP_TOKEN / WHATSAPP_PHONE_NUMBER_ID).")

    template_name = getattr(settings, "WHATSAPP_TEMPLATE_NAME", "")
    template_language = getattr(settings, "WHATSAPP_TEMPLATE_LANGUAGE", "")
    if not template_name or not template_language:
        raise ValueError(
            "Configuration du modèle WhatsApp manquante "
            "(WHATSAPP_TEMPLATE_NAME / WHATSAPP_TEMPLATE_LANGUAGE)."
        )

    numero = _normaliser_telephone(enfant.telephone_parent)
    if not numero:
        raise ValueError("Aucun numéro WhatsApp connu pour cet enfant.")

    api_version = getattr(settings, "WHATSAPP_API_VERSION", "v18.0") or "v18.0"
    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": template_language},
        },
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    request = urllib_request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib_request.urlopen(request, timeout=25) as response:
            response_body = response.read().decode("utf-8") or "{}"
            payload = json.loads(response_body)
    except urllib_error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Échec WhatsApp API: {body[:500]}") from exc

    message_ids = payload.get("messages") or []
    if not message_ids or not message_ids[0].get("id"):
        raise RuntimeError(
            "L'API WhatsApp n'a pas confirmé l'acceptation du message."
        )

    reminder.statut = "envoye"
    reminder.date_tentative = timezone.now()
    reminder.resultat = "Message WhatsApp accepté par l'API."
    reminder.fournisseur_message_id = message_ids[0]["id"]
    reminder.nombre_tentatives += 1
    reminder.save(
        update_fields=[
            "statut",
            "date_tentative",
            "resultat",
            "fournisseur_message_id",
            "nombre_tentatives",
            "updated_at",
        ]
    )
    return True


def send_reminder(reminder):
    if reminder.canal == "email":
        return send_email_reminder(reminder)
    if reminder.canal == "whatsapp":
        return send_whatsapp_reminder(reminder)
    raise ValueError(f"Canal de rappel inconnu : {reminder.canal}")


def send_due_vaccination_reminders():
    reminders = (
        VaccinationRappel.objects.filter(
            statut="planifie",
            date_tentative__lte=timezone.now(),
        )
        .select_related("vaccination__enfant__parent")
        .order_by("date_tentative")
    )

    total = 0
    for reminder in reminders:
        try:
            if send_reminder(reminder):
                total += 1
        except Exception as exc:
            reminder.statut = "echec"
            reminder.date_tentative = timezone.now()
            reminder.resultat = str(exc)[:500]
            reminder.nombre_tentatives += 1
            reminder.save(
                update_fields=[
                    "statut",
                    "date_tentative",
                    "resultat",
                    "nombre_tentatives",
                    "updated_at",
                ]
            )

    return total


def programmer_rappels_manquants():
    vaccinations = (
        Vaccination.objects.filter(
            date_prevue__gte=timezone.localdate(),
            date_effectuee__isnull=True,
        )
        .select_related("enfant__parent")
        .order_by("date_prevue", "pk")
    )
    return sum(
        1
        for vaccination in vaccinations
        for rappel in programmer_rappels_pour_vaccination(vaccination)
        if rappel["created"]
    )

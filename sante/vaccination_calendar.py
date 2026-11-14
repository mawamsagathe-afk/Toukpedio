from __future__ import annotations

from datetime import date, datetime, timedelta
import re
import unicodedata

from django.utils import timezone

CAMEROON_VACCINE_SCHEDULE = [
    {"nom_vaccin": "BCG", "dose": "Naissance", "age_recommande": "À la naissance", "jours_apres_naissance": 0},
    {"nom_vaccin": "VPO", "dose": "Dose 0", "age_recommande": "À la naissance", "jours_apres_naissance": 0},
    {"nom_vaccin": "DTCoq-HepB-Hib", "dose": "1ère dose", "age_recommande": "6 semaines", "jours_apres_naissance": 42},
    {"nom_vaccin": "DTCoq-HepB-Hib", "dose": "2ème dose", "age_recommande": "10 semaines", "jours_apres_naissance": 70},
    {"nom_vaccin": "DTCoq-HepB-Hib", "dose": "3ème dose", "age_recommande": "14 semaines", "jours_apres_naissance": 98},
    {"nom_vaccin": "Pneumocoque", "dose": "1ère dose", "age_recommande": "6 semaines", "jours_apres_naissance": 42},
    {"nom_vaccin": "Pneumocoque", "dose": "2ème dose", "age_recommande": "10 semaines", "jours_apres_naissance": 70},
    {"nom_vaccin": "Pneumocoque", "dose": "3ème dose", "age_recommande": "14 semaines", "jours_apres_naissance": 98},
    {"nom_vaccin": "Rota", "dose": "1ère dose", "age_recommande": "6 semaines", "jours_apres_naissance": 42},
    {"nom_vaccin": "Rota", "dose": "2ème dose", "age_recommande": "10 semaines", "jours_apres_naissance": 70},
    {"nom_vaccin": "VPO", "dose": "1ère dose", "age_recommande": "6 semaines", "jours_apres_naissance": 42},
    {"nom_vaccin": "VPO", "dose": "2ème dose", "age_recommande": "10 semaines", "jours_apres_naissance": 70},
    {"nom_vaccin": "VPO", "dose": "3ème dose", "age_recommande": "14 semaines", "jours_apres_naissance": 98},
    {"nom_vaccin": "RR", "dose": "1ère dose", "age_recommande": "9 mois", "jours_apres_naissance": 270},
    {"nom_vaccin": "Méningocoque", "dose": "1ère dose", "age_recommande": "9 mois", "jours_apres_naissance": 270},
    {"nom_vaccin": "Méningocoque", "dose": "2ème dose", "age_recommande": "15 mois", "jours_apres_naissance": 450},
]


def normaliser_texte(value):
    if value is None:
        return ""
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def _dose_correspond(dose_enregistre, dose_attendue):
    if not dose_attendue:
        return True
    if not dose_enregistre:
        return False

    dose_enregistre_norm = normaliser_texte(dose_enregistre)
    dose_attendue_norm = normaliser_texte(dose_attendue)

    ordinal_patterns = (
        (1, r"\b1\s*(?:er|ere|re|e)\b|\bpremiere\b"),
        (2, r"\b2\s*(?:eme|e|nde|nd)\b|\bdeuxieme\b|\bseconde\b"),
        (3, r"\b3\s*(?:eme|e)\b|\btroisieme\b"),
    )
    ordinal_enregistre = next(
        (
            ordinal
            for ordinal, pattern in ordinal_patterns
            if re.search(pattern, dose_enregistre_norm)
        ),
        None,
    )
    ordinal_attendu = next(
        (
            ordinal
            for ordinal, pattern in ordinal_patterns
            if re.search(pattern, dose_attendue_norm)
        ),
        None,
    )
    if ordinal_enregistre is not None and ordinal_attendu is not None:
        return ordinal_enregistre == ordinal_attendu

    if dose_enregistre_norm == dose_attendue_norm:
        return True
    return dose_attendue_norm in dose_enregistre_norm or dose_enregistre_norm in dose_attendue_norm


def _vaccination_deja_programmee(enregistrements, item):
    for vaccination in enregistrements:
        nom_enregistre = normaliser_texte(vaccination.nom_vaccin)
        nom_attendu = normaliser_texte(item["nom_vaccin"])
        correspondance_directe = (
            nom_enregistre == nom_attendu
            and _dose_correspond(vaccination.dose, item["dose"])
        )
        vaccin_combine_naissance = (
            "bcg" in nom_enregistre
            and any(
                terme in nom_enregistre
                for terme in (
                    "polio",
                    "polomyelite",
                    "pollomyelite",
                    "poliomyelite",
                    "vpo",
                )
            )
            and (
                (nom_attendu == "bcg" and item["dose"] == "Naissance")
                or (nom_attendu == "vpo" and item["dose"] == "Dose 0")
            )
        )
        if correspondance_directe or vaccin_combine_naissance:
            return True
    return False


def calculer_date_programmee(date_naissance, jours_apres_naissance):
    if not date_naissance:
        return None
    return date_naissance + timedelta(days=int(jours_apres_naissance))


def prochaine_vaccination_enfant(enfant):
    from .models import Vaccination

    if not enfant or not enfant.date_naissance:
        return None

    enregistrements = list(
        Vaccination.objects.filter(
            enfant=enfant,
            date_effectuee__isnull=False,
        )
    )

    for item in CAMEROON_VACCINE_SCHEDULE:
        if _vaccination_deja_programmee(enregistrements, item):
            continue

        date_prevue = calculer_date_programmee(
            enfant.date_naissance,
            item["jours_apres_naissance"],
        )
        if date_prevue is None:
            continue

        aujourd_hui = timezone.localdate()
        statut = "Effectuée" if any(
            normaliser_texte(v.nom_vaccin) == normaliser_texte(item["nom_vaccin"]) and _dose_correspond(v.dose, item["dose"])
            for v in enregistrements
        ) else ("En retard" if date_prevue < aujourd_hui else "À venir")

        return {
            "nom_vaccin": item["nom_vaccin"],
            "dose": item["dose"],
            "age_recommande": item["age_recommande"],
            "date_prevue": date_prevue,
            "jours_restants": (date_prevue - aujourd_hui).days,
            "statut": statut,
        }

    return None


def programmer_rappels_pour_vaccination(vaccination):
    from .models import VaccinationRappel

    if not vaccination:
        return []

    if (
        not vaccination.date_prevue
        or vaccination.date_effectuee
        or vaccination.date_prevue < timezone.localdate()
    ):
        VaccinationRappel.objects.filter(
            vaccination=vaccination,
            statut="planifie",
        ).update(
            statut="annule",
            date_tentative=timezone.now(),
            resultat="Annulé : vaccination effectuée ou date prévue dépassée.",
            updated_at=timezone.now(),
        )
        return []

    enfant = vaccination.enfant
    canaux = []
    if (enfant.parent.email or "").strip():
        canaux.append("email")
    if enfant.whatsapp_consent and enfant.telephone_parent:
        canaux.append("whatsapp")

    rappels_non_autorises = VaccinationRappel.objects.filter(
        vaccination=vaccination,
        statut="planifie",
    )
    if canaux:
        rappels_non_autorises = rappels_non_autorises.exclude(canal__in=canaux)
    rappels_non_autorises.update(
        statut="annule",
        date_tentative=timezone.now(),
        resultat="Annulé : canal de notification non configuré ou non autorisé.",
        updated_at=timezone.now(),
    )

    rappels = []
    for delai, decalage in (("J-3", -3), ("J-1", -1), ("J0", 0)):
        date_rappel = vaccination.date_prevue + timedelta(days=decalage)
        if date_rappel < timezone.localdate():
            VaccinationRappel.objects.filter(
                vaccination=vaccination,
                canal__in=canaux,
                delai=delai,
                statut="planifie",
            ).update(
                statut="annule",
                date_tentative=timezone.now(),
                resultat="Annulé : date de rappel dépassée après mise à jour.",
                updated_at=timezone.now(),
            )
            continue

        due_datetime = datetime.combine(
            date_rappel,
            datetime.min.time(),
            tzinfo=timezone.get_current_timezone(),
        )
        for canal in canaux:
            rappel, created = VaccinationRappel.objects.get_or_create(
                vaccination=vaccination,
                canal=canal,
                delai=delai,
                defaults={
                    "statut": "planifie",
                    "date_tentative": due_datetime,
                    "resultat": "Planifié",
                },
            )
            if not created and rappel.statut in ("planifie", "annule"):
                rappel.statut = "planifie"
                rappel.date_tentative = due_datetime
                rappel.resultat = f"Planifié pour le {date_rappel.isoformat()}"
                rappel.save(
                    update_fields=[
                        "statut",
                        "date_tentative",
                        "resultat",
                        "updated_at",
                    ]
                )

            rappels.append(
                {"objet": rappel, "created": created, "date_rappel": date_rappel}
            )

    return rappels

from django.core.management.base import BaseCommand
from django.utils import timezone

from sante.models import VaccinationRappel
from sante.reminders import (
    programmer_rappels_manquants,
    send_due_vaccination_reminders,
)


class Command(BaseCommand):
    help = "Envoie les rappels de vaccination planifiés à leur date." 

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche le nombre de rappels dus sans envoyer ni modifier de données.",
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            due_count = VaccinationRappel.objects.filter(
                statut="planifie",
                date_tentative__lte=timezone.now(),
            ).count()
            self.stdout.write(
                f"Mode test : {due_count} rappel(s) déjà planifié(s) sont dus; "
                "aucun message ne sera envoyé."
            )
            return

        started_at = timezone.now()
        scheduled = programmer_rappels_manquants()
        total = send_due_vaccination_reminders()
        failures = VaccinationRappel.objects.filter(
            statut="echec",
            updated_at__gte=started_at,
        ).count()
        self.stdout.write(
            f"{scheduled} rappel(s) programmé(s), {total} rappel(s) envoyé(s), "
            f"{failures} échec(s)."
        )
        if failures:
            self.stderr.write(
                self.style.ERROR(
                    "Consultez l'historique VaccinationRappel pour les erreurs "
                    "et la configuration manquante."
                )
            )

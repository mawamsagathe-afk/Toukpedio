from django.contrib import admin

from .models import (
    Enfant,
    Consultation,
    Vaccination,
    SuiviCroissance,
    BienEtre,
    RendezVous,
)


# =========================================================
# ENFANTS
# =========================================================

@admin.register(Enfant)
class EnfantAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "nom",
        "prenom",
        "date_naissance",
        "sexe",
        "parent",
        "telephone_parent",
        "date_creation",
    )

    list_display_links = (
        "id",
        "nom",
        "prenom",
    )

    search_fields = (
        "nom",
        "prenom",
        "parent__username",
        "parent__email",
        "telephone_parent",
    )

    list_filter = (
        "sexe",
        "date_naissance",
        "date_creation",
    )

    ordering = (
        "-date_creation",
    )

    autocomplete_fields = (
        "parent",
    )


# =========================================================
# CONSULTATIONS
# =========================================================

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "enfant",
        "date_consultation",
        "motif",
        "temperature",
        "poids",
        "taille",
        "diagnostic",
        "prochaine_visite",
    )

    list_display_links = (
        "id",
        "enfant",
    )

    search_fields = (
        "enfant__nom",
        "enfant__prenom",
        "motif",
        "diagnostic",
        "traitement",
    )

    list_filter = (
        "date_consultation",
        "prochaine_visite",
    )

    ordering = (
        "-date_consultation",
    )

    autocomplete_fields = (
        "enfant",
    )


# =========================================================
# VACCINATIONS
# =========================================================

@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "enfant",
        "nom_vaccin",
        "dose",
        "date_prevue",
        "date_effectuee",
        "prochaine_dose",
    )

    list_display_links = (
        "id",
        "enfant",
        "nom_vaccin",
    )

    search_fields = (
        "enfant__nom",
        "enfant__prenom",
        "nom_vaccin",
    )

    list_filter = (
        "nom_vaccin",
        "date_prevue",
        "date_effectuee",
        "prochaine_dose",
    )

    ordering = (
        "date_prevue",
    )

    autocomplete_fields = (
        "enfant",
    )


# =========================================================
# SUIVI DE CROISSANCE
# =========================================================

@admin.register(SuiviCroissance)
class SuiviCroissanceAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "enfant",
        "date_mesure",
        "poids",
        "taille",
        "perimetre_cranien",
    )

    list_display_links = (
        "id",
        "enfant",
    )

    search_fields = (
        "enfant__nom",
        "enfant__prenom",
    )

    list_filter = (
        "date_mesure",
    )

    ordering = (
        "-date_mesure",
    )

    autocomplete_fields = (
        "enfant",
    )


# =========================================================
# BIEN-ÊTRE
# =========================================================

@admin.register(BienEtre)
class BienEtreAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "enfant",
        "date_suivi",
        "humeur",
        "sommeil",
        "temps_ecran",
    )

    list_display_links = (
        "id",
        "enfant",
    )

    search_fields = (
        "enfant__nom",
        "enfant__prenom",
        "alimentation",
        "observations",
    )

    list_filter = (
        "humeur",
        "sommeil",
        "date_suivi",
    )

    ordering = (
        "-date_suivi",
    )

    autocomplete_fields = (
        "enfant",
    )


# =========================================================
# RENDEZ-VOUS
# =========================================================

@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "enfant",
        "date_rendez_vous",
        "heure",
        "motif",
        "professionnel",
        "statut",
    )

    list_display_links = (
        "id",
        "enfant",
    )

    search_fields = (
        "enfant__nom",
        "enfant__prenom",
        "motif",
        "professionnel__username",
        "professionnel__email",
    )

    list_filter = (
        "statut",
        "date_rendez_vous",
        "professionnel",
    )

    ordering = (
        "date_rendez_vous",
        "heure",
    )

    autocomplete_fields = (
        "enfant",
        "professionnel",
    )
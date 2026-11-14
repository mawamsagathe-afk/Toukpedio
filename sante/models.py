import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.utils import timezone


def mode_garde_expiration_par_defaut():
    duree_jours = getattr(settings, "MODE_GARDE_TOKEN_VALIDITY_DAYS", 7)
    return timezone.now() + timedelta(days=duree_jours)


class Enfant(models.Model):

    SEXE_CHOICES = [
        ("M", "Masculin"),
        ("F", "Féminin"),
    ]

    # ==========================
    # IDENTITÉ DE L'ENFANT
    # ==========================

    nom = models.CharField(max_length=100)

    prenom = models.CharField(max_length=100)

    date_naissance = models.DateField()

    sexe = models.CharField(
        max_length=1,
        choices=SEXE_CHOICES
    )

    photo = models.ImageField(
        upload_to="enfants/",
        blank=True,
        null=True
    )

    # ==========================
    # INFORMATIONS DU PARENT
    # ==========================

    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="enfants"
    )

    telephone_parent = models.CharField(
        max_length=30,
        blank=True
    )

    whatsapp_consent = models.BooleanField(
        default=False,
        verbose_name="Consentement aux rappels WhatsApp"
    )

    adresse = models.TextField(
        blank=True
    )

    # ==========================
    # INFORMATIONS DE SANTÉ
    # ==========================

    groupe_sanguin = models.CharField(
        max_length=5,
        blank=True
    )

    allergies = models.TextField(
        blank=True
    )
    traitement = models.TextField(
    blank=True,
    null=True
    )

    antecedents = models.TextField(
        blank=True
    )

    observations = models.TextField(
        blank=True
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.nom} {self.prenom}"

    class Meta:
        ordering = ["nom", "prenom"]
        verbose_name = "Enfant"
        verbose_name_plural = "Enfants"
        
class JournalSymptome(models.Model):

    INTENSITE_CHOICES = [
        ("faible", "Faible"),
        ("moderee", "Modérée"),
        ("forte", "Forte"),
        ("tres_forte", "Très forte"),
    ]

    EVOLUTION_CHOICES = [
        ("ameliore", "Amélioration"),
        ("stable", "Stable"),
        ("aggrave", "Aggravation"),
    ]

    enfant = models.ForeignKey(
        Enfant,
        on_delete=models.CASCADE,
        related_name="journaux_symptomes"
    )

    date = models.DateField(default=timezone.localdate)

    symptome = models.CharField(
        max_length=200
    )

    intensite = models.CharField(
        max_length=20,
        choices=INTENSITE_CHOICES
    )

    description = models.TextField(
        blank=True
    )

    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True
    )

    traitement_pris = models.TextField(
        blank=True
    )

    evolution = models.CharField(
        max_length=20,
        choices=EVOLUTION_CHOICES,
        blank=True
    )

    observations = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.enfant.prenom} - {self.symptome} - {self.date}" 
           
class Parent(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profil_parent"
    )

    telephone = models.CharField(
        max_length=30,
        blank=True
    )

    adresse = models.TextField(
        blank=True
    )

    def __str__(self):
        return self.user.username 


class ProfessionnelSante(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profil_sante",
    )
    profession = models.CharField(max_length=100)
    specialite = models.CharField(max_length=120, blank=True)
    numero_ordre = models.CharField(max_length=80, blank=True)

    class Meta:
        verbose_name = "Professionnel de santé"
        verbose_name_plural = "Professionnels de santé"
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return self.user.get_full_name() or self.user.username


# =========================================================
# CONSULTATION
# =========================================================

class Consultation(models.Model):

    enfant = models.ForeignKey(
        Enfant,
        on_delete=models.CASCADE,
        related_name="consultations"
    )

    date_consultation = models.DateTimeField(
        auto_now_add=True
    )

    motif = models.TextField()

    symptomes = models.TextField(
        blank=True
    )

    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True
    )

    poids = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    taille = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    diagnostic = models.TextField(
        blank=True
    )

    traitement = models.TextField(
        blank=True
    )

    recommandations = models.TextField(
        blank=True
    )

    prochaine_visite = models.DateField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Consultation - {self.enfant}"

    class Meta:
        ordering = ["-date_consultation"]
        verbose_name = "Consultation"
        verbose_name_plural = "Consultations"


# =========================================================
# VACCINATION
# =========================================================

class Vaccination(models.Model):

    enfant = models.ForeignKey(
        Enfant,
        on_delete=models.CASCADE,
        related_name="vaccinations"
    )

    # Âge recommandé au moment de la vaccination
    age = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Âge"
    )

    # Nom du vaccin
    nom_vaccin = models.CharField(
        max_length=150,
        verbose_name="Nom du vaccin"
    )

    # Dose : 1ère dose, 2ème dose, rappel...
    dose = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Dose"
    )

    # Date prévue selon le calendrier
    date_prevue = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date prévue"
    )

    # Date réelle à laquelle le vaccin a été administré
    date_effectuee = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date effectuée"
    )

    # Prochaine date de vaccination / rendez-vous
    prochaine_dose = models.DateField(
        null=True,
        blank=True,
        verbose_name="Prochain rendez-vous"
    )

    # Informations supplémentaires
    observations = models.TextField(
        blank=True,
        verbose_name="Observations"
    )

    def __str__(self):
        return f"{self.nom_vaccin} - {self.enfant.prenom}"

    @property
    def est_effectuee(self):
        return bool(self.date_effectuee)

    @property
    def statut(self):
        if self.date_effectuee:
            return "Effectuée"
        if self.date_prevue and self.date_prevue < timezone.localdate():
            return "En retard"
        return "À venir"

    @property
    def jours_restants(self):
        if not self.date_prevue:
            return None
        return (self.date_prevue - timezone.localdate()).days

    class Meta:
        ordering = [
            "date_prevue",
            "date_effectuee",
        ]

        verbose_name = "Vaccination"

        verbose_name_plural = "Vaccinations"


class VaccinationProgramme(models.Model):
    """Calendrier vaccinal de référence et échéances prévisionnelles."""

    vaccin = models.CharField(max_length=150)
    dose = models.CharField(max_length=50, blank=True)
    age_recommande = models.CharField(max_length=100)
    intervalle_jours = models.IntegerField(null=True, blank=True)
    ordre = models.IntegerField(default=0)
    source = models.CharField(max_length=255, blank=True, default="")
    source_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["ordre", "dose", "vaccin"]
        verbose_name = "Programme vaccinal"
        verbose_name_plural = "Programmes vaccinaux"

    def __str__(self):
        return f"{self.vaccin} - {self.dose or 'Dose'}"


class VaccinationRappel(models.Model):
    """Historique des rappels envoyés ou planifiés."""

    CANAL_CHOICES = [
        ("email", "Email"),
        ("whatsapp", "WhatsApp"),
    ]

    STATUT_CHOICES = [
        ("planifie", "Planifié"),
        ("envoye", "Envoyé"),
        ("echec", "Échec"),
        ("annule", "Annulé"),
    ]

    vaccination = models.ForeignKey(
        Vaccination,
        on_delete=models.CASCADE,
        related_name="rappels"
    )
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES)
    delai = models.CharField(max_length=20)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="planifie")
    date_tentative = models.DateTimeField(null=True, blank=True)
    nombre_tentatives = models.IntegerField(default=0)
    resultat = models.TextField(blank=True)
    fournisseur_message_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Rappel vaccination"
        verbose_name_plural = "Rappels vaccination"
        constraints = [
            models.UniqueConstraint(
                fields=["vaccination", "canal", "delai"],
                name="unique_rappel_vaccin_canal_delai",
            )
        ]

    def __str__(self):
        return f"{self.vaccination} - {self.canal} - {self.delai}"


# =========================================================
# SUIVI DE CROISSANCE
# =========================================================

class SuiviCroissance(models.Model):

    enfant = models.ForeignKey(
        Enfant,
        on_delete=models.CASCADE,
        related_name="croissances"
    )

    date_mesure = models.DateField()

    poids = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    taille = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    perimetre_cranien = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    observations = models.TextField(
        blank=True
    )

    def __str__(self):
        return f"Croissance - {self.enfant} - {self.date_mesure}"

    class Meta:
        ordering = ["-date_mesure"]
        verbose_name = "Suivi de croissance"
        verbose_name_plural = "Suivis de croissance"


# =========================================================
# BIEN-ÊTRE
# =========================================================

class BienEtre(models.Model):

    HUMEUR_CHOICES = [
        ("tres_bonne", "Très bonne"),
        ("bonne", "Bonne"),
        ("moyenne", "Moyenne"),
        ("mauvaise", "Mauvaise"),
    ]

    SOMMEIL_CHOICES = [
        ("tres_bon", "Très bon"),
        ("bon", "Bon"),
        ("moyen", "Moyen"),
        ("mauvais", "Mauvais"),
    ]

    enfant = models.ForeignKey(
        Enfant,
        on_delete=models.CASCADE,
        related_name="bien_etre"
    )

    date_suivi = models.DateField()

    humeur = models.CharField(
        max_length=20,
        choices=HUMEUR_CHOICES
    )

    sommeil = models.CharField(
        max_length=20,
        choices=SOMMEIL_CHOICES
    )

    alimentation = models.TextField(
        blank=True
    )

    hydratation = models.TextField(
        blank=True
    )

    activite_physique = models.TextField(
        blank=True
    )

    hygiene = models.TextField(
        blank=True
    )

    temps_ecran = models.PositiveIntegerField(
        default=0,
        help_text="Temps d'écran en minutes par jour"
    )

    observations = models.TextField(
        blank=True
    )

    def __str__(self):
        return f"Bien-être - {self.enfant} - {self.date_suivi}"

    class Meta:
        ordering = ["-date_suivi"]
        verbose_name = "Suivi du bien-être"
        verbose_name_plural = "Suivis du bien-être"


# =========================================================
# RENDEZ-VOUS
# =========================================================

class RendezVous(models.Model):

    STATUT_CHOICES = [
        ("planifie", "Planifié"),
        ("confirme", "Confirmé"),
        ("termine", "Terminé"),
        ("annule", "Annulé"),
    ]

    enfant = models.ForeignKey(
        Enfant,
        on_delete=models.CASCADE,
        related_name="rendez_vous"
    )

    date_rendez_vous = models.DateField()

    heure = models.TimeField()

    motif = models.TextField()

    professionnel = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rendez_vous_professionnels"
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="planifie"
    )

    notes = models.TextField(
        blank=True
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"Rendez-vous - {self.enfant} - "
            f"{self.date_rendez_vous}"
        )

    class Meta:
        ordering = ["date_rendez_vous", "heure"]
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"
        
from django.db import models


class Temperature(models.Model):

    enfant = models.ForeignKey(
        "Enfant",
        on_delete=models.CASCADE,
        related_name="temperatures"
    )

    valeur = models.DecimalField(
        max_digits=4,
        decimal_places=1
    )

    date_prise = models.DateTimeField(
        auto_now_add=True
    )

    observation = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-date_prise"]
        verbose_name = "Température"
        verbose_name_plural = "Températures"

    def categorie(self):

        if self.valeur < 38:
            return "normal"

        elif self.valeur < 39:
            return "surveillance"

        return "elevee"

    def message_alerte(self):

        if self.valeur < 38:
            return ""

        if self.valeur < 39:
            return "Surveillez l'évolution de la température."

        return "Contactez un professionnel de santé pour avis."

    def couleur(self):

        categories = {
            "normal": "#198754",
            "surveillance": "#ffc107",
            "elevee": "#dc3545",
        }

        return categories[self.categorie()]

    def __str__(self):

        return (
            f"{self.enfant.prenom} - "
            f"{self.valeur} °C - "
            f"{self.date_prise:%d/%m/%Y %H:%M}"
        )
        
class PhotoSymptome(models.Model):

    journal = models.ForeignKey(
        "JournalSymptome",
        on_delete=models.CASCADE,
        related_name="photos"
    )

    photo = models.FileField(
        upload_to="symptomes/"
    )

    date_ajout = models.DateTimeField(
        auto_now_add=True
    )

    description = models.CharField(
        max_length=255,
        blank=True
    )

    def __str__(self):
        return f"Photo - {self.journal.symptome}"
    
    # =========================================================
# GESTION DES TRAITEMENTS
# =========================================================

class Traitement(models.Model):

    FREQUENCE_CHOICES = [
        ("unique", "Une seule fois"),
        ("quotidienne", "Une fois par jour"),
        ("2_jours", "Deux fois par jour"),
        ("3_jours", "Trois fois par jour"),
        ("4_jours", "Quatre fois par jour"),
        ("6_heures", "Toutes les 6 heures"),
        ("8_heures", "Toutes les 8 heures"),
        ("12_heures", "Toutes les 12 heures"),
        ("personnalisee", "Personnalisée"),
    ]

    enfant = models.ForeignKey(
        Enfant,
        on_delete=models.CASCADE,
        related_name="traitements"
    )

    prescrit_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescriptions_sante",
    )

    medicament = models.CharField(
        max_length=150
    )

    dose = models.CharField(
        max_length=100,
        help_text="Exemple : 1 pipette de 5 ml"
    )

    frequence = models.CharField(
        max_length=30,
        choices=FREQUENCE_CHOICES
    )

    intervalle_heures = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Délai minimal entre deux prises, en heures"
    )

    premiere_prise = models.DateTimeField()

    date_fin = models.DateField(
        null=True,
        blank=True
    )

    actif = models.BooleanField(
        default=True
    )

    notes = models.TextField(
        blank=True
    )

    prochaine_prise = models.DateTimeField(
        null=True,
        blank=True
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.medicament} - {self.enfant.prenom}"

    class Meta:
        ordering = ["prochaine_prise", "-date_creation"]
        verbose_name = "Traitement"
        verbose_name_plural = "Traitements"


# =========================================================
# PRISES DE TRAITEMENT
# =========================================================

class PriseTraitement(models.Model):

    STATUT_CHOICES = [
        ("prise", "Prise effectuée"),
        ("annulee", "Annulée"),
        ("en_attente", "En attente"),
    ]

    traitement = models.ForeignKey(
        Traitement,
        on_delete=models.CASCADE,
        related_name="prises"
    )

    date_heure_prevue = models.DateTimeField()

    date_heure_prise = models.DateTimeField(
        null=True,
        blank=True
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="en_attente"
    )

    observation = models.TextField(
        blank=True
    )

    def __str__(self):
        return (
            f"{self.traitement.medicament} - "
            f"{self.date_heure_prevue:%d/%m/%Y %H:%M}"
        )

    class Meta:
        ordering = ["-date_heure_prevue"]
        verbose_name = "Prise de traitement"
        verbose_name_plural = "Prises de traitement"
        
class PartageEnfant(models.Model):
    enfant = models.ForeignKey(
        Enfant,
        on_delete=models.CASCADE,
        related_name="partages"
    )

    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="enfants_partages"
    )

    date_invitation = models.DateTimeField(auto_now_add=True)

    accepte = models.BooleanField(default=False)
    refusee = models.BooleanField(default=False)

    class Meta:
        unique_together = ("enfant", "parent")

    def __str__(self):
        statut = "Acceptée" if self.accepte else "En attente"
        return f"{self.parent.username} → {self.enfant.prenom} ({statut})"
    
import uuid

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Enfant


class ModeGarde(models.Model):

    TYPE_GARDIEN_CHOICES = [
        ("baby_sitter", "Baby-sitter"),
        ("grand_parent", "Grand-parent"),
        ("autre", "Autre"),
    ]

    # =====================================================
    # ENFANT ET PARENT
    # =====================================================

    enfant = models.ForeignKey(
        Enfant,
        on_delete=models.CASCADE,
        related_name="modes_garde"
    )

    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="modes_garde_crees"
    )

    # =====================================================
    # PERSONNE QUI GARDE L'ENFANT
    # =====================================================

    nom_gardien = models.CharField(
        max_length=150
    )

    telephone_gardien = models.CharField(
        max_length=30,
        blank=True,
    )

    email_gardien = models.EmailField(
        max_length=254,
        blank=True,
    )

    type_gardien = models.CharField(
        max_length=30,
        choices=TYPE_GARDIEN_CHOICES
    )

    # =====================================================
    # DURÉE DE LA GARDE
    # =====================================================

    date_debut = models.DateField()

    date_fin = models.DateField()

    heure_debut = models.TimeField(
        blank=True,
        null=True,
    )

    heure_fin = models.TimeField(
        blank=True,
        null=True,
    )

    # =====================================================
    # INFORMATIONS À PARTAGER
    # =====================================================

    partager_allergies = models.BooleanField(
        default=True
    )

    partager_traitement = models.BooleanField(
        default=True
    )

    partager_alimentation = models.BooleanField(
        default=True
    )

    partager_sommeil = models.BooleanField(
        default=True
    )

    partager_hydratation = models.BooleanField(
        default=False
    )

    partager_antecedents = models.BooleanField(
        default=False
    )

    partager_vaccinations = models.BooleanField(
        default=False
    )

    partager_consultations = models.BooleanField(
        default=False
    )

    partager_temperature = models.BooleanField(
        default=False
    )

    partager_contact_parent = models.BooleanField(
        default=True
    )

    # =====================================================
    # CONSIGNES
    # =====================================================
    consignes = models.TextField(
    blank=True,
    null=True
    )
    contact_urgence = models.CharField(
    max_length=30,
    blank=True,
    null=True
    )

    # =====================================================
    # SÉCURITÉ
    # =====================================================

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    token_expires_at = models.DateTimeField(
        default=mode_garde_expiration_par_defaut,
        editable=False,
    )

    token_revoked_at = models.DateTimeField(
        blank=True,
        null=True,
        editable=False,
    )

    actif = models.BooleanField(
        default=True
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    # =====================================================
    # AFFICHAGE
    # =====================================================

    def __str__(self):

        return (
            f"Mode garde - "
            f"{self.enfant.prenom} - "
            f"{self.nom_gardien}"
        )

    # =====================================================
    # VÉRIFIER SI LA FICHE EST ENCORE VALIDE
    # =====================================================

    @property
    def est_valide(self):

        aujourd_hui = timezone.localdate()

        return (
            self.actif
            and self.token_revoked_at is None
            and self.token_expires_at > timezone.now()
            and self.date_debut <= aujourd_hui <= self.date_fin
        )


class Conversation(models.Model):
    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="conversations_sante_parent",
    )
    professionnel = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="conversations_sante_professionnel",
    )
    enfant = models.ForeignKey(
        Enfant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations_sante",
    )
    sujet = models.CharField(max_length=160)
    ouverte = models.BooleanField(default=True)
    creee_le = models.DateTimeField(auto_now_add=True)
    mise_a_jour = models.DateTimeField(auto_now=True)
    dernier_message_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-dernier_message_le", "-creee_le"]
        verbose_name = "Conversation de santé"
        verbose_name_plural = "Conversations de santé"

    def __str__(self):
        return f"{self.sujet} ({self.parent} - {self.professionnel})"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    expediteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="messages_sante_envoyes",
    )
    texte = models.CharField(max_length=4000)
    envoye_le = models.DateTimeField(auto_now_add=True)
    lu_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["envoye_le", "pk"]
        verbose_name = "Message de santé"
        verbose_name_plural = "Messages de santé"

    def __str__(self):
        return f"Message de {self.expediteur} dans {self.conversation_id}"
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import re
from .models import Consultation, Vaccination
from .models import (JournalSymptome,PhotoSymptome,Traitement,PriseTraitement,)
from .models import (
    Enfant,
    SuiviCroissance,
    BienEtre,
    RendezVous,
    PartageEnfant,
    ProfessionnelSante,
)


class ProfessionnelSanteForm(UserCreationForm):
    first_name = forms.CharField(
        label="Prénom",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label="Nom",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    profession = forms.CharField(
        label="Profession",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Médecin, infirmier…",
            }
        ),
    )
    specialite = forms.CharField(
        label="Spécialité",
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    numero_ordre = forms.CharField(
        label="Numéro d’ordre (facultatif)",
        max_length=80,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
        )
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {"username": "Nom d’utilisateur"}

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Cette adresse e-mail est déjà associée à un compte."
            )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.email = self.cleaned_data["email"].strip()
        user.is_active = True
        user.is_staff = False
        if commit:
            user.save()
            ProfessionnelSante.objects.create(
                user=user,
                profession=self.cleaned_data["profession"].strip(),
                specialite=self.cleaned_data["specialite"].strip(),
                numero_ordre=self.cleaned_data["numero_ordre"].strip(),
            )
        return user


class RendezVousParentForm(forms.ModelForm):

    class Meta:
        model = RendezVous
        fields = [
            "date_rendez_vous",
            "heure",
            "professionnel",
            "motif",
            "notes",
        ]

        widgets = {
            "date_rendez_vous": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "heure": forms.TimeInput(
                attrs={"type": "time", "class": "form-control"}
            ),
            "professionnel": forms.Select(
                attrs={"class": "form-select"}
            ),
            "motif": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["professionnel"].required = False
        self.fields["professionnel"].queryset = (
            self.fields["professionnel"].queryset
            .filter(is_staff=True, is_active=True)
            .order_by("first_name", "last_name")
        )


class ConsultationForm(forms.ModelForm):

    class Meta:
        model = Consultation

        fields = [
            "motif",
            "symptomes",
            "temperature",
            "poids",
            "taille",
            "diagnostic",
            "traitement",
            "recommandations",
            "prochaine_visite",
        ]

        widgets = {
            "motif": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Motif de la consultation"
                }
            ),

            "symptomes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "temperature": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.1"
                }
            ),

            "poids": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01"
                }
            ),

            "taille": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01"
                }
            ),

            "diagnostic": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "traitement": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "recommandations": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "prochaine_visite": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date"
                }
            ),
        }
        
from .models import Temperature


class TemperatureForm(forms.ModelForm):

    class Meta:
        model = Temperature

        fields = [
            "valeur",
            "observation",
        ]

        widgets = {
            "valeur": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "placeholder": "Exemple : 38.2",
                    "step": "0.1",
                    "min": "30",
                    "max": "45",
                }
            ),

            "observation": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Observation facultative...",
                    "rows": 3,
                }
            ),
        }

        labels = {
            "valeur": "Température (°C)",
            "observation": "Observation",
        }
        


class JournalSymptomeForm(forms.ModelForm):

    class Meta:
        model = JournalSymptome

        fields = [
            "date",
            "temperature",
            "symptome",
            "intensite",
            "description",
            "traitement_pris",
            "evolution",
            "observations",
        ]

        widgets = {
            "date": forms.HiddenInput(),

            "temperature": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.1",
                    "placeholder": "Ex : 38.5"
                }
            ),

            "symptome": forms.HiddenInput(),

            "intensite": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Décrivez ce que vous observez..."
                }
            ),

            "observations": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Autres observations..."
                }
            ),
        }

        labels = {
            "date": "Date",
            "temperature": "Température",
            "symptome": "Symptôme",
            "intensite": "Intensité",
            "description": "Description",
            "observations": "Observations",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["date"].required = False
        self.fields["symptome"].required = True

class PhotoSymptomeForm(forms.ModelForm):
    class Meta:
        model = PhotoSymptome

        fields = [
            "photo",
            "description",
        ]

        widgets = {

            "photo": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                    "capture": "environment",
                }
            ),

            "description": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Description de la photo",
                }
            ),
        }
        # =========================================================
# FORMULAIRE TRAITEMENT
# =========================================================

class TraitementForm(forms.ModelForm):

    class Meta:

        model = Traitement

        fields = [
            "medicament",
            "dose",
            "frequence",
            "intervalle_heures",
            "premiere_prise",
            "date_fin",
            "notes",
        ]

        widgets = {

            "medicament": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nom du médicament",
                }
            ),

            "dose": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Exemple : 1 pipette de 5 ml",
                }
            ),

            "frequence": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "intervalle_heures": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                    "placeholder": "Exemple : 6",
                }
            ),

            "premiere_prise": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),

            "date_fin": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Consignes ou observations...",
                }
            ),
        }


# =========================================================
# FORMULAIRE PRISE DE TRAITEMENT
# =========================================================

class PriseTraitementForm(forms.ModelForm):

    class Meta:

        model = PriseTraitement

        fields = [
            "observation",
        ]

        widgets = {

            "observation": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Observation après la prise...",
                }
            ),
        }
        

from .models import ModeGarde

class ModeGardeForm(forms.ModelForm):

    email_gardien = forms.EmailField(
        max_length=254,
        label="Adresse e-mail de la personne qui garde l'enfant",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "gardien@example.com",
                "autocomplete": "email",
            }
        ),
    )

    class Meta:

        model = ModeGarde

        fields = [
            "nom_gardien",
            "telephone_gardien",
            "email_gardien",
            "type_gardien",
            "date_debut",
            "date_fin",
            "heure_debut",
            "heure_fin",

            "partager_allergies",
            "partager_traitement",
            "partager_alimentation",
            "partager_sommeil",
            "partager_hydratation",
            "partager_antecedents",
            "partager_vaccinations",
            "partager_consultations",
            "partager_temperature",
            "partager_contact_parent",

            "consignes",
            "contact_urgence",
        ]

        widgets = {

            "nom_gardien": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex : Marie Dupont"
                }
            ),

            "telephone_gardien": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+237 6XX XXX XXX",
                    "type": "tel",
                    "inputmode": "tel",
                }
            ),

            "heure_debut": forms.TimeInput(
                attrs={"type": "time", "class": "form-control"}
            ),

            "heure_fin": forms.TimeInput(
                attrs={"type": "time", "class": "form-control"}
            ),

            "type_gardien": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "date_debut": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control"
                }
            ),

            "date_fin": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control"
                }
            ),

            "consignes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Ex : Donner le repas à 12h, "
                        "sieste à 14h..."
                    )
                }
            ),

            "contact_urgence": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+237 6XX XXX XXX"
                }
            ),
        }

        labels = {
            "nom_gardien": "Nom complet",
            "telephone_gardien": "Téléphone (facultatif)",
            "date_debut": "Date de début",
            "date_fin": "Date de fin",
            "heure_debut": "Heure de début (facultative)",
            "heure_fin": "Heure de fin (facultative)",
        }

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get("date_debut")
        date_fin = cleaned_data.get("date_fin")
        if date_debut and date_fin and date_fin < date_debut:
            self.add_error(
                "date_fin",
                "La date de fin doit être postérieure ou égale à la date de début.",
            )
        heure_debut = cleaned_data.get("heure_debut")
        heure_fin = cleaned_data.get("heure_fin")
        if (
            date_debut
            and date_fin == date_debut
            and heure_debut
            and heure_fin
            and heure_fin < heure_debut
        ):
            self.add_error(
                "heure_fin",
                "L'heure de fin doit être postérieure ou égale à l'heure de début.",
            )
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["email_gardien"].required = False
from django import forms

from .models import Vaccination


class VaccinationForm(forms.ModelForm):

    class Meta:

        model = Vaccination

        fields = [
            "age",
            "nom_vaccin",
            "dose",
            "date_prevue",
            "date_effectuee",
            "prochaine_dose",
            "observations",
        ]

        widgets = {

            "age": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex : Naissance, 6 semaines, 9 mois..."
                }
            ),

            "nom_vaccin": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex : BCG"
                }
            ),

            "dose": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex : 1ère dose"
                }
            ),

            "date_prevue": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date"
                }
            ),

            "date_effectuee": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date"
                }
            ),

            "prochaine_dose": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date"
                }
            ),

            "observations": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Ajouter une observation concernant "
                        "la vaccination..."
                    )
                }
            ),
        }

        labels = {

            "age": "Âge de l'enfant",

            "nom_vaccin": "Nom du vaccin",

            "dose": "Dose",

            "date_prevue": "Date prévue",

            "date_effectuee": "Date du vaccin",

            "prochaine_dose": "Prochain rendez-vous",

            "observations": "Observations",
        }
    
class EnfantForm(forms.ModelForm):
    email_parent = forms.EmailField(
        required=False,
        max_length=254,
        label="Adresse e-mail du parent",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "exemple@domaine.com",
                "autocomplete": "email",
            }
        ),
    )

    class Meta:
        model = Enfant

        fields = [
            "nom",
            "prenom",
            "date_naissance",
            "sexe",
            "photo",
            "telephone_parent",
            "whatsapp_consent",
            "adresse",
            "groupe_sanguin",
            "allergies",
            "traitement",
            "antecedents",
            "observations",
        ]

        widgets = {
            "nom": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "prenom": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "date_naissance": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date"
                }
            ),

            "sexe": forms.Select(
                attrs={"class": "form-select"}
            ),

            "photo": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*"
                }
            ),

            "telephone_parent": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+237 6XX XXX XXX",
                    "inputmode": "tel",
                    "autocomplete": "tel",
                }
            ),

            "whatsapp_consent": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),

            "adresse": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2
                }
            ),

            "groupe_sanguin": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "allergies": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "traitement": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "antecedents": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "observations": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),
        }

        labels = {
            "telephone_parent": "Numéro WhatsApp du parent",
            "whatsapp_consent": "J'accepte de recevoir les rappels de vaccination par WhatsApp",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        parent_id = getattr(self.instance, "parent_id", None)
        if parent_id:
            self.fields["email_parent"].initial = self.instance.parent.email

    def clean_telephone_parent(self):
        telephone = self.cleaned_data.get("telephone_parent", "").strip()
        if not telephone:
            return ""

        if not re.fullmatch(r"\+?[0-9][0-9\s().-]*", telephone):
            raise forms.ValidationError(
                "Saisissez un numéro valide avec indicatif international, par exemple +237 6XX XXX XXX."
            )

        nombre_chiffres = sum(caractere.isdigit() for caractere in telephone)
        if not 8 <= nombre_chiffres <= 15:
            raise forms.ValidationError(
                "Le numéro doit contenir entre 8 et 15 chiffres."
            )
        return telephone

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get("whatsapp_consent")
            and not cleaned_data.get("telephone_parent")
        ):
            self.add_error(
                "telephone_parent",
                "Saisissez un numéro WhatsApp pour activer les rappels WhatsApp.",
            )
        return cleaned_data
class SuiviCroissanceForm(forms.ModelForm):

    class Meta:
        model = SuiviCroissance

        fields = [
            "date_mesure",
            "poids",
            "taille",
            "perimetre_cranien",
            "observations",
        ]

        widgets = {
            "date_mesure": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date"
                }
            ),

            "poids": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "Ex : 12.50"
                }
            ),

            "taille": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "Ex : 85.50"
                }
            ),

            "perimetre_cranien": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01"
                }
            ),

            "observations": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),
        }
        
class BienEtreForm(forms.ModelForm):

    class Meta:
        model = BienEtre

        fields = [
            "date_suivi",
            "humeur",
            "sommeil",
            "alimentation",
            "hydratation",
            "activite_physique",
            "hygiene",
            "temps_ecran",
            "observations",
        ]

        widgets = {
            "date_suivi": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date"
                }
            ),

            "humeur": forms.Select(
                attrs={"class": "form-select"}
            ),

            "sommeil": forms.Select(
                attrs={"class": "form-select"}
            ),

            "alimentation": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "hydratation": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "activite_physique": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "hygiene": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "temps_ecran": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0"
                }
            ),

            "observations": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),
        }
        
class RendezVousForm(forms.ModelForm):

    class Meta:
        model = RendezVous

        fields = [
            "date_rendez_vous",
            "heure",
            "motif",
            "professionnel",
            "statut",
            "notes",
        ]

        widgets = {
            "date_rendez_vous": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date"
                }
            ),

            "heure": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time"
                }
            ),

            "motif": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "professionnel": forms.Select(
                attrs={"class": "form-select"}
            ),

            "statut": forms.Select(
                attrs={"class": "form-select"}
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),
        }
from django import forms
from .models import Consultation, Vaccination
from .models import (JournalSymptome,PhotoSymptome,Traitement,PriseTraitement,)
from .models import (Enfant,SuiviCroissance,BienEtre,RendezVous,PartageEnfant,)


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

    class Meta:

        model = ModeGarde

        fields = [
            "nom_gardien",
            "telephone_gardien",
            "type_gardien",
            "date_debut",
            "date_fin",

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
                    "placeholder": "+237 6XX XXX XXX"
                }
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
class VaccinationForm(forms.ModelForm):

  class Meta:

    model = Vaccination

    fields = [
        "nom_vaccin",
        "dose",
        "date_prevue",
        "date_effectuee",
        "prochaine_dose",
        "observations",
    ]

    widgets = {

        "nom_vaccin": forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ex : BCG, Polio, Rougeole..."
            }
        ),

        "dose": forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ex : 1ère dose, 2ème dose..."
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
                "placeholder": "Ajoutez une observation concernant cette vaccination..."
            }
        ),
    }

    labels = {

        "nom_vaccin": "Nom du vaccin",

        "dose": "Dose",

        "date_prevue": "Date prévue",

        "date_effectuee": "Date effectuée",

        "prochaine_dose": "Prochaine dose",

        "observations": "Observations",
    }
    
class EnfantForm(forms.ModelForm):

    class Meta:
        model = Enfant

        fields = [
            "nom",
            "prenom",
            "date_naissance",
            "sexe",
            "photo",
            "telephone_parent",
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
                attrs={"class": "form-control"}
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
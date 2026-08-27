from django import forms
from .models import Consultation
from .models import (
    JournalSymptome,
    PhotoSymptome,
    Traitement,
    PriseTraitement,
)



class ConsultationForm(forms.ModelForm):

    class Meta:
        model = Consultation

        fields = [
            "motif",
            "symptomes",
            "diagnostic",
            "traitement",
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
                    "rows": 4,
                    "placeholder": "Décrire les symptômes..."
                }
            ),

            "diagnostic": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Diagnostic..."
                }
            ),

            "traitement": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Traitement prescrit..."
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
            "symptome",
            "intensite",
            "temperature",
            "description",
            "traitement_pris",
            "evolution",
            "observations",
        ]

        widgets = {

            "symptome": forms.HiddenInput(),

            "intensite": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "temperature": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Exemple : 38.2",
                    "step": "0.1"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Décrivez ce que vous observez..."
                }
            ),

            "traitement_pris": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Traitement éventuellement pris..."
                }
            ),

            "evolution": forms.Select(
                attrs={
                    "class": "form-select"
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
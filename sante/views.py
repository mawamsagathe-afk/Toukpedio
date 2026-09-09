# =========================================================
# TOUKPEDIO - views.py
# =========================================================

from io import BytesIO
import os
from urllib.parse import quote
from datetime import timedelta

from django.db import models
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse
from google import genai
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image, ImageDraw, ImageFont
from .models import ( Enfant,Consultation,JournalSymptome,Parent,PartageEnfant,PriseTraitement,
    Temperature,Traitement,Vaccination,SuiviCroissance,BienEtre,RendezVous,ModeGarde,PhotoSymptome,)
from .forms import (JournalSymptomeForm,PhotoSymptomeForm,TraitementForm,PriseTraitementForm,
    ConsultationForm,TemperatureForm,VaccinationForm,ModeGardeForm,)


# =========================================================
# UTILITAIRE ADMINISTRATEUR
# =========================================================

def est_administrateur(user):
    return user.is_authenticated and (
        user.is_staff or user.is_superuser
    )


admin_required = user_passes_test(
    est_administrateur,
    login_url="sante:connexion_admin"
)


# =========================================================
# UTILITAIRE : REDIRECTION VERS LA FICHE ADMIN ENFANT
# =========================================================

def retour_admin_enfant(enfant):
    return redirect(
        "sante:administration_enfant_detail",
        enfant_id=enfant.id
    )


# =========================================================
# PAGE D'ACCUEIL
# =========================================================

def accueil(request):
    return render(
        request,
        "sante/accueil.html"
    )


# =========================================================
# DECONNEXION
# =========================================================

def logout_view(request):
    logout(request)

    return redirect(
        "sante:connexion"
    )


# =========================================================
# CONNEXION PARENT
# =========================================================

def connexion(request):

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(
                request,
                user
            )

            if user.is_staff or user.is_superuser:

                return redirect(
                    "sante:tableau_bord_admin"
                )

            return redirect(
                "sante:tableau_bord_parent"
            )

        messages.error(
            request,
            "Nom d'utilisateur ou mot de passe incorrect."
        )

    return render(
        request,
        "sante/connexion.html"
    )


# =========================================================
# INSCRIPTION
# =========================================================

def inscription(request):

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        telephone = request.POST.get(
            "telephone",
            ""
        ).strip()

        adresse = request.POST.get(
            "adresse",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        if not username or not email or not password:

            messages.error(
                request,
                "Veuillez remplir tous les champs obligatoires."
            )

            return render(
                request,
                "sante/inscription.html"
            )

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Ce nom d'utilisateur est déjà utilisé."
            )

            return render(
                request,
                "sante/inscription.html"
            )

        if User.objects.filter(
            email=email
        ).exists():

            messages.error(
                request,
                "Cette adresse email est déjà utilisée."
            )

            return render(
                request,
                "sante/inscription.html"
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        Parent.objects.create(
            user=user,
            telephone=telephone,
            adresse=adresse
        )

        login(
            request,
            user
        )

        messages.success(
            request,
            "Votre compte parent a été créé avec succès."
        )

        return redirect(
            "sante:tableau_bord_parent"
        )

    return render(
        request,
        "sante/inscription.html"
    )


# =========================================================
# TABLEAU DE BORD PARENT
# =========================================================

@login_required
def tableau_bord_parent(request):

    enfants = (
        Enfant.objects
        .filter(parent=request.user)
        .order_by("nom", "prenom")
    )

    nombre_enfants = enfants.count()

    nombre_consultations = (
        Consultation.objects
        .filter(enfant__parent=request.user)
        .count()
    )

    nombre_vaccinations = (
        Vaccination.objects
        .filter(enfant__parent=request.user)
        .count()
    )

    nombre_rendez_vous = (
        RendezVous.objects
        .filter(enfant__parent=request.user)
        .count()
    )

    aujourd_hui = timezone.localdate()

    rendez_vous_a_venir = (
        RendezVous.objects
        .filter(
            enfant__parent=request.user,
            date_rendez_vous__gte=aujourd_hui,
            statut__in=[
                "planifie",
                "confirme",
            ]
        )
        .select_related(
            "enfant",
            "professionnel"
        )
        .order_by(
            "date_rendez_vous",
            "heure"
        )[:5]
    )

    vaccinations_a_venir = (
        Vaccination.objects
        .filter(
            enfant__parent=request.user,
            date_prevue__gte=aujourd_hui,
            date_effectuee__isnull=True
        )
        .select_related("enfant")
        .order_by("date_prevue")[:5]
    )

    dernieres_consultations = (
        Consultation.objects
        .filter(
            enfant__parent=request.user
        )
        .select_related("enfant")
        .order_by("-date_consultation")[:5]
    )

    context = {
        "enfants": enfants,
        "nombre_enfants": nombre_enfants,
        "nombre_consultations": nombre_consultations,
        "nombre_vaccinations": nombre_vaccinations,
        "nombre_rendez_vous": nombre_rendez_vous,
        "rendez_vous_a_venir": rendez_vous_a_venir,
        "vaccinations_a_venir": vaccinations_a_venir,
        "dernieres_consultations": dernieres_consultations,
    }

    return render(
        request,
        "sante/tableau_bord_parent.html",
        context
    )


# =========================================================
# ASSISTANT GEMINI
# =========================================================

@login_required
@require_POST
def assistant_gemini(request):

    message = request.POST.get("message", "").strip()

    if not message:
        return JsonResponse(
            {"error": "Veuillez écrire un message."},
            status=400
        )

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return JsonResponse(
            {"error": "La clé API Gemini n'est pas configurée."},
            status=500
        )

    historique = request.session.get("assistant_historique", [])
    historique_texte = "\n".join(
        f"{element['role']} : {element['text']}"
        for element in historique[-10:]
    )

    prompt = f"""
Tu es l'assistant santé de Toukpedio.
Réponds en français, clairement et simplement.
Ne pose jamais de diagnostic et ne remplace pas un professionnel de santé.
En cas de symptômes graves, recommande immédiatement les urgences.

Historique de la conversation :
{historique_texte}

Utilisateur : {message}
Assistant :
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )

        reponse = response.text or "Je ne peux pas répondre actuellement."

        historique.extend([
            {"role": "Utilisateur", "text": message},
            {"role": "Assistant", "text": reponse},
        ])
        request.session["assistant_historique"] = historique[-10:]
        request.session.modified = True

        return JsonResponse({"reply": reponse})

    except Exception:
        return JsonResponse(
            {"error": "Le service Gemini est momentanément indisponible."},
            status=503
        )


# =========================================================
# =========================================================
#                 ADMINISTRATION
# =========================================================
# =========================================================


# =========================================================
# TABLEAU DE BORD ADMIN
# =========================================================
@login_required
@user_passes_test(est_administrateur)
def tableau_bord_admin(request):

    nombre_enfants = Enfant.objects.count()
    dernier_enfant = Enfant.objects.order_by("-id").first()
    nombre_consultations = Consultation.objects.count()
    nombre_vaccinations = Vaccination.objects.count()
    nombre_symptomes = JournalSymptome.objects.count()
    nombre_temperatures = Temperature.objects.count()
    nombre_traitements = Traitement.objects.count()
    nombre_rendez_vous = RendezVous.objects.count()
    nombre_partages = PartageEnfant.objects.count()
    nombre_modes_garde = ModeGarde.objects.count()
    

    contexte = {
        "nombre_enfants": nombre_enfants,
        "nombre_consultations": nombre_consultations,
        "nombre_vaccinations": nombre_vaccinations,
        "nombre_symptomes": nombre_symptomes,
        "nombre_temperatures": nombre_temperatures,
        "nombre_traitements": nombre_traitements,
        "nombre_rendez_vous": nombre_rendez_vous,
        "nombre_partages": nombre_partages,
        "nombre_modes_garde": nombre_modes_garde,
        
        "dernier_enfant": dernier_enfant,
    }

    return render(
        request,
        "sante/tableau_bord_admin.html",
        contexte
    )

@admin_required
def administration(request):

    nombre_parents = Parent.objects.count()
    nombre_enfants = Enfant.objects.count()
    nombre_vaccinations = Vaccination.objects.count()
    nombre_traitements = Traitement.objects.count()
    nombre_temperatures = Temperature.objects.count()
    nombre_consultations = Consultation.objects.count()
    nombre_rendez_vous = RendezVous.objects.count()

    enfants_recents = (
        Enfant.objects
        .select_related("parent")
        .order_by("-date_creation")[:10]
    )

    rendez_vous_recents = (
        RendezVous.objects
        .select_related(
            "enfant",
            "professionnel"
        )
        .order_by("-date_creation")[:10]
    )

    context = {
        "nombre_parents": nombre_parents,
        "nombre_enfants": nombre_enfants,
        "nombre_vaccinations": nombre_vaccinations,
        "nombre_traitements": nombre_traitements,
        "nombre_temperatures": nombre_temperatures,
        "nombre_consultations": nombre_consultations,
        "nombre_rendez_vous": nombre_rendez_vous,
        "enfants_recents": enfants_recents,
        "rendez_vous_recents": rendez_vous_recents,
    }

    return render(
        request,
        "sante/administration.html",
        context
    )


# =========================================================
# LISTE DES ENFANTS
# =========================================================

@admin_required
def administration_enfants(request):

    recherche = request.GET.get(
        "recherche",
        ""
    ).strip()

    enfants = (
        Enfant.objects
        .select_related("parent")
        .order_by(
            "nom",
            "prenom"
        )
    )

    if recherche:

        enfants = enfants.filter(
            models.Q(prenom__icontains=recherche)
            |
            models.Q(nom__icontains=recherche)
            |
            models.Q(parent__username__icontains=recherche)
        )

    return render(
        request,
        "sante/admin_enfants.html",
        {
            "enfants": enfants,
            "recherche": recherche,
        }
    )


# =========================================================
# AJOUTER UN ENFANT - ADMIN
# =========================================================

@admin_required
def administration_ajouter_enfant(request):

    if request.method == "POST":

        nom = request.POST.get(
            "nom",
            ""
        ).strip()

        prenom = request.POST.get(
            "prenom",
            ""
        ).strip()

        date_naissance = request.POST.get(
            "date_naissance"
        )

        sexe = request.POST.get(
            "sexe"
        )

        parent_id = request.POST.get(
            "parent"
        )

        parent = get_object_or_404(
            User,
            id=parent_id
        )

        if not nom or not prenom or not date_naissance or not sexe:

            messages.error(
                request,
                "Veuillez remplir tous les champs obligatoires."
            )

            return render(
                request,
                "sante/admin_ajouter_enfant.html",
                {
                    "parents": User.objects.filter(
                        is_staff=False,
                        is_superuser=False
                    )
                }
            )

        enfant = Enfant.objects.create(
            nom=nom,
            prenom=prenom,
            date_naissance=date_naissance,
            sexe=sexe,
            parent=parent,
            photo=request.FILES.get("photo"),
            telephone_parent=request.POST.get(
                "telephone_parent",
                ""
            ).strip(),
            adresse=request.POST.get(
                "adresse",
                ""
            ).strip(),
            groupe_sanguin=request.POST.get(
                "groupe_sanguin",
                ""
            ).strip(),
            allergies=request.POST.get(
                "allergies",
                ""
            ).strip(),
            traitement=request.POST.get(
                "traitement",
                ""
            ).strip(),
            antecedents=request.POST.get(
                "antecedents",
                ""
            ).strip(),
            observations=request.POST.get(
                "observations",
                ""
            ).strip(),
        )

        messages.success(
            request,
            f"{enfant.prenom} {enfant.nom} a été ajouté avec succès."
        )

        return retour_admin_enfant(
            enfant
        )

    parents = (
        User.objects
        .filter(
            is_staff=False,
            is_superuser=False
        )
        .order_by("username")
    )

    return render(
        request,
        "sante/admin_ajouter_enfant.html",
        {
            "parents": parents
        }
    )


# =========================================================
# MODIFIER UN ENFANT - ADMIN
# =========================================================

@admin_required
def administration_modifier_enfant(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id
    )

    if request.method == "POST":

        enfant.nom = request.POST.get(
            "nom",
            ""
        ).strip()

        enfant.prenom = request.POST.get(
            "prenom",
            ""
        ).strip()

        enfant.date_naissance = request.POST.get(
            "date_naissance"
        )

        enfant.sexe = request.POST.get(
            "sexe"
        )

        parent_id = request.POST.get(
            "parent"
        )

        if parent_id:

            enfant.parent = get_object_or_404(
                User,
                id=parent_id
            )

        enfant.telephone_parent = request.POST.get(
            "telephone_parent",
            ""
        ).strip()

        enfant.adresse = request.POST.get(
            "adresse",
            ""
        ).strip()

        enfant.groupe_sanguin = request.POST.get(
            "groupe_sanguin",
            ""
        ).strip()

        enfant.allergies = request.POST.get(
            "allergies",
            ""
        ).strip()

        enfant.traitement = request.POST.get(
            "traitement",
            ""
        ).strip()

        enfant.antecedents = request.POST.get(
            "antecedents",
            ""
        ).strip()

        enfant.observations = request.POST.get(
            "observations",
            ""
        ).strip()

        photo = request.FILES.get("photo")

        if photo:
            enfant.photo = photo

        enfant.save()

        messages.success(
            request,
            f"Le dossier de {enfant.prenom} a été modifié."
        )

        return retour_admin_enfant(
            enfant
        )

    parents = (
        User.objects
        .filter(
            is_staff=False,
            is_superuser=False
        )
        .order_by("username")
    )

    return render(
        request,
        "sante/admin_modifier_enfant.html",
        {
            "enfant": enfant,
            "parents": parents,
        }
    )


# =========================================================
# SUPPRIMER UN ENFANT - ADMIN
# =========================================================

@admin_required
def administration_supprimer_enfant(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id
    )

    if request.method != "POST":

        return render(
            request,
            "sante/admin_confirmer_suppression.html",
            {
                "objet": enfant,
                "type_objet": "enfant",
                "retour": "sante:administration_enfant_detail",
                "retour_id": enfant.id,
            }
        )

    nom = f"{enfant.prenom} {enfant.nom}"

    enfant.delete()

    messages.success(
        request,
        f"Le dossier de {nom} a été supprimé définitivement."
    )

    return redirect(
        "sante:admin_enfants"
    )


# =========================================================
# DETAIL COMPLET D'UN ENFANT
# =========================================================

@admin_required
def administration_enfant_detail(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant.objects.select_related("parent"),
        id=enfant_id
    )

    context = {
        "enfant": enfant,

        "vaccinations": (
            enfant.vaccinations
            .all()
            .order_by("date_prevue")
        ),

        "temperatures": (
            enfant.temperatures
            .all()
            .order_by("-date_prise")
        ),

        "traitements": (
            enfant.traitements
            .all()
            .order_by("prochaine_prise")
        ),

        "consultations": (
            enfant.consultations
            .all()
            .order_by("-date_consultation")
        ),

        "symptomes": (
            enfant.journaux_symptomes
            .all()
            .order_by("-date")
        ),

        "croissances": (
            enfant.croissances
            .all()
            .order_by("-date_mesure")
        ),

        "bien_etre": (
            enfant.bien_etre
            .all()
            .order_by("-date_suivi")
        ),

        "rendez_vous": (
            enfant.rendez_vous
            .all()
            .select_related("professionnel")
            .order_by(
                "date_rendez_vous",
                "heure"
            )
        ),

        "modes_garde": (
            enfant.modes_garde
            .all()
            .order_by("-date_creation")
        ),

        "partages": (
            enfant.partages
            .all()
            .select_related("parent")
            .order_by("-date_invitation")
        ),
    }

    return render(
        request,
        "sante/admin_enfant_detail.html",
        context
    )


# =========================================================
# =========================================================
# CRUD SYMPTOMES
# =========================================================
# =========================================================

@admin_required
def administration_modifier_symptome(
    request,
    symptome_id
):

    symptome = get_object_or_404(
        JournalSymptome,
        id=symptome_id
    )

    enfant = symptome.enfant

    if request.method == "POST":

        form = JournalSymptomeForm(
            request.POST,
            instance=symptome
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Le symptôme a été modifié avec succès."
            )

            return retour_admin_enfant(
                enfant
            )

    else:

        form = JournalSymptomeForm(
            instance=symptome
        )

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "enfant": enfant,
            "titre": "Modifier le symptôme",
            "objet": "Symptôme",
        }
    )


@admin_required
def administration_supprimer_symptome(
    request,
    symptome_id
):

    symptome = get_object_or_404(
        JournalSymptome,
        id=symptome_id
    )

    enfant = symptome.enfant

    if request.method == "POST":

        symptome.delete()

        messages.success(
            request,
            "Le symptôme a été supprimé."
        )

        return retour_admin_enfant(
            enfant
        )

    return render(
        request,
        "sante/admin_confirmer_suppression.html",
        {
            "objet": symptome,
            "type_objet": "symptôme",
            "enfant": enfant,
        }
    )


# =========================================================
# CRUD CONSULTATIONS
# =========================================================

@login_required
@user_passes_test(est_administrateur)
def administration_ajouter_symptome(request, enfant_id):
    enfant = get_object_or_404(Enfant, id=enfant_id)

    if request.method == "POST":
        form = JournalSymptomeForm(request.POST)

        if form.is_valid():
            symptome = form.save(commit=False)
            symptome.enfant = enfant
            symptome.save()

            messages.success(
                request,
                "Le symptôme a été ajouté avec succès."
            )

            return redirect(
                "sante:administration_enfant_detail",
                enfant_id=enfant.id
            )

    else:
        form = JournalSymptomeForm()

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "titre": f"Ajouter un symptôme pour {enfant.prenom}",
            "enfant": enfant,
        }
    )

@admin_required
def administration_ajouter_consultation(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id
    )

    if request.method == "POST":

        form = ConsultationForm(
            request.POST
        )

        if form.is_valid():

            consultation = form.save(
                commit=False
            )

            consultation.enfant = enfant

            consultation.save()

            messages.success(
                request,
                "Consultation ajoutée avec succès."
            )

            return retour_admin_enfant(
                enfant
            )

    else:

        form = ConsultationForm()

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "enfant": enfant,
            "titre": "Ajouter une consultation",
            "objet": "Consultation",
        }
    )


@admin_required
def administration_modifier_consultation(
    request,
    consultation_id
):

    consultation = get_object_or_404(
        Consultation,
        id=consultation_id
    )

    enfant = consultation.enfant

    if request.method == "POST":

        form = ConsultationForm(
            request.POST,
            instance=consultation
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Consultation modifiée avec succès."
            )

            return retour_admin_enfant(
                enfant
            )

    else:

        form = ConsultationForm(
            instance=consultation
        )

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "enfant": enfant,
            "titre": "Modifier la consultation",
            "objet": "Consultation",
        }
    )


@admin_required
def administration_supprimer_consultation(
    request,
    consultation_id
):

    consultation = get_object_or_404(
        Consultation,
        id=consultation_id
    )

    enfant = consultation.enfant

    if request.method == "POST":

        consultation.delete()

        messages.success(
            request,
            "Consultation supprimée."
        )

        return retour_admin_enfant(
            enfant
        )

    return render(
        request,
        "sante/admin_confirmer_suppression.html",
        {
            "objet": consultation,
            "type_objet": "consultation",
            "enfant": enfant,
        }
    )


# =========================================================
# CRUD VACCINATIONS
# =========================================================

@admin_required
def administration_ajouter_vaccination(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id
    )

    if request.method == "POST":

        form = VaccinationForm(
            request.POST
        )

        if form.is_valid():

            vaccination = form.save(
                commit=False
            )

            vaccination.enfant = enfant

            vaccination.save()

            messages.success(
                request,
                "Vaccination ajoutée avec succès."
            )

            return retour_admin_enfant(
                enfant
            )

    else:

        form = VaccinationForm()

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "enfant": enfant,
            "titre": "Ajouter une vaccination",
            "objet": "Vaccination",
        }
    )


@admin_required
def administration_modifier_vaccination(
    request,
    vaccination_id
):

    vaccination = get_object_or_404(
        Vaccination,
        id=vaccination_id
    )

    enfant = vaccination.enfant

    if request.method == "POST":

        form = VaccinationForm(
            request.POST,
            instance=vaccination
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Vaccination modifiée avec succès."
            )

            return retour_admin_enfant(
                enfant
            )

    else:

        form = VaccinationForm(
            instance=vaccination
        )

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "enfant": enfant,
            "titre": "Modifier la vaccination",
            "objet": "Vaccination",
        }
    )


@admin_required
def administration_supprimer_vaccination(
    request,
    vaccination_id
):

    vaccination = get_object_or_404(
        Vaccination,
        id=vaccination_id
    )

    enfant = vaccination.enfant

    if request.method == "POST":

        vaccination.delete()

        messages.success(
            request,
            "Vaccination supprimée."
        )

        return retour_admin_enfant(
            enfant
        )

    return render(
        request,
        "sante/admin_confirmer_suppression.html",
        {
            "objet": vaccination,
            "type_objet": "vaccination",
            "enfant": enfant,
        }
    )


# =========================================================
# CRUD CROISSANCE
# =========================================================

@admin_required
def administration_ajouter_croissance(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id
    )

    champs = [
        "date_mesure",
        "poids",
        "taille",
        "perimetre_cranien",
        "observations",
    ]

    from django.forms import modelform_factory

    CroissanceForm = modelform_factory(
        SuiviCroissance,
        fields=champs
    )

    if request.method == "POST":

        form = CroissanceForm(
            request.POST
        )

        if form.is_valid():

            croissance_obj = form.save(
                commit=False
            )

            croissance_obj.enfant = enfant

            croissance_obj.save()

            messages.success(
                request,
                "Mesure de croissance ajoutée."
            )

            return retour_admin_enfant(
                enfant
            )

    else:

        form = CroissanceForm()

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "enfant": enfant,
            "titre": "Ajouter une mesure de croissance",
            "objet": "Croissance",
        }
    )


@admin_required
def administration_modifier_croissance(
    request,
    croissance_id
):

    croissance_obj = get_object_or_404(
        SuiviCroissance,
        id=croissance_id
    )

    enfant = croissance_obj.enfant

    from django.forms import modelform_factory

    CroissanceForm = modelform_factory(
        SuiviCroissance,
        fields=[
            "date_mesure",
            "poids",
            "taille",
            "perimetre_cranien",
            "observations",
        ]
    )

    if request.method == "POST":

        form = CroissanceForm(
            request.POST,
            instance=croissance_obj
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Mesure de croissance modifiée."
            )

            return retour_admin_enfant(
                enfant
            )

    else:

        form = CroissanceForm(
            instance=croissance_obj
        )

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "enfant": enfant,
            "titre": "Modifier la croissance",
            "objet": "Croissance",
        }
    )


@admin_required
def administration_supprimer_croissance(
    request,
    croissance_id
):

    croissance_obj = get_object_or_404(
        SuiviCroissance,
        id=croissance_id
    )

    enfant = croissance_obj.enfant

    if request.method == "POST":

        croissance_obj.delete()

        messages.success(
            request,
            "Mesure de croissance supprimée."
        )

        return retour_admin_enfant(
            enfant
        )

    return render(
        request,
        "sante/admin_confirmer_suppression.html",
        {
            "objet": croissance_obj,
            "type_objet": "mesure de croissance",
            "enfant": enfant,
        }
    )


# =========================================================
# CRUD BIEN-ÊTRE
# =========================================================

@admin_required
def administration_ajouter_bien_etre(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id
    )

    from django.forms import modelform_factory

    BienEtreFormAdmin = modelform_factory(
        BienEtre,
        fields=[
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
    )

    if request.method == "POST":

        form = BienEtreFormAdmin(
            request.POST
        )

        if form.is_valid():

            objet = form.save(
                commit=False
            )

            objet.enfant = enfant

            objet.save()

            messages.success(
                request,
                "Suivi du bien-être ajouté."
            )

            return retour_admin_enfant(
                enfant
            )

    else:

        form = BienEtreFormAdmin()

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "enfant": enfant,
            "titre": "Ajouter un suivi du bien-être",
            "objet": "Bien-être",
        }
    )


@admin_required
def administration_modifier_bien_etre(
    request,
    bien_etre_id
):

    objet = get_object_or_404(
        BienEtre,
        id=bien_etre_id
    )

    enfant = objet.enfant

    from django.forms import modelform_factory

    BienEtreFormAdmin = modelform_factory(
        BienEtre,
        fields=[
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
    )

    if request.method == "POST":

        form = BienEtreFormAdmin(
            request.POST,
            instance=objet
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Suivi du bien-être modifié."
            )

            return retour_admin_enfant(
                enfant
            )

    else:

        form = BienEtreFormAdmin(
            instance=objet
        )

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "enfant": enfant,
            "titre": "Modifier le suivi du bien-être",
            "objet": "Bien-être",
        }
    )


@admin_required
def administration_supprimer_bien_etre(
    request,
    bien_etre_id
):

    objet = get_object_or_404(
        BienEtre,
        id=bien_etre_id
    )

    enfant = objet.enfant

    if request.method == "POST":

        objet.delete()

        messages.success(
            request,
            "Suivi du bien-être supprimé."
        )

        return retour_admin_enfant(
            enfant
        )

    return render(
        request,
        "sante/admin_confirmer_suppression.html",
        {
            "objet": objet,
            "type_objet": "suivi du bien-être",
            "enfant": enfant,
        }
    )


# =========================================================
# CRUD TEMPERATURE
# =========================================================

@admin_required
def administration_ajouter_temperature(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id
    )

    if request.method == "POST":

        form = TemperatureForm(
            request.POST
        )

        if form.is_valid():

            objet = form.save(
                commit=False
            )

            objet.enfant = enfant

            objet.save()

            messages.success(
                request,
                "Température ajoutée."
            )

            return retour_admin_enfant(
                enfant
            )

    else:

        form = TemperatureForm()

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "enfant": enfant,
            "titre": "Ajouter une température",
            "objet": "Température",
        }
    )


@admin_required
def administration_modifier_temperature(
    request,
    temperature_id
):

    objet = get_object_or_404(
        Temperature,
        id=temperature_id
    )

    enfant = objet.enfant

    if request.method == "POST":

        form = TemperatureForm(
            request.POST,
            instance=objet
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Température modifiée."
            )

            return retour_admin_enfant(
                enfant
            )

    else:

        form = TemperatureForm(
            instance=objet
        )

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "enfant": enfant,
            "titre": "Modifier la température",
            "objet": "Température",
        }
    )


@admin_required
def administration_supprimer_temperature(
    request,
    temperature_id
):

    objet = get_object_or_404(
        Temperature,
        id=temperature_id
    )

    enfant = objet.enfant

    if request.method == "POST":

        objet.delete()

        messages.success(
            request,
            "Température supprimée."
        )

        return retour_admin_enfant(
            enfant
        )

    return render(
        request,
        "sante/admin_confirmer_suppression.html",
        {
            "objet": objet,
            "type_objet": "température",
            "enfant": enfant,
        }
    )


# =========================================================
# CRUD TRAITEMENTS
# =========================================================

@admin_required
def administration_ajouter_traitement(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id
    )

    if request.method == "POST":

        form = TraitementForm(
            request.POST
        )

        if form.is_valid():

            objet = form.save(
                commit=False
            )

            objet.enfant = enfant
            objet.prochaine_prise = objet.premiere_prise

            objet.save()

            messages.success(
                request,
                "Traitement ajouté."
            )

            return retour_admin_enfant(
                enfant
            )

    else:

        form = TraitementForm()

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "enfant": enfant,
            "titre": "Ajouter un traitement",
            "objet": "Traitement",
        }
    )


@admin_required
def administration_modifier_traitement(
    request,
    traitement_id
):

    objet = get_object_or_404(
        Traitement,
        id=traitement_id
    )

    enfant = objet.enfant

    if request.method == "POST":

        form = TraitementForm(
            request.POST,
            instance=objet
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Traitement modifié."
            )

            return retour_admin_enfant(
                enfant
            )

    else:

        form = TraitementForm(
            instance=objet
        )

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "enfant": enfant,
            "titre": "Modifier le traitement",
            "objet": "Traitement",
        }
    )


@admin_required
def administration_supprimer_traitement(
    request,
    traitement_id
):

    objet = get_object_or_404(
        Traitement,
        id=traitement_id
    )

    enfant = objet.enfant

    if request.method == "POST":

        objet.delete()

        messages.success(
            request,
            "Traitement supprimé."
        )

        return retour_admin_enfant(
            enfant
        )

    return render(
        request,
        "sante/admin_confirmer_suppression.html",
        {
            "objet": objet,
            "type_objet": "traitement",
            "enfant": enfant,
        }
    )


# =========================================================
# CRUD RENDEZ-VOUS
# =========================================================

@admin_required
def administration_ajouter_rendez_vous(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id
    )

    from django.forms import modelform_factory

    RendezVousFormAdmin = modelform_factory(
        RendezVous,
        fields=[
            "date_rendez_vous",
            "heure",
            "motif",
            "professionnel",
            "statut",
            "notes",
        ]
    )

    if request.method == "POST":

        form = RendezVousFormAdmin(
            request.POST
        )

        if form.is_valid():

            objet = form.save(
                commit=False
            )

            objet.enfant = enfant

            objet.save()

            messages.success(
                request,
                "Rendez-vous ajouté."
            )

            return retour_admin_enfant(
                enfant
            )

    else:

        form = RendezVousFormAdmin()

    form.fields["professionnel"].queryset = (
        User.objects
        .filter(is_staff=True)
        .order_by(
            "first_name",
            "last_name"
        )
    )

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "enfant": enfant,
            "titre": "Ajouter un rendez-vous",
            "objet": "Rendez-vous",
        }
    )


@admin_required
def administration_modifier_rendez_vous(
    request,
    rendez_vous_id
):

    objet = get_object_or_404(
        RendezVous,
        id=rendez_vous_id
    )

    enfant = objet.enfant

    from django.forms import modelform_factory

    RendezVousFormAdmin = modelform_factory(
        RendezVous,
        fields=[
            "date_rendez_vous",
            "heure",
            "motif",
            "professionnel",
            "statut",
            "notes",
        ]
    )

    if request.method == "POST":

        form = RendezVousFormAdmin(
            request.POST,
            instance=objet
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Rendez-vous modifié."
            )

            return retour_admin_enfant(
                enfant
            )

    else:

        form = RendezVousFormAdmin(
            instance=objet
        )

    form.fields["professionnel"].queryset = (
        User.objects
        .filter(is_staff=True)
        .order_by(
            "first_name",
            "last_name"
        )
    )

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "enfant": enfant,
            "titre": "Modifier le rendez-vous",
            "objet": "Rendez-vous",
        }
    )


@admin_required
def administration_supprimer_rendez_vous(
    request,
    rendez_vous_id
):

    objet = get_object_or_404(
        RendezVous,
        id=rendez_vous_id
    )

    enfant = objet.enfant

    if request.method == "POST":

        objet.delete()

        messages.success(
            request,
            "Rendez-vous supprimé."
        )

        return retour_admin_enfant(
            enfant
        )

    return render(
        request,
        "sante/admin_confirmer_suppression.html",
        {
            "objet": objet,
            "type_objet": "rendez-vous",
            "enfant": enfant,
        }
    )


# =========================================================
# CRUD PARTAGE PARENT
# =========================================================

@admin_required
def administration_ajouter_partage(request, enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id
    )

    if request.method == "POST":

        email = request.POST.get("email", "").strip().lower()

        if not email:
            messages.error(
                request,
                "Veuillez saisir l'adresse e-mail du parent."
            )

            return redirect(
                "sante:administration_ajouter_partage",
                enfant_id=enfant.id
            )

        # Recherche du compte parent
        parent = User.objects.filter(
            email__iexact=email
        ).first()

        if not parent:
            messages.error(
                request,
                "Aucun compte TOUKPEDIO ne correspond à cette adresse e-mail."
            )

            return redirect(
                "sante:administration_ajouter_partage",
                enfant_id=enfant.id
            )

        # Le parent principal ne peut pas être invité
        if parent == enfant.parent:

            messages.warning(
                request,
                "Ce parent est déjà le parent principal de cet enfant."
            )

            return redirect(
                "sante:administration_enfant_detail",
                enfant_id=enfant.id
            )

        # Vérifier si un partage existe déjà
        partage_existant = PartageEnfant.objects.filter(
            enfant=enfant,
            parent=parent
        ).first()

        if partage_existant:

            if partage_existant.accepte:

                messages.info(
                    request,
                    "Ce parent possède déjà un accès au dossier."
                )

            else:

                messages.info(
                    request,
                    "Une invitation existe déjà pour ce parent."
                )

            return redirect(
                "sante:administration_enfant_detail",
                enfant_id=enfant.id
            )

        # Création du partage
        PartageEnfant.objects.create(
            enfant=enfant,
            parent=parent,
            accepte=False
        )

        messages.success(
            request,
            f"Invitation créée pour {parent.email}."
        )

        return redirect(
            "sante:administration_enfant_detail",
            enfant_id=enfant.id
        )

    return render(
        request,
        "sante/admin_ajouter_partage.html",
        {
            "enfant": enfant,
        }
    )

@admin_required
def administration_supprimer_partage(
    request,
    partage_id
):

    partage = get_object_or_404(
        PartageEnfant,
        id=partage_id
    )

    enfant = partage.enfant

    if request.method == "POST":

        partage.delete()

        messages.success(
            request,
            "Le partage a été supprimé."
        )

        return retour_admin_enfant(
            enfant
        )

    return render(
        request,
        "sante/admin_confirmer_suppression.html",
        {
            "objet": partage,
            "type_objet": "partage",
            "enfant": enfant,
        }
    )


@admin_required
def administration_modifier_partage(
    request,
    partage_id
):

    partage = get_object_or_404(
        PartageEnfant,
        id=partage_id
    )

    enfant = partage.enfant

    if request.method == "POST":

        partage.accepte = (
            request.POST.get("accepte")
            == "1"
        )

        partage.save()

        messages.success(
            request,
            "Statut du partage modifié."
        )

        return retour_admin_enfant(
            enfant
        )

    return render(
        request,
        "sante/admin_modifier_partage.html",
        {
            "partage": partage,
            "enfant": enfant,
        }
    )


# =========================================================
# CRUD MODE GARDE
# =========================================================

@admin_required
def administration_ajouter_mode_garde(request, enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id
    )

    if request.method == "POST":

        formulaire = ModeGardeForm(request.POST)

        if formulaire.is_valid():

            mode_garde = formulaire.save(commit=False)

            mode_garde.enfant = enfant

            # Si ton modèle possède un champ parent/created_by,
            # on peut le renseigner ici.
            if hasattr(mode_garde, "parent"):
                mode_garde.parent = enfant.parent

            if hasattr(mode_garde, "cree_par"):
                mode_garde.cree_par = request.user

            mode_garde.save()

            messages.success(
                request,
                f"Le mode garde de {enfant.prenom} a été créé avec succès."
            )

            return redirect(
                "sante:administration_enfant_detail",
                enfant_id=enfant.id
            )

    else:

        formulaire = ModeGardeForm()

    return render(
        request,
        "sante/admin_form.html",
        {
            "enfant": enfant,
            "form": formulaire,
            "objet": "Mode garde",
            "titre": "Créer un mode garde",
        }
    )

@admin_required
def administration_modifier_mode_garde(
    request,
    mode_garde_id
):

    mode_garde = get_object_or_404(
        ModeGarde,
        id=mode_garde_id
    )

    enfant = mode_garde.enfant

    if request.method == "POST":

        form = ModeGardeForm(
            request.POST,
            instance=mode_garde
        )

        if form.is_valid():

            objet = form.save(
                commit=False
            )

            objet.enfant = enfant
            objet.parent = mode_garde.parent

            objet.save()

            messages.success(
                request,
                "Mode garde modifié avec succès."
            )

            return retour_admin_enfant(
                enfant
            )

    else:

        form = ModeGardeForm(
            instance=mode_garde
        )

    return render(
        request,
        "sante/admin_form.html",
        {
            "form": form,
            "enfant": enfant,
            "titre": "Modifier le mode garde",
            "objet": "Mode garde",
        }
    )


@admin_required
def administration_supprimer_mode_garde(
    request,
    mode_garde_id
):

    mode_garde = get_object_or_404(
        ModeGarde,
        id=mode_garde_id
    )

    enfant = mode_garde.enfant

    if request.method == "POST":

        mode_garde.delete()

        messages.success(
            request,
            "Mode garde supprimé."
        )

        return retour_admin_enfant(
            enfant
        )

    return render(
        request,
        "sante/admin_confirmer_suppression.html",
        {
            "objet": mode_garde,
            "type_objet": "mode garde",
            "enfant": enfant,
        }
    )


@admin_required
def administration_desactiver_mode_garde(
    request,
    mode_garde_id
):

    mode_garde = get_object_or_404(
        ModeGarde,
        id=mode_garde_id
    )

    enfant = mode_garde.enfant

    if request.method == "POST":

        mode_garde.actif = False
        mode_garde.save(
            update_fields=["actif"]
        )

        messages.success(
            request,
            "Mode garde désactivé."
        )

    return retour_admin_enfant(
        enfant
    )


# =========================================================
# CONNEXION ADMIN
# =========================================================

def connexion_admin(request):

    if (
        request.user.is_authenticated
        and request.user.is_staff
    ):

        return redirect(
            "sante:tableau_bord_admin"
        )

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            if user.is_staff or user.is_superuser:

                login(
                    request,
                    user
                )

                return redirect(
                    "sante:tableau_bord_admin"
                )

            messages.error(
                request,
                "Ce compte n'a pas accès à l'administration."
            )

        else:

            messages.error(
                request,
                "Identifiants administrateur incorrects."
            )

    return render(
        request,
        "sante/connexion_admin.html"
    )


# =========================================================
# MES ENFANTS
# =========================================================

@login_required
def enfant(request):

    enfants = (
        Enfant.objects
        .filter(parent=request.user)
        .order_by(
            "nom",
            "prenom"
        )
    )

    return render(
        request,
        "sante/enfant.html",
        {
            "enfants": enfants
        }
    )


# =========================================================
# AJOUTER UN ENFANT - PARENT
# =========================================================

@login_required
def ajouter_enfant(request):

    if request.method == "POST":

        nom = request.POST.get(
            "nom",
            ""
        ).strip()

        prenom = request.POST.get(
            "prenom",
            ""
        ).strip()

        date_naissance = request.POST.get(
            "date_naissance"
        )

        sexe = request.POST.get(
            "sexe"
        )

        if not nom or not prenom or not date_naissance or not sexe:

            messages.error(
                request,
                "Veuillez remplir tous les champs obligatoires."
            )

            return render(
                request,
                "sante/ajouter_enfant.html"
            )

        Enfant.objects.create(
            nom=nom,
            prenom=prenom,
            date_naissance=date_naissance,
            sexe=sexe,
            photo=request.FILES.get("photo"),
            parent=request.user,
            telephone_parent=request.POST.get(
                "telephone_parent",
                ""
            ).strip(),
            adresse=request.POST.get(
                "adresse",
                ""
            ).strip(),
            groupe_sanguin=request.POST.get(
                "groupe_sanguin",
                ""
            ).strip(),
            allergies=request.POST.get(
                "allergies",
                ""
            ).strip(),
            traitement=request.POST.get(
                "traitement",
                ""
            ).strip(),
            antecedents=request.POST.get(
                "antecedents",
                ""
            ).strip(),
            observations=request.POST.get(
                "observations",
                ""
            ).strip(),
        )

        messages.success(
            request,
            f"{prenom} {nom} a été ajouté avec succès."
        )

        return redirect(
            "sante:enfant"
        )

    return render(
        request,
        "sante/ajouter_enfant.html"
    )


# =========================================================
# AJOUTER SYMPTOME - PARENT
# =========================================================

@login_required
def ajouter_symptome(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        form = JournalSymptomeForm(
            request.POST
        )

        if form.is_valid():

            journal = form.save(
                commit=False
            )

            journal.enfant = enfant
            journal.date = timezone.localdate()

            journal.save()

            fichier_photo = request.FILES.get(
                "photo"
            )

            description_photo = request.POST.get(
                "photo_description",
                ""
            ).strip()

            if fichier_photo:

                PhotoSymptome.objects.create(
                    journal=journal,
                    photo=fichier_photo,
                    description=description_photo
                )

            messages.success(
                request,
                "Le suivi a bien été enregistré."
            )

            return redirect(
                "sante:detail_enfant",
                enfant_id=enfant.id
            )

    else:

        form = JournalSymptomeForm()

    return render(
        request,
        "sante/ajouter_symptome.html",
        {
            "enfant": enfant,
            "form": form,
        }
    )


# =========================================================
# MODIFIER SYMPTOME - PARENT
# =========================================================
@login_required
def modifier_symptome(request, symptome_id):

    symptome = get_object_or_404(
        JournalSymptome,
        id=symptome_id
    )

    enfant = symptome.enfant

    # Vérification du propriétaire
    acces_principal = (
        enfant.parent == request.user
    )

    # Vérification d'un partage accepté
    acces_partage = PartageEnfant.objects.filter(
        enfant=enfant,
        parent=request.user,
        accepte=True
    ).exists()

    if not (acces_principal or acces_partage):
        messages.error(
            request,
            "Vous n'avez pas accès à ce dossier."
        )

        return redirect("sante:enfant")

    if request.method == "POST":

        formulaire = JournalSymptomeForm(
            request.POST,
            instance=symptome
        )

        if formulaire.is_valid():

            formulaire.save()

            messages.success(
                request,
                "Le symptôme a été modifié avec succès."
            )

            return redirect(
                "sante:detail_enfant",
                enfant_id=enfant.id
            )

    else:

        formulaire = JournalSymptomeForm(
            instance=symptome
        )

    return render(
        request,
        "sante/modifier_symptome.html",
        {
            "form": formulaire,
            "symptome": symptome,
            "enfant": enfant,
        }
    )

# =========================================================
# SUPPRIMER SYMPTOME - PARENT
# =========================================================

@login_required
def supprimer_symptome(request, symptome_id):

    symptome = get_object_or_404(
        JournalSymptome,
        id=symptome_id
    )

    enfant = symptome.enfant

    # Vérifier que l'utilisateur a accès à l'enfant
    acces_principal = (
        enfant.parent == request.user
    )

    acces_partage = PartageEnfant.objects.filter(
        enfant=enfant,
        parent=request.user,
        accepte=True
    ).exists()

    if not (acces_principal or acces_partage):
        messages.error(
            request,
            "Vous n'avez pas accès à ce dossier."
        )
        return redirect("sante:enfant")

    # Suppression
    symptome.delete()

    messages.success(
        request,
        "Le symptôme a été supprimé avec succès."
    )

    return redirect(
        "sante:detail_enfant",
        enfant_id=enfant.id
    )

# =========================================================
# DETAIL ENFANT - PARENT
# =========================================================

@login_required
def detail_enfant(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id
    )

    acces_principal = (
        enfant.parent == request.user
    )

    acces_partage = (
        PartageEnfant.objects
        .filter(
            enfant=enfant,
            parent=request.user,
            accepte=True
        )
        .exists()
    )

    if not acces_principal and not acces_partage:

        messages.error(
            request,
            "Vous n'avez pas accès à ce dossier."
        )

        return redirect(
            "sante:tableau_bord_parent"
        )

    symptomes = (
        JournalSymptome.objects
        .filter(enfant=enfant)
        .order_by("-date")
    )

    return render(
        request,
        "sante/detail_enfant.html",
        {
            "enfant": enfant,
            "symptomes": symptomes,
        }
    )


# =========================================================
# MODIFIER ENFANT - PARENT
# =========================================================

@login_required
def modifier_enfant(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        enfant.nom = request.POST.get(
            "nom",
            ""
        ).strip()

        enfant.prenom = request.POST.get(
            "prenom",
            ""
        ).strip()

        enfant.date_naissance = request.POST.get(
            "date_naissance"
        )

        enfant.sexe = request.POST.get(
            "sexe"
        )

        enfant.telephone_parent = request.POST.get(
            "telephone_parent",
            ""
        ).strip()

        enfant.adresse = request.POST.get(
            "adresse",
            ""
        ).strip()

        enfant.groupe_sanguin = request.POST.get(
            "groupe_sanguin",
            ""
        ).strip()

        enfant.allergies = request.POST.get(
            "allergies",
            ""
        ).strip()

        enfant.traitement = request.POST.get(
            "traitement",
            ""
        ).strip()

        enfant.antecedents = request.POST.get(
            "antecedents",
            ""
        ).strip()

        enfant.observations = request.POST.get(
            "observations",
            ""
        ).strip()

        photo = request.FILES.get(
            "photo"
        )

        if photo:
            enfant.photo = photo

        if (
            not enfant.nom
            or not enfant.prenom
            or not enfant.date_naissance
            or not enfant.sexe
        ):

            messages.error(
                request,
                "Veuillez remplir tous les champs obligatoires."
            )

            return render(
                request,
                "sante/modifier_enfant.html",
                {
                    "enfant": enfant
                }
            )

        enfant.save()

        messages.success(
            request,
            "Les informations ont été modifiées."
        )

        return redirect(
            "sante:detail_enfant",
            enfant_id=enfant.id
        )

    return render(
        request,
        "sante/modifier_enfant.html",
        {
            "enfant": enfant
        }
    )


# =========================================================
# CROISSANCE - PARENT
# =========================================================

@login_required
def croissance(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        date_mesure = request.POST.get(
            "date_mesure"
        )

        poids = request.POST.get(
            "poids"
        )

        taille = request.POST.get(
            "taille"
        )

        if not date_mesure or not poids or not taille:

            messages.error(
                request,
                "La date, le poids et la taille sont obligatoires."
            )

        else:

            SuiviCroissance.objects.create(
                enfant=enfant,
                date_mesure=date_mesure,
                poids=poids,
                taille=taille,
                perimetre_cranien=(
                    request.POST.get(
                        "perimetre_cranien"
                    )
                    or None
                ),
                observations=request.POST.get(
                    "observations",
                    ""
                ).strip(),
            )

            messages.success(
                request,
                "La mesure de croissance a été enregistrée."
            )

            return redirect(
                "sante:croissance",
                enfant_id=enfant.id
            )

    croissances = (
        SuiviCroissance.objects
        .filter(enfant=enfant)
        .order_by("-date_mesure")
    )

    return render(
        request,
        "sante/croissance.html",
        {
            "enfant": enfant,
            "croissances": croissances,
        }
    )


# =========================================================
# VACCINATION - PARENT
# =========================================================

@login_required
def vaccination(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    vaccinations = (
        Vaccination.objects
        .filter(enfant=enfant)
        .order_by("date_prevue")
    )

    return render(
        request,
        "sante/vaccination.html",
        {
            "enfant": enfant,
            "vaccinations": vaccinations,
        }
    )


# =========================================================
# AJOUT VACCINATION - PARENT
# =========================================================

@login_required
def ajouter_vaccination(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        form = VaccinationForm(
            request.POST
        )

        if form.is_valid():

            objet = form.save(
                commit=False
            )

            objet.enfant = enfant
            objet.save()

            messages.success(
                request,
                "La vaccination a été enregistrée."
            )

            return redirect(
                "sante:vaccination",
                enfant_id=enfant.id
            )

    else:

        form = VaccinationForm()

    return render(
        request,
        "sante/ajouter_vaccination.html",
        {
            "form": form,
            "enfant": enfant,
        }
    )


# =========================================================
# RENDEZ-VOUS - PARENT
# =========================================================

@login_required
def rendez_vous(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    professionnels = (
        User.objects
        .filter(is_staff=True)
        .order_by(
            "first_name",
            "last_name"
        )
    )

    rendez_vous_list = (
        RendezVous.objects
        .filter(enfant=enfant)
        .select_related("professionnel")
        .order_by(
            "date_rendez_vous",
            "heure"
        )
    )

    return render(
        request,
        "sante/rendez_vous.html",
        {
            "enfant": enfant,
            "professionnels": professionnels,
            "rendez_vous_list": rendez_vous_list,
        }
    )


# =========================================================
# CONSULTATIONS - PARENT
# =========================================================

@login_required
def consultation(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    consultations = (
        Consultation.objects
        .filter(enfant=enfant)
        .order_by("-date_consultation")
    )

    return render(
        request,
        "sante/consultation.html",
        {
            "enfant": enfant,
            "consultations": consultations,
        }
    )


@login_required
def liste_consultations(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    consultations = (
        Consultation.objects
        .filter(enfant=enfant)
        .order_by("-date_consultation")
    )

    return render(
        request,
        "sante/liste_consultations.html",
        {
            "enfant": enfant,
            "consultations": consultations,
        }
    )


@login_required
def ajouter_consultation(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        form = ConsultationForm(
            request.POST
        )

        if form.is_valid():

            objet = form.save(
                commit=False
            )

            objet.enfant = enfant
            objet.save()

            messages.success(
                request,
                "La consultation a été ajoutée."
            )

            return redirect(
                "sante:liste_consultations",
                enfant_id=enfant.id
            )

    else:

        form = ConsultationForm()

    return render(
        request,
        "sante/ajouter_consultation.html",
        {
            "form": form,
            "enfant": enfant,
        }
    )


# =========================================================
# BIEN-ÊTRE - PARENT
# =========================================================

@login_required
def bien_etre(request,enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    suivis = (
        BienEtre.objects
        .filter(enfant=enfant)
        .order_by("-date_suivi")
    )

    return render(
        request,
        "sante/bien_etre.html",
        {
            "enfant": enfant,
            "suivis": suivis,
        }
    )


# =========================================================
# TEMPERATURE - PARENT
# =========================================================

@login_required
def suivi_temperature(request,enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        form = TemperatureForm(
            request.POST
        )

        if form.is_valid():

            objet = form.save(
                commit=False
            )

            objet.enfant = enfant
            objet.save()

            messages.success(
                request,
                "🌡️ Température enregistrée avec succès."
            )

            return redirect(
                "sante:suivi_temperature",
                enfant_id=enfant.id
            )

    else:

        form = TemperatureForm()

    temperatures = (
        Temperature.objects
        .filter(enfant=enfant)
        .order_by("-date_prise")
    )

    return render(
        request,
        "sante/temperature.html",
        {
            "enfant": enfant,
            "form": form,
            "temperatures": temperatures,
        }
    )


@login_required
def supprimer_temperature(request,temperature_id):

    temperature = get_object_or_404(
        Temperature,
        id=temperature_id,
        enfant__parent=request.user
    )

    enfant_id = temperature.enfant.id

    if request.method == "POST":

        temperature.delete()

        messages.success(
            request,
            "Mesure de température supprimée."
        )

    return redirect(
        "sante:suivi_temperature",
        enfant_id=enfant_id
    )


# =========================================================
# TRAITEMENTS - PARENT
# =========================================================

@login_required
def ajouter_traitement(request,enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        form = TraitementForm(
            request.POST
        )

        if form.is_valid():

            objet = form.save(
                commit=False
            )

            objet.enfant = enfant
            objet.prochaine_prise = objet.premiere_prise

            objet.save()

            messages.success(
                request,
                "Traitement ajouté avec succès."
            )

            return redirect(
                "sante:traitements",
                enfant_id=enfant.id
            )

    else:

        form = TraitementForm()

    return render(
        request,
        "sante/ajouter_traitement.html",
        {
            "enfant": enfant,
            "form": form,
        }
    )


@login_required
def traitements(request,enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    liste_traitements = (
        Traitement.objects
        .filter(
            enfant=enfant,
            actif=True
        )
        .order_by("prochaine_prise")
    )

    return render(
        request,
        "sante/traitements.html",
        {
            "enfant": enfant,
            "traitements": liste_traitements,
            "maintenant": timezone.now(),
        }
    )


@login_required
def enregistrer_prise(
    request,
    traitement_id
):

    traitement = get_object_or_404(
        Traitement,
        id=traitement_id,
        enfant__parent=request.user
    )

    maintenant = timezone.now()

    prochaine = traitement.prochaine_prise

    if prochaine and maintenant < prochaine:

        messages.warning(
            request,
            "Cette prise n'est pas encore planifiée."
        )

        return redirect(
            "sante:traitements",
            enfant_id=traitement.enfant.id
        )

    if request.method == "POST":

        PriseTraitement.objects.create(
            traitement=traitement,
            date_heure_prevue=(
                traitement.prochaine_prise
                or maintenant
            ),
            date_heure_prise=maintenant,
            statut="prise",
            observation=request.POST.get(
                "observation",
                ""
            )
        )

        if traitement.intervalle_heures:

            traitement.prochaine_prise = (
                maintenant
                +
                timedelta(
                    hours=traitement.intervalle_heures
                )
            )

            traitement.save(
                update_fields=[
                    "prochaine_prise"
                ]
            )

        else:

            traitement.actif = False

            traitement.save(
                update_fields=[
                    "actif"
                ]
            )

        messages.success(
            request,
            "Prise enregistrée."
        )

    return redirect(
        "sante:traitements",
        enfant_id=traitement.enfant.id
    )


# =========================================================
# PARTAGE PARENT
# =========================================================

@login_required
def inviter_parent(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        email = request.POST.get(
            "email",
            ""
        ).strip()

        if not email:

            messages.error(
                request,
                "Veuillez saisir l'adresse e-mail."
            )

            return redirect(
                "sante:inviter_parent",
                enfant_id=enfant.id
            )

        try:

            parent = User.objects.get(
                email=email
            )

        except User.DoesNotExist:

            messages.error(
                request,
                "Aucun compte ne correspond à cette adresse e-mail."
            )

            return redirect(
                "sante:inviter_parent",
                enfant_id=enfant.id
            )

        if parent == request.user:

            messages.error(
                request,
                "Vous ne pouvez pas vous inviter vous-même."
            )

            return redirect(
                "sante:inviter_parent",
                enfant_id=enfant.id
            )

        partage, created = (
            PartageEnfant.objects
            .get_or_create(
                enfant=enfant,
                parent=parent
            )
        )

        if not created and partage.accepte:

            messages.info(
                request,
                "Ce parent a déjà accès à cet enfant."
            )

        else:

            partage.accepte = False
            partage.save()

            messages.success(
                request,
                f"Invitation envoyée à {parent.email}."
            )

        return redirect(
            "sante:inviter_parent",
            enfant_id=enfant.id
        )

    partages = (
        PartageEnfant.objects
        .filter(enfant=enfant)
        .select_related("parent")
    )

    return render(
        request,
        "sante/inviter_parent.html",
        {
            "enfant": enfant,
            "partages": partages,
        }
    )


@login_required
def accepter_partage(
    request,
    partage_id
):

    partage = get_object_or_404(
        PartageEnfant,
        id=partage_id,
        parent=request.user
    )

    partage.accepte = True
    partage.save()

    messages.success(
        request,
        f"Vous avez maintenant accès au dossier de "
        f"{partage.enfant.prenom}."
    )

    return redirect(
        "sante:tableau_bord_parent"
    )


# =========================================================
# MODE GARDE - CREATION
# =========================================================

@login_required
def creer_mode_garde(
    request,
    enfant_id
):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        form = ModeGardeForm(
            request.POST
        )

        if form.is_valid():

            objet = form.save(
                commit=False
            )

            objet.enfant = enfant
            objet.parent = request.user

            objet.save()

            messages.success(
                request,
                "Mode garde créé avec succès."
            )

            return redirect(
                "sante:mode_garde_detail",
                enfant_id=enfant.id,
                mode_garde_id=objet.id
            )

    else:

        form = ModeGardeForm(
            initial={
                "date_debut": timezone.localdate(),
                "partager_allergies": True,
                "partager_traitement": True,
                "partager_alimentation": True,
                "partager_sommeil": True,
                "partager_contact_parent": True,
            }
        )

    return render(
        request,
        "sante/mode_garde_form.html",
        {
            "enfant": enfant,
            "form": form,
        }
    )


@login_required
def desactiver_mode_garde(
    request,
    enfant_id,
    mode_garde_id
):

    mode_garde = get_object_or_404(
        ModeGarde,
        id=mode_garde_id,
        enfant_id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        mode_garde.actif = False
        mode_garde.save()

        messages.success(
            request,
            "Mode garde désactivé."
        )

    return redirect(
        "sante:detail_enfant",
        enfant_id=enfant_id
    )


# =========================================================
# DETAIL MODE GARDE
# =========================================================

@login_required
def mode_garde_detail(
    request,
    enfant_id,
    mode_garde_id
):

    mode_garde = get_object_or_404(
        ModeGarde,
        id=mode_garde_id,
        enfant_id=enfant_id,
        parent=request.user
    )

    enfant = mode_garde.enfant

    dernier_bien_etre = (
        BienEtre.objects
        .filter(enfant=enfant)
        .order_by("-date_suivi")
        .first()
    )

    vaccinations = (
        Vaccination.objects
        .filter(enfant=enfant)
        .order_by("date_prevue")
        if mode_garde.partager_vaccinations
        else Vaccination.objects.none()
    )

    consultations = (
        Consultation.objects
        .filter(enfant=enfant)
        .order_by("-date_consultation")
        if mode_garde.partager_consultations
        else Consultation.objects.none()
    )

    return render(
        request,
        "sante/mode_garde_detail.html",
        {
            "mode_garde": mode_garde,
            "enfant": enfant,
            "dernier_bien_etre": dernier_bien_etre,
            "vaccinations": vaccinations,
            "consultations": consultations,
        }
    )


# =========================================================
# MODE GARDE PUBLIC
# =========================================================

def consulter_mode_garde(
    request,
    token
):

    mode_garde = get_object_or_404(
        ModeGarde,
        token=token,
        actif=True
    )

    aujourd_hui = timezone.localdate()

    if not (
        mode_garde.date_debut
        <= aujourd_hui
        <= mode_garde.date_fin
    ):

        return render(
            request,
            "sante/mode_garde_expire.html"
        )

    enfant = mode_garde.enfant

    dernier_bien_etre = (
        BienEtre.objects
        .filter(enfant=enfant)
        .order_by("-date_suivi")
        .first()
        if (
            mode_garde.partager_alimentation
            or mode_garde.partager_sommeil
            or mode_garde.partager_hydratation
        )
        else None
    )

    vaccinations = (
        Vaccination.objects
        .filter(enfant=enfant)
        .order_by("date_prevue")
        if mode_garde.partager_vaccinations
        else Vaccination.objects.none()
    )

    consultations = (
        Consultation.objects
        .filter(enfant=enfant)
        .order_by("-date_consultation")
        if mode_garde.partager_consultations
        else Consultation.objects.none()
    )

    temperatures = (
        Temperature.objects
        .filter(enfant=enfant)
        .order_by("-date_prise")[:5]
        if mode_garde.partager_temperature
        else Temperature.objects.none()
    )

    return render(
        request,
        "sante/mode_garde_public.html",
        {
            "mode_garde": mode_garde,
            "enfant": enfant,
            "dernier_bien_etre": dernier_bien_etre,
            "vaccinations": vaccinations,
            "consultations": consultations,
            "temperatures": temperatures,
        }
    )


# =========================================================
# PDF MODE GARDE
# =========================================================

@login_required
def mode_garde_pdf(
    request,
    enfant_id,
    mode_garde_id
):

    mode_garde = get_object_or_404(
        ModeGarde,
        id=mode_garde_id,
        enfant_id=enfant_id,
        parent=request.user
    )

    enfant = mode_garde.enfant

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="mode_garde_'
        f'{enfant.prenom}.pdf"'
    )

    pdf = canvas.Canvas(
        response,
        pagesize=A4
    )

    largeur, hauteur = A4

    y = hauteur - 55

    pdf.setFont(
        "Helvetica-Bold",
        22
    )

    pdf.drawString(
        50,
        y,
        "FICHE DE GARDE"
    )

    y -= 40

    pdf.setFont(
        "Helvetica-Bold",
        16
    )

    pdf.drawString(
        50,
        y,
        f"Enfant : {enfant.prenom} {enfant.nom}"
    )

    y -= 30

    pdf.setFont(
        "Helvetica",
        11
    )

    informations = [
        f"Responsable : {mode_garde.nom_gardien}",
        f"Type : {mode_garde.get_type_gardien_display()}",
        f"Téléphone : {mode_garde.telephone_gardien}",
        (
            f"Valable du "
            f"{mode_garde.date_debut.strftime('%d/%m/%Y')} "
            f"au "
            f"{mode_garde.date_fin.strftime('%d/%m/%Y')}"
        ),
    ]

    for ligne in informations:

        pdf.drawString(
            50,
            y,
            ligne
        )

        y -= 20

    y -= 15

    pdf.setFont(
        "Helvetica-Bold",
        14
    )

    pdf.drawString(
        50,
        y,
        "Informations importantes"
    )

    y -= 25

    pdf.setFont(
        "Helvetica",
        10
    )

    if mode_garde.partager_allergies:

        pdf.drawString(
            50,
            y,
            "Allergies :"
        )

        y -= 17

        pdf.drawString(
            70,
            y,
            enfant.allergies or "Aucune information"
        )

        y -= 25

    if mode_garde.partager_traitement:

        pdf.drawString(
            50,
            y,
            "Traitement :"
        )

        y -= 17

        pdf.drawString(
            70,
            y,
            enfant.traitement or "Aucun traitement indiqué"
        )

        y -= 25

    dernier_bien_etre = (
        BienEtre.objects
        .filter(enfant=enfant)
        .order_by("-date_suivi")
        .first()
    )

    if (
        mode_garde.partager_alimentation
        and dernier_bien_etre
    ):

        pdf.drawString(
            50,
            y,
            "Alimentation :"
        )

        y -= 17

        pdf.drawString(
            70,
            y,
            dernier_bien_etre.alimentation
            or "Aucune information"
        )

        y -= 25

    if (
        mode_garde.partager_sommeil
        and dernier_bien_etre
    ):

        pdf.drawString(
            50,
            y,
            "Sommeil :"
        )

        y -= 17

        pdf.drawString(
            70,
            y,
            dernier_bien_etre.get_sommeil_display()
        )

        y -= 25

    if mode_garde.partager_antecedents:

        pdf.drawString(
            50,
            y,
            "Antécédents :"
        )

        y -= 17

        pdf.drawString(
            70,
            y,
            enfant.antecedents or "Aucune information"
        )

        y -= 25

    if mode_garde.partager_contact_parent:

        pdf.drawString(
            50,
            y,
            f"Parent : "
            f"{enfant.telephone_parent or 'Non renseigné'}"
        )

        y -= 25

    if mode_garde.contact_urgence:

        pdf.setFont(
            "Helvetica-Bold",
            11
        )

        pdf.drawString(
            50,
            y,
            f"Urgence : {mode_garde.contact_urgence}"
        )

        y -= 25

        pdf.setFont(
            "Helvetica",
            10
        )

    if mode_garde.partager_vaccinations:

        pdf.setFont(
            "Helvetica-Bold",
            13
        )

        pdf.drawString(
            50,
            y,
            "Vaccinations"
        )

        y -= 22

        pdf.setFont(
            "Helvetica",
            10
        )

        vaccinations = (
            Vaccination.objects
            .filter(enfant=enfant)
            .order_by("date_prevue")[:8]
        )

        for vaccination in vaccinations:

            texte = (
                f"{vaccination.nom_vaccin} - "
                f"{vaccination.date_prevue.strftime('%d/%m/%Y')}"
            )

            pdf.drawString(
                70,
                y,
                texte
            )

            y -= 17

            if y < 80:

                pdf.showPage()

                y = hauteur - 60

                pdf.setFont(
                    "Helvetica",
                    10
                )

    if mode_garde.partager_consultations:

        pdf.setFont(
            "Helvetica-Bold",
            13
        )

        pdf.drawString(
            50,
            y,
            "Dernières consultations"
        )

        y -= 22

        pdf.setFont(
            "Helvetica",
            10
        )

        consultations = (
            Consultation.objects
            .filter(enfant=enfant)
            .order_by("-date_consultation")[:5]
        )

        for consultation in consultations:

            texte = (
                f"{consultation.date_consultation:%d/%m/%Y} - "
                f"{consultation.motif[:80]}"
            )

            pdf.drawString(
                70,
                y,
                texte
            )

            y -= 17

    if mode_garde.consignes:

        pdf.setFont(
            "Helvetica-Bold",
            13
        )

        pdf.drawString(
            50,
            y,
            "Consignes particulières"
        )

        y -= 22

        pdf.setFont(
            "Helvetica",
            10
        )

        mots = mode_garde.consignes.split()

        ligne = ""

        for mot in mots:

            if len(ligne) + len(mot) > 90:

                pdf.drawString(
                    60,
                    y,
                    ligne
                )

                y -= 17

                ligne = ""

                if y < 70:

                    pdf.showPage()

                    y = hauteur - 60

                    pdf.setFont(
                        "Helvetica",
                        10
                    )

            ligne += mot + " "

        if ligne:

            pdf.drawString(
                60,
                y,
                ligne
            )

    pdf.setFont(
        "Helvetica-Oblique",
        8
    )

    pdf.drawString(
        50,
        35,
        "Document généré par TOUKPEDIO"
    )

    pdf.showPage()
    pdf.save()

    return response


# =========================================================
# IMAGE MODE GARDE
# =========================================================

@login_required
def mode_garde_image(
    request,
    enfant_id,
    mode_garde_id
):

    mode_garde = get_object_or_404(
        ModeGarde,
        id=mode_garde_id,
        enfant_id=enfant_id,
        parent=request.user
    )

    enfant = mode_garde.enfant

    largeur = 1200
    hauteur = 1600

    image = Image.new(
        "RGB",
        (largeur, hauteur),
        "white"
    )

    draw = ImageDraw.Draw(
        image
    )

    try:

        font_titre = ImageFont.truetype(
            "arial.ttf",
            55
        )

        font_sous_titre = ImageFont.truetype(
            "arial.ttf",
            38
        )

        font = ImageFont.truetype(
            "arial.ttf",
            30
        )

    except:

        font_titre = ImageFont.load_default()
        font_sous_titre = ImageFont.load_default()
        font = ImageFont.load_default()

    y = 70

    draw.text(
        (60, y),
        "FICHE DE GARDE",
        font=font_titre,
        fill="black"
    )

    y += 100

    draw.text(
        (60, y),
        f"{enfant.prenom} {enfant.nom}",
        font=font_sous_titre,
        fill="black"
    )

    y += 70

    draw.text(
        (60, y),
        f"Gardien : {mode_garde.nom_gardien}",
        font=font,
        fill="black"
    )

    y += 50

    draw.text(
        (60, y),
        f"Téléphone : {mode_garde.telephone_gardien}",
        font=font,
        fill="black"
    )

    y += 50

    draw.text(
        (60, y),
        (
            f"Valable du "
            f"{mode_garde.date_debut.strftime('%d/%m/%Y')} "
            f"au "
            f"{mode_garde.date_fin.strftime('%d/%m/%Y')}"
        ),
        font=font,
        fill="black"
    )

    y += 90

    if mode_garde.partager_allergies:

        draw.text(
            (60, y),
            "Allergies :",
            font=font_sous_titre,
            fill="black"
        )

        y += 50

        draw.text(
            (80, y),
            enfant.allergies or "Aucune information",
            font=font,
            fill="black"
        )

        y += 70

    if mode_garde.partager_traitement:

        draw.text(
            (60, y),
            "Traitement :",
            font=font_sous_titre,
            fill="black"
        )

        y += 50

        draw.text(
            (80, y),
            enfant.traitement or "Aucun traitement",
            font=font,
            fill="black"
        )

        y += 70

    if mode_garde.partager_antecedents:

        draw.text(
            (60, y),
            "Antécédents :",
            font=font_sous_titre,
            fill="black"
        )

        y += 50

        draw.text(
            (80, y),
            enfant.antecedents or "Aucune information",
            font=font,
            fill="black"
        )

        y += 70

    if mode_garde.partager_contact_parent:

        draw.text(
            (60, y),
            (
                f"Parent : "
                f"{enfant.telephone_parent or 'Non renseigné'}"
            ),
            font=font,
            fill="black"
        )

        y += 60

    if mode_garde.contact_urgence:

        draw.text(
            (60, y),
            (
                f"Urgence : "
                f"{mode_garde.contact_urgence}"
            ),
            font=font,
            fill="black"
        )

        y += 70

    if mode_garde.consignes:

        draw.text(
            (60, y),
            "Consignes :",
            font=font_sous_titre,
            fill="black"
        )

        y += 55

        mots = mode_garde.consignes.split()

        ligne = ""

        for mot in mots:

            if len(ligne) > 55:

                draw.text(
                    (80, y),
                    ligne,
                    font=font,
                    fill="black"
                )

                y += 45

                ligne = ""

            ligne += mot + " "

        if ligne:

            draw.text(
                (80, y),
                ligne,
                font=font,
                fill="black"
            )

    draw.text(
        (60, hauteur - 80),
        "TOUKPEDIO",
        font=font,
        fill="black"
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="image/png"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="mode_garde_'
        f'{enfant.prenom}.png"'
    )

    return response


# =========================================================
# WHATSAPP MODE GARDE
# =========================================================

@login_required
def mode_garde_whatsapp(
    request,
    enfant_id,
    mode_garde_id
):

    mode_garde = get_object_or_404(
        ModeGarde,
        id=mode_garde_id,
        enfant_id=enfant_id,
        parent=request.user
    )

    lien = request.build_absolute_uri(
        reverse(
            "sante:consulter_mode_garde",
            kwargs={
                "token": mode_garde.token
            }
        )
    )

    message = (
        f"Bonjour {mode_garde.nom_gardien},\n\n"
        f"Voici la fiche de garde de "
        f"{mode_garde.enfant.prenom}.\n\n"
        f"Elle est valable du "
        f"{mode_garde.date_debut.strftime('%d/%m/%Y')} "
        f"au "
        f"{mode_garde.date_fin.strftime('%d/%m/%Y')}.\n\n"
        f"Consulter la fiche :\n"
        f"{lien}\n\n"
        f"TOUKPEDIO"
    )

    telephone = (
        mode_garde.telephone_gardien
        .replace(" ", "")
        .replace("-", "")
        .replace("+", "")
    )

    return redirect(
        f"https://wa.me/{telephone}"
        f"?text={quote(message)}"
    )


# =========================================================
# SMS MODE GARDE
# =========================================================

@login_required
def mode_garde_sms(
    request,
    enfant_id,
    mode_garde_id
):

    mode_garde = get_object_or_404(
        ModeGarde,
        id=mode_garde_id,
        enfant_id=enfant_id,
        parent=request.user
    )

    lien = request.build_absolute_uri(
        reverse(
            "sante:consulter_mode_garde",
            kwargs={
                "token": mode_garde.token
            }
        )
    )

    message = (
        f"Fiche de garde de "
        f"{mode_garde.enfant.prenom}. "
        f"Valable du "
        f"{mode_garde.date_debut.strftime('%d/%m/%Y')} "
        f"au "
        f"{mode_garde.date_fin.strftime('%d/%m/%Y')}. "
        f"Consulter : {lien}"
    )

    telephone = (
        mode_garde.telephone_gardien
        .replace(" ", "")
        .replace("-", "")
    )

    return redirect(
        f"sms:{telephone}?body={quote(message)}"
    )
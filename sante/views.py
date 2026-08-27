from datetime import date

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from .forms import JournalSymptomeForm, PhotoSymptomeForm
from datetime import date, timedelta
from .forms import (
    JournalSymptomeForm,
    PhotoSymptomeForm,
    TraitementForm,
    PriseTraitementForm,
)


from .models import (
    Enfant,
    Consultation,
    JournalSymptome,
    Parent,
    PriseTraitement,
    Temperature,
    Traitement,
    Vaccination,
    SuiviCroissance,
    BienEtre,
    RendezVous,
)

from .forms import (
    ConsultationForm,
    TemperatureForm,
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

            # Administrateur
            if user.is_staff or user.is_superuser:

                return redirect(
                    "sante:tableau_bord_admin"
                )

            # Parent
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
# INSCRIPTION PARENT
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

        # -------------------------------------------------
        # VERIFICATION DES CHAMPS
        # -------------------------------------------------

        if not username or not email or not password:

            messages.error(
                request,
                "Veuillez remplir tous les champs obligatoires."
            )

            return render(
                request,
                "sante/inscription.html"
            )

        # -------------------------------------------------
        # VERIFICATION USERNAME
        # -------------------------------------------------

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

        # -------------------------------------------------
        # VERIFICATION EMAIL
        # -------------------------------------------------

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

        # -------------------------------------------------
        # CREATION DU COMPTE DJANGO
        # -------------------------------------------------

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # -------------------------------------------------
        # CREATION DU PROFIL PARENT
        # -------------------------------------------------

        Parent.objects.create(
            user=user,
            telephone=telephone,
            adresse=adresse
        )

        # -------------------------------------------------
        # CONNEXION AUTOMATIQUE
        # -------------------------------------------------

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
        .order_by(
            "nom",
            "prenom"
        )
    )

    nombre_enfants = enfants.count()

    nombre_consultations = (
        Consultation.objects
        .filter(
            enfant__parent=request.user
        )
        .count()
    )

    nombre_vaccinations = (
        Vaccination.objects
        .filter(
            enfant__parent=request.user
        )
        .count()
    )

    nombre_rendez_vous = (
        RendezVous.objects
        .filter(
            enfant__parent=request.user
        )
        .count()
    )

    aujourd_hui = timezone.localdate()

    # -----------------------------------------------------
    # RENDEZ-VOUS A VENIR
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # VACCINATIONS A VENIR
    # -----------------------------------------------------

    vaccinations_a_venir = (
        Vaccination.objects
        .filter(
            enfant__parent=request.user,
            date_prevue__gte=aujourd_hui,
            date_effectuee__isnull=True
        )
        .select_related(
            "enfant"
        )
        .order_by(
            "date_prevue"
        )[:5]
    )

    # -----------------------------------------------------
    # DERNIERES CONSULTATIONS
    # -----------------------------------------------------

    dernieres_consultations = (
        Consultation.objects
        .filter(
            enfant__parent=request.user
        )
        .select_related(
            "enfant"
        )
        .order_by(
            "-date_consultation"
        )[:5]
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
# TABLEAU DE BORD ADMINISTRATEUR
# =========================================================

@staff_member_required(login_url="sante:connexion_admin")
def tableau_bord_admin(request):

    nombre_parents = (
        User.objects
        .filter(
            is_staff=False,
            is_superuser=False
        )
        .count()
    )

    nombre_enfants = Enfant.objects.count()

    nombre_consultations = Consultation.objects.count()

    nombre_vaccinations = Vaccination.objects.count()

    nombre_rendez_vous = RendezVous.objects.count()

    enfants_recents = (
        Enfant.objects
        .select_related("parent")
        .order_by(
            "-date_creation"
        )[:5]
    )

    rendez_vous_recents = (
        RendezVous.objects
        .select_related(
            "enfant",
            "professionnel"
        )
        .order_by(
            "-date_creation"
        )[:5]
    )

    context = {
        "nombre_parents": nombre_parents,
        "nombre_enfants": nombre_enfants,
        "nombre_consultations": nombre_consultations,
        "nombre_vaccinations": nombre_vaccinations,
        "nombre_rendez_vous": nombre_rendez_vous,
        "enfants_recents": enfants_recents,
        "rendez_vous_recents": rendez_vous_recents,
    }

    return render(
        request,
        "sante/tableau_bord_admin.html",
        context
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
        .filter(
            parent=request.user
        )
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
# AJOUTER UN ENFANT
# =========================================================
from .models import Enfant, JournalSymptome, PhotoSymptome

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

        photo = request.FILES.get(
            "photo"
        )

        telephone_parent = request.POST.get(
            "telephone_parent",
            ""
        ).strip()

        adresse = request.POST.get(
            "adresse",
            ""
        ).strip()

        groupe_sanguin = request.POST.get(
            "groupe_sanguin",
            ""
        ).strip()

        allergies = request.POST.get(
            "allergies",
            ""
        ).strip()

        traitement = request.POST.get(
            "traitement",
            ""
        ).strip()

        antecedents = request.POST.get(
            "antecedents",
            ""
        ).strip()

        observations = request.POST.get(
            "observations",
            ""
        ).strip()

        # -------------------------------------------------
        # VERIFICATION
        # -------------------------------------------------

        if (
            not nom
            or not prenom
            or not date_naissance
            or not sexe
        ):

            messages.error(
                request,
                "Veuillez remplir tous les champs obligatoires."
            )

            return render(
                request,
                "sante/ajouter_enfant.html"
            )

        # -------------------------------------------------
        # CREATION
        # -------------------------------------------------

        Enfant.objects.create(
            nom=nom,
            prenom=prenom,
            date_naissance=date_naissance,
            sexe=sexe,
            photo=photo,
            parent=request.user,
            telephone_parent=telephone_parent,
            adresse=adresse,
            groupe_sanguin=groupe_sanguin,
            allergies=allergies,
            traitement=traitement,
            antecedents=antecedents,
            observations=observations,
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
# AJOUTER UN SYMPTOME
# =========================================================

@login_required
def ajouter_symptome(request, enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        form = JournalSymptomeForm(
            request.POST
        )

        photo_form = PhotoSymptomeForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            journal = form.save(
                commit=False
            )

            journal.enfant = enfant

            journal.save()

            # =========================
            # ENREGISTREMENT DE LA PHOTO
            # =========================

            if (
                request.FILES.get("photo")
            ):

                photo = PhotoSymptome.objects.create(

                    journal=journal,

                    photo=request.FILES["photo"],

                    description=request.POST.get(
                        "photo_description",
                        ""
                    )
                )

            return redirect(
                "sante:dossier_enfant",
                enfant_id=enfant.id
            )

    else:

        form = JournalSymptomeForm()

        photo_form = PhotoSymptomeForm()


    return render(
        request,
        "sante/ajouter_symptome.html",
        {
            "enfant": enfant,
            "form": form,
            "photo_form": photo_form,
        }
    )


# =========================================================
# MODIFIER UN SYMPTOME
# =========================================================

@login_required
def modifier_symptome(request, symptome_id):

    suivi = get_object_or_404(
        JournalSymptome,
        id=symptome_id,
        enfant__parent=request.user
    )

    if request.method == "POST":

        suivi.symptome = request.POST.get(
            "symptome"
        )

        suivi.intensite = request.POST.get(
            "intensite"
        )

        suivi.date = request.POST.get(
            "date"
        )

        suivi.description = request.POST.get(
            "description"
        )

        temperature = request.POST.get(
            "temperature"
        )

        suivi.temperature = (
            temperature
            if temperature
            else None
        )

        suivi.traitement_pris = request.POST.get(
            "traitement_pris"
        )

        suivi.evolution = request.POST.get(
            "evolution"
        )

        suivi.observations = request.POST.get(
            "observations"
        )

        suivi.save()

        messages.success(
            request,
            "Le suivi a été modifié avec succès."
        )

        return redirect(
            "sante:dossier_enfant",
            enfant_id=suivi.enfant.id
        )

    return render(
        request,
        "sante/modifier_symptome.html",
        {
            "suivi": suivi,
            "enfant": suivi.enfant,
        }
    )


# =========================================================
# SUPPRIMER UN SYMPTOME
# =========================================================

@login_required
def supprimer_symptome(request, symptome_id):

    suivi = get_object_or_404(
        JournalSymptome,
        id=symptome_id,
        enfant__parent=request.user
    )

    enfant_id = suivi.enfant.id

    if request.method == "POST":

        suivi.delete()

        messages.success(
            request,
            "Le suivi a été supprimé."
        )

        return redirect(
            "sante:dossier_enfant",
            enfant_id=enfant_id
        )

    return render(
        request,
        "sante/confirmer_suppression_symptome.html",
        {
            "suivi": suivi
        }
    )


# =========================================================
# DOSSIER D'UN ENFANT
# =========================================================

@login_required
def dossier_enfant(request, enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    suivis = (
        enfant.journaux_symptomes
        .all()
        .order_by(
            "-date",
            "-created_at"
        )
    )

    date_debut = request.GET.get(
        "date_debut"
    )

    date_fin = request.GET.get(
        "date_fin"
    )

    if date_debut:

        suivis = suivis.filter(
            date__gte=date_debut
        )

    if date_fin:

        suivis = suivis.filter(
            date__lte=date_fin
        )

    return render(
        request,
        "sante/dossier_enfant.html",
        {
            "enfant": enfant,
            "suivis": suivis,
            "date_debut": date_debut,
            "date_fin": date_fin,
        }
    )


# =========================================================
# DETAIL D'UN ENFANT
# =========================================================

@login_required
def detail_enfant(request, enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    consultations = (
        Consultation.objects
        .filter(enfant=enfant)
        .order_by(
            "-date_consultation"
        )[:5]
    )

    vaccinations = (
        Vaccination.objects
        .filter(enfant=enfant)
        .order_by(
            "-date_prevue"
        )[:5]
    )

    croissances = (
        SuiviCroissance.objects
        .filter(enfant=enfant)
        .order_by(
            "-date_mesure"
        )[:5]
    )

    suivis_bien_etre = (
        BienEtre.objects
        .filter(enfant=enfant)
        .order_by(
            "-date_suivi"
        )[:5]
    )

    rendez_vous = (
        RendezVous.objects
        .filter(enfant=enfant)
        .select_related(
            "professionnel"
        )
        .order_by(
            "date_rendez_vous",
            "heure"
        )[:5]
    )

    return render(
        request,
        "sante/detail_enfant.html",
        {
            "enfant": enfant,
            "consultations": consultations,
            "vaccinations": vaccinations,
            "croissances": croissances,
            "suivis_bien_etre": suivis_bien_etre,
            "rendez_vous": rendez_vous,
        }
    )


# =========================================================
# MODIFIER UN ENFANT
# =========================================================

@login_required
def modifier_enfant(request, pk):

    enfant = get_object_or_404(
        Enfant,
        pk=pk,
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
            f"Les informations de {enfant.prenom} "
            f"{enfant.nom} ont été modifiées avec succès."
        )

        return redirect(
            "sante:detail_enfant",
            pk=enfant.id
        )

    return render(
        request,
        "sante/modifier_enfant.html",
        {
            "enfant": enfant
        }
    )


# =========================================================
# SUIVI DE CROISSANCE
# =========================================================

@login_required
def croissance(request, enfant_id):

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

        perimetre_cranien = request.POST.get(
            "perimetre_cranien"
        )

        observations = request.POST.get(
            "observations",
            ""
        ).strip()

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
                    perimetre_cranien
                    if perimetre_cranien
                    else None
                ),
                observations=observations,
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
        .order_by(
            "-date_mesure"
        )
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
# VACCINATIONS
# =========================================================

@login_required
def vaccination(request, enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        nom_vaccin = request.POST.get(
            "nom_vaccin",
            ""
        ).strip()

        dose = request.POST.get(
            "dose",
            ""
        ).strip()

        date_prevue = request.POST.get(
            "date_prevue"
        )

        date_effectuee = request.POST.get(
            "date_effectuee"
        )

        prochaine_dose = request.POST.get(
            "prochaine_dose"
        )

        observations = request.POST.get(
            "observations",
            ""
        ).strip()

        if not nom_vaccin or not date_prevue:

            messages.error(
                request,
                "Le nom du vaccin et la date prévue sont obligatoires."
            )

        else:

            Vaccination.objects.create(
                enfant=enfant,
                nom_vaccin=nom_vaccin,
                dose=dose,
                date_prevue=date_prevue,
                date_effectuee=(
                    date_effectuee
                    if date_effectuee
                    else None
                ),
                prochaine_dose=(
                    prochaine_dose
                    if prochaine_dose
                    else None
                ),
                observations=observations,
            )

            messages.success(
                request,
                "La vaccination a été enregistrée."
            )

            return redirect(
                "sante:vaccination",
                enfant_id=enfant.id
            )

    vaccinations = (
        Vaccination.objects
        .filter(enfant=enfant)
        .order_by(
            "date_prevue"
        )
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
# RENDEZ-VOUS
# =========================================================

@login_required
def rendez_vous(request, enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        date_rendez_vous = request.POST.get(
            "date_rendez_vous"
        )

        heure = request.POST.get(
            "heure"
        )

        motif = request.POST.get(
            "motif",
            ""
        ).strip()

        professionnel_id = request.POST.get(
            "professionnel"
        )

        notes = request.POST.get(
            "notes",
            ""
        ).strip()

        if (
            not date_rendez_vous
            or not heure
            or not motif
        ):

            messages.error(
                request,
                "La date, l'heure et le motif sont obligatoires."
            )

        else:

            professionnel = None

            if professionnel_id:

                professionnel = get_object_or_404(
                    User,
                    id=professionnel_id,
                    is_staff=True
                )

            RendezVous.objects.create(
                enfant=enfant,
                date_rendez_vous=date_rendez_vous,
                heure=heure,
                motif=motif,
                professionnel=professionnel,
                notes=notes,
            )

            messages.success(
                request,
                "Le rendez-vous a été enregistré."
            )

            return redirect(
                "sante:rendez_vous",
                enfant_id=enfant.id
            )

    professionnels = (
        User.objects
        .filter(
            is_staff=True
        )
        .order_by(
            "first_name",
            "last_name"
        )
    )

    rendez_vous_list = (
        RendezVous.objects
        .filter(enfant=enfant)
        .select_related(
            "professionnel"
        )
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
# CONSULTATIONS
# =========================================================

@login_required
def consultation(request, enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    consultations = (
        Consultation.objects
        .filter(enfant=enfant)
        .order_by(
            "-date_consultation"
        )
    )

    return render(
        request,
        "sante/consultation.html",
        {
            "enfant": enfant,
            "consultations": consultations,
        }
    )


# =========================================================
# LISTE DES CONSULTATIONS
# =========================================================

@login_required
def liste_consultations(request, enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    consultations = (
        Consultation.objects
        .filter(enfant=enfant)
        .order_by(
            "-date_consultation"
        )
    )

    return render(
        request,
        "sante/liste_consultations.html",
        {
            "enfant": enfant,
            "consultations": consultations,
        }
    )


# =========================================================
# AJOUTER UNE CONSULTATION
# =========================================================

@login_required
def ajouter_consultation(request, enfant_id):

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

            consultation = form.save(
                commit=False
            )

            consultation.enfant = enfant

            consultation.save()

            messages.success(
                request,
                "La consultation a été ajoutée avec succès."
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
# BIEN-ÊTRE
# =========================================================

@login_required
def bien_etre(request, enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        date_suivi = request.POST.get(
            "date_suivi"
        )

        humeur = request.POST.get(
            "humeur"
        )

        sommeil = request.POST.get(
            "sommeil"
        )

        alimentation = request.POST.get(
            "alimentation",
            ""
        ).strip()

        hydratation = request.POST.get(
            "hydratation",
            ""
        ).strip()

        activite_physique = request.POST.get(
            "activite_physique",
            ""
        ).strip()

        hygiene = request.POST.get(
            "hygiene",
            ""
        ).strip()

        temps_ecran = request.POST.get(
            "temps_ecran",
            0
        )

        observations = request.POST.get(
            "observations",
            ""
        ).strip()

        if (
            not date_suivi
            or not humeur
            or not sommeil
        ):

            messages.error(
                request,
                "La date, l'humeur et le sommeil sont obligatoires."
            )

        else:

            try:

                temps_ecran = int(
                    temps_ecran
                )

            except (
                TypeError,
                ValueError
            ):

                temps_ecran = 0

            BienEtre.objects.create(
                enfant=enfant,
                date_suivi=date_suivi,
                humeur=humeur,
                sommeil=sommeil,
                alimentation=alimentation,
                hydratation=hydratation,
                activite_physique=activite_physique,
                hygiene=hygiene,
                temps_ecran=temps_ecran,
                observations=observations,
            )

            messages.success(
                request,
                "Le suivi du bien-être a été enregistré."
            )

            return redirect(
                "sante:bien_etre",
                enfant_id=enfant.id
            )

    suivis = (
        BienEtre.objects
        .filter(enfant=enfant)
        .order_by(
            "-date_suivi"
        )
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
# SUIVI TEMPERATURE
# =========================================================

@login_required
def suivi_temperature(request, enfant_id):

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

            temperature = form.save(
                commit=False
            )

            temperature.enfant = enfant

            temperature.save()

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
        .order_by(
            "-date_prise"
        )
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


# =========================================================
# SUPPRIMER UNE TEMPERATURE
# =========================================================

@login_required
def supprimer_temperature(request, temperature_id):

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
      
    
@login_required
def ajouter_traitement(request, enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        form = TraitementForm(request.POST)

        if form.is_valid():

            traitement = form.save(
                commit=False
            )

            traitement.enfant = enfant

            traitement.prochaine_prise = (
                traitement.premiere_prise
            )

            traitement.save()

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
def traitements(request, enfant_id):

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

    maintenant = timezone.now()

    return render(
        request,
        "sante/traitements.html",
        {
            "enfant": enfant,
            "traitements": liste_traitements,
            "maintenant": maintenant,
        }
    )
    
@login_required
def enregistrer_prise(request, traitement_id):

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


        # =====================================
        # CALCUL DE LA PROCHAINE PRISE
        # =====================================

        if traitement.intervalle_heures:

            traitement.prochaine_prise = (
                maintenant +

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
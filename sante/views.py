from datetime import date
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
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
    PartageEnfant,
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
    
def logout_view(request):
    logout(request)
    return redirect("sante:connexion")


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

        # ==========================================
        # FORMULAIRE DU JOURNAL
        # ==========================================

        form = JournalSymptomeForm(request.POST)

        if form.is_valid():

            # Création du journal sans enregistrer immédiatement
            journal = form.save(commit=False)

            # Association à l'enfant
            journal.enfant = enfant

            # Date automatique
            journal.date = timezone.localdate()

            # Enregistrement du symptôme
            journal.save()

            # ==========================================
            # PHOTO
            # ==========================================

            fichier_photo = request.FILES.get("photo")

            description_photo = request.POST.get(
                "photo_description",
                ""
            ).strip()

            # Si une photo a été sélectionnée
            if fichier_photo:

                PhotoSymptome.objects.create(
                    journal=journal,
                    photo=fichier_photo,
                    description=description_photo
                )

            # ==========================================
            # REDIRECTION
            # ==========================================

            return redirect(
                "sante:detail_enfant",
                enfant_id=enfant.id
            )

    else:

        form = JournalSymptomeForm()

    # ==========================================
    # AFFICHAGE
    # ==========================================

    return render(
        request,
        "sante/ajouter_symptome.html",
        {
            "enfant": enfant,
            "form": form,
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
        id=enfant_id
    )

    acces_principal = (
        enfant.parent == request.user
    )

    acces_partage = PartageEnfant.objects.filter(
        enfant=enfant,
        parent=request.user,
        accepte=True
    ).exists()

    if not acces_principal and not acces_partage:
        messages.error(
            request,
            "Vous n'avez pas accès à ce dossier."
        )
        return redirect("sante:tableau_bord_parent")

    return render(
        request,
        "sante/detail_enfant.html",
        {
            "enfant": enfant
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

@login_required
def inviter_parent(request, enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        email = request.POST.get("email", "").strip()

        if not email:
            messages.error(
                request,
                "Veuillez saisir l'adresse e-mail du parent."
            )
            return redirect(
                "sante:inviter_parent",
                enfant_id=enfant.id
            )

        try:
            parent = User.objects.get(email=email)
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

        partage, created = PartageEnfant.objects.get_or_create(
            enfant=enfant,
            parent=parent
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

    partages = PartageEnfant.objects.filter(
        enfant=enfant
    ).select_related("parent")

    return render(
        request,
        "sante/inviter_parent.html",
        {
            "enfant": enfant,
            "partages": partages,
        }
    )
    
@login_required
def accepter_partage(request, partage_id):

    partage = get_object_or_404(
        PartageEnfant,
        id=partage_id,
        parent=request.user
    )

    partage.accepte = True
    partage.save()

    messages.success(
        request,
        f"Vous avez maintenant accès au dossier de {partage.enfant.prenom}."
    )

    return redirect("sante:tableau_bord_parent")

# =========================================================
# MODE GARDE
# =========================================================

from io import BytesIO
from urllib.parse import quote

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.urls import reverse

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from PIL import Image, ImageDraw, ImageFont

from .models import (
    Enfant,
    ModeGarde,
    BienEtre,
    Vaccination,
    Consultation,
)

from .forms import ModeGardeForm

# =========================================================
# CREER UN MODE GARDE
# =========================================================

@login_required
def creer_mode_garde(request, enfant_id):

    enfant = get_object_or_404(
        Enfant,
        id=enfant_id,
        parent=request.user
    )

    if request.method == "POST":

        form = ModeGardeForm(request.POST)

        if form.is_valid():

            mode_garde = form.save(
                commit=False
            )

            mode_garde.enfant = enfant
            mode_garde.parent = request.user

            mode_garde.save()

            messages.success(
                request,
                f"Le mode garde de {enfant.prenom} "
                f"a été créé avec succès."
            )

            return redirect(
                "sante:mode_garde_detail",
                enfant_id=enfant.id,
                mode_garde_id=mode_garde.id
            )

    else:

        form = ModeGardeForm(
            initial={
                "date_debut": timezone.localdate(),

                "partager_allergies": True,
                "partager_traitement": True,
                "partager_alimentation": True,
                "partager_sommeil": True,

                "partager_antecedents": False,
                "partager_vaccinations": False,
                "partager_consultations": False,

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

    mode_garde.actif = False
    mode_garde.save()

    return redirect(
        "sante:detail_enfant",
        enfant_id=enfant_id
    )
    
# =========================================================
# CONSULTATION PUBLIQUE DU MODE GARDE
# =========================================================

def consulter_mode_garde(request, token):

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
    )

    vaccinations = (
        Vaccination.objects
        .filter(enfant=enfant)
        .order_by("date_prevue")
    )

    consultations = (
        Consultation.objects
        .filter(enfant=enfant)
        .order_by("-date_consultation")
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
        }
    )
    # =========================================================
# DETAIL DU MODE GARDE
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

    # -----------------------------------------------------
    # DERNIER SUIVI DU BIEN-ÊTRE
    # -----------------------------------------------------

    dernier_bien_etre = (
        BienEtre.objects
        .filter(enfant=enfant)
        .order_by("-date_suivi")
        .first()
    )

    # -----------------------------------------------------
    # VACCINATIONS
    # -----------------------------------------------------

    vaccinations = (
        Vaccination.objects
        .filter(enfant=enfant)
        .order_by("date_prevue")
    )

    # -----------------------------------------------------
    # CONSULTATIONS
    # -----------------------------------------------------

    consultations = (
        Consultation.objects
        .filter(enfant=enfant)
        .order_by("-date_consultation")
    )

    # -----------------------------------------------------
    # CONTEXTE
    # -----------------------------------------------------

    context = {
        "mode_garde": mode_garde,
        "enfant": enfant,
        "dernier_bien_etre": dernier_bien_etre,
        "vaccinations": vaccinations,
        "consultations": consultations,
    }

    return render(
        request,
        "sante/mode_garde_detail.html",
        context
    )
    
# =========================================================
# GENERER PDF MODE GARDE
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

    # -----------------------------------------------------
    # TITRE
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # INFORMATIONS GARDIEN
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # INFORMATIONS IMPORTANTES
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # ALLERGIES
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # TRAITEMENT
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # ALIMENTATION
    # -----------------------------------------------------

    if mode_garde.partager_alimentation:

        dernier_bien_etre = (
            BienEtre.objects
            .filter(enfant=enfant)
            .order_by("-date_suivi")
            .first()
        )

        pdf.drawString(
            50,
            y,
            "Alimentation :"
        )

        y -= 17

        alimentation = (
            dernier_bien_etre.alimentation
            if dernier_bien_etre
            and dernier_bien_etre.alimentation
            else "Aucune information"
        )

        pdf.drawString(
            70,
            y,
            alimentation[:100]
        )

        y -= 25

    # -----------------------------------------------------
    # SOMMEIL
    # -----------------------------------------------------

    if mode_garde.partager_sommeil:

        dernier_bien_etre = (
            BienEtre.objects
            .filter(enfant=enfant)
            .order_by("-date_suivi")
            .first()
        )

        pdf.drawString(
            50,
            y,
            "Sommeil :"
        )

        y -= 17

        sommeil = (
            dernier_bien_etre.get_sommeil_display()
            if dernier_bien_etre
            else "Aucune information"
        )

        pdf.drawString(
            70,
            y,
            sommeil
        )

        y -= 25

    # -----------------------------------------------------
    # ANTECEDENTS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CONTACT PARENT
    # -----------------------------------------------------

    if mode_garde.partager_contact_parent:

        pdf.drawString(
            50,
            y,
            f"Parent : "
            f"{enfant.telephone_parent or 'Non renseigné'}"
        )

        y -= 25

    # -----------------------------------------------------
    # CONTACT URGENCE
    # -----------------------------------------------------

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

        pdf.setFont(
            "Helvetica",
            10
        )

        y -= 25

    # -----------------------------------------------------
    # VACCINATIONS
    # -----------------------------------------------------

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

        y -= 10

    # -----------------------------------------------------
    # CONSULTATIONS
    # -----------------------------------------------------

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

            date_consultation = (
                consultation.date_consultation
                .strftime("%d/%m/%Y")
            )

            texte = (
                f"{date_consultation} - "
                f"{consultation.motif[:80]}"
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

        y -= 10

    # -----------------------------------------------------
    # CONSIGNES
    # -----------------------------------------------------

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

            y -= 25

    # -----------------------------------------------------
    # PIED DE PAGE
    # -----------------------------------------------------

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

    largeur = 1200
    hauteur = 1600

    image = Image.new(
        "RGB",
        (largeur, hauteur),
        "white"
    )

    draw = ImageDraw.Draw(image)

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

    enfant = mode_garde.enfant

    draw.text(
        (60, y),
        f"👧 {enfant.prenom}",
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
            "⚠ Allergies :",
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
            "💊 Traitement :",
            font=font_sous_titre,
            fill="black"
        )

        y += 50

        draw.text(
            (80, y),
            enfant.traitement or "Aucun traitement indiqué",
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

    y = hauteur - 80

    draw.text(
        (60, y),
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

    response[
        "Content-Disposition"
    ] = (
        f'attachment; filename="mode_garde_'
        f'{enfant.prenom}.png"'
    )

    return response

# =========================================================
# WHATSAPP
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

    whatsapp_url = (
        f"https://wa.me/{telephone}"
        f"?text={quote(message)}"
    )

    return redirect(
        whatsapp_url
    )
    
# =========================================================
# SMS
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
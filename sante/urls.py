from django.urls import path
from . import views

app_name = "sante"

urlpatterns = [

    # =============================
    # ACCUEIL
    # =============================

    path(
        "",
        views.accueil,
        name="accueil"
    ),
    

    # =============================
    # CONNEXION
    # =============================

    path(
        "connexion/",
        views.connexion,
        name="connexion"
    ),
    
    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),

    path(
        "inscription/",
        views.inscription,
        name="inscription"
    ),

    # =============================
    # TABLEAU DE BORD PARENT
    # =============================

    path(
        "tableau_bord_parent/",
        views.tableau_bord_parent,
        name="tableau_bord_parent"
    ),

    # =============================
    # ADMIN
    # =============================

    path(
        "connexion-admin/",
        views.connexion_admin,
        name="connexion_admin"
    ),

    path(
        "tableau-de-bord/admin/",
        views.tableau_bord_admin,
        name="tableau_bord_admin"
    ),

    # =============================
    # ENFANTS
    # =============================

    path(
        "enfants/",
        views.enfant,
        name="enfant"
    ),

    path(
        "enfants/ajouter/",
        views.ajouter_enfant,
        name="ajouter_enfant"
    ),
    
    path(
    "enfant/<int:enfant_id>/symptome/ajouter/",
    views.ajouter_symptome,
    name="ajouter_symptome"
    ),
    
    
    path(
    "symptome/<int:symptome_id>/modifier/",
    views.modifier_symptome,
    name="modifier_symptome"
    ),

    path(
    "symptome/<int:symptome_id>/supprimer/",
    views.supprimer_symptome,
    name="supprimer_symptome"
    ),

    path(
    "enfants/<int:pk>/modifier/",
    views.modifier_enfant,
    name="modifier_enfant"
    ),

    # =============================
    # SANTÉ DE L'ENFANT
    # =============================

    path(
        "enfants/<int:enfant_id>/croissance/",
        views.croissance,
        name="croissance"
    ),
    
     path(
        "enfants/<int:enfant_id>/consultations/ajouter/",
        views.ajouter_consultation,
        name="ajouter_consultation"
    ),
     
    path(
    "enfants/<int:enfant_id>/consultations/",
    views.liste_consultations,
    name="liste_consultations"
    ),

    path(
        "enfants/<int:enfant_id>/vaccinations/",
        views.vaccination,
        name="vaccination"
    ),

    path(
        "enfants/<int:enfant_id>/rendez-vous/",
        views.rendez_vous,
        name="rendez_vous"
    ),

    path(
        "enfants/<int:enfant_id>/consultations/",
        views.consultation,
        name="consultation"
    ),

    path(
        "enfants/<int:enfant_id>/bien-etre/",
        views.bien_etre,
        name="bien_etre"
    ),
    

    path(
        "temperature/<int:temperature_id>/supprimer/",
        views.supprimer_temperature,
        name="supprimer_temperature"
    ),
    
    path(
    "enfant/<int:enfant_id>/",
    views.detail_enfant,
    name="detail_enfant"
    ),
    
    path(
    "enfant/<int:enfant_id>/temperature/",
    views.suivi_temperature,
    name="suivi_temperature"
     ),
    path(
    "enfants/<int:enfant_id>/traitements/",
    views.traitements,
    name="traitements"
),

path(
    "enfants/<int:enfant_id>/traitements/ajouter/",
    views.ajouter_traitement,
    name="ajouter_traitement"
),

path(
    "traitements/<int:traitement_id>/prise/",
    views.enregistrer_prise,
    name="enregistrer_prise"
),

path(
    "enfants/<int:enfant_id>/inviter-parent/",
    views.inviter_parent,
    name="inviter_parent"
),

path(
    "partage/<int:partage_id>/accepter/",
    views.accepter_partage,
    name="accepter_partage"
),

# =========================================================
# MODE GARDE
# =========================================================

path(
    "enfants/<int:enfant_id>/mode-garde/creer/",
    views.creer_mode_garde,
    name="creer_mode_garde"
),

path(
    "enfants/<int:enfant_id>/mode-garde/<int:mode_garde_id>/",
    views.mode_garde_detail,
    name="mode_garde_detail"
),

path(
    "enfants/<int:enfant_id>/mode-garde/<int:mode_garde_id>/desactiver/",
    views.desactiver_mode_garde,
    name="desactiver_mode_garde"
),

path(
    "mode-garde/<uuid:token>/",
    views.consulter_mode_garde,
    name="consulter_mode_garde"
),

path(
    "enfants/<int:enfant_id>/mode-garde/<int:mode_garde_id>/pdf/",
    views.mode_garde_pdf,
    name="mode_garde_pdf"
),

path(
    "enfants/<int:enfant_id>/mode-garde/<int:mode_garde_id>/image/",
    views.mode_garde_image,
    name="mode_garde_image"
),

path(
    "enfants/<int:enfant_id>/mode-garde/<int:mode_garde_id>/whatsapp/",
    views.mode_garde_whatsapp,
    name="mode_garde_whatsapp"
),

path(
    "enfants/<int:enfant_id>/mode-garde/<int:mode_garde_id>/sms/",
    views.mode_garde_sms,
    name="mode_garde_sms"
),

]
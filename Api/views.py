import json

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from sante.models import Parent


@csrf_exempt
@require_POST
def inscription(request):
	try:
		data = json.loads(request.body or "{}")
	except json.JSONDecodeError:
		return JsonResponse(
			{"error": "Le corps de la requête doit être un JSON valide."},
			status=400,
		)

	required_fields = ("username", "email", "password")
	missing_fields = [field for field in required_fields if not str(data.get(field, "")).strip()]
	if missing_fields:
		return JsonResponse(
			{
				"error": "Veuillez remplir tous les champs obligatoires.",
				"fields": missing_fields,
			},
			status=400,
		)

	username = str(data["username"]).strip()
	email = str(data["email"]).strip()
	password = str(data["password"])

	if User.objects.filter(username=username).exists():
		return JsonResponse(
			{"error": "Ce nom d'utilisateur est déjà utilisé."},
			status=409,
		)

	if User.objects.filter(email=email).exists():
		return JsonResponse(
			{"error": "Cette adresse email est déjà utilisée."},
			status=409,
		)

	try:
		with transaction.atomic():
			user = User.objects.create_user(
				username=username,
				email=email,
				password=password,
			)
			Parent.objects.create(
				user=user,
				telephone=str(data.get("telephone", "")).strip(),
				adresse=str(data.get("adresse", "")).strip(),
			)
	except IntegrityError:
		return JsonResponse(
			{"error": "Impossible de créer ce compte."},
			status=409,
		)

	return JsonResponse(
		{
			"message": "Votre compte parent a été créé avec succès.",
			"user": {
				"id": user.id,
				"username": user.username,
				"email": user.email,
			},
		},
		status=201,
	)


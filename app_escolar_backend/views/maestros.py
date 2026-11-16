import json
from django.db import transaction
from django.contrib.auth.models import Group, User
from rest_framework import permissions, generics, status
from rest_framework.response import Response
from app_escolar_backend.serializers import UserSerializer
from app_escolar_backend.models import Maestros


class MaestrosAll(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return Response({})


class MaestrosView(generics.CreateAPIView):
    # Permisos por método (sobreescribe el comportamiento default)
    # Verifica que el usuario esté autenticado para las peticiones GET, PUT y DELETE
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return [] # POST no requiere autenticación

    # Registrar nuevo maestro
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        
        # Serializamos los datos de autenticación del maestro para validarlos
        user = UserSerializer(data=request.data)
        
        if user.is_valid():
            # Datos del usuario --- esto va en la tabla auth_user
            role = request.data['rol']
            first_name = request.data['first_name']
            last_name = request.data['last_name']
            email = request.data['email']
            password = request.data['password']

            # Valida si existe el usuario con ese correo
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                return Response({"message": "Usuario " + email + ", ya está registrado"}, 400)

            # Crea el usuario en la BD
            user = User.objects.create(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=1
            )
            # Cifra la contraseña 
            user.set_password(password)
            user.save()

            # Se guarda el rol -> maestro
            group, created = Group.objects.get_or_create(name=role)
            group.user_set.add(user)

            # El arreglo de materias se convierte a texto JSON para guardarlo en un TextField
            materias = request.data.get('materias_array', [])
            if isinstance(materias, list):
                materias = json.dumps(materias, ensure_ascii=False)

            # Almacenar los datos adicionales del maestro
            maestro = Maestros.objects.create(
                user=user,
                id_trabajador=request.data['id_trabajador'],
                fecha_nacimiento=request.data['fecha_nacimiento'],
                telefono=request.data['telefono'],
                rfc=request.data['rfc'].upper(),
                cubiculo=request.data['cubiculo'],
                edad=request.data['edad'],
                area_investigacion=request.data['area_investigacion'],
                materias_array=materias
            )
            maestro.save()

            return Response({"Maestro creado correctamente": maestro.id}, 201)

        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)
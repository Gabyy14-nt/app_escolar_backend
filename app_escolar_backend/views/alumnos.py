from django.db import transaction
from django.contrib.auth.models import Group, User
from rest_framework import permissions, generics, status
from rest_framework.response import Response
from app_escolar_backend.serializers import UserSerializer
from app_escolar_backend.models import Alumnos


class AlumnosAll(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return Response({})


class AlumnosView(generics.CreateAPIView):
    
    # Permisos por método (sobreescribe el comportamiento default)
    # Verifica que el usuario esté autenticado para las peticiones GET, PUT y DELETE
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return [] # POST no requiere autenticación
    
    # Registrar nuevo alumno
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        
        # Serializamos los datos de autenticación del alumno para validarlos
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

            # Se guarda el rol -> alumno
            group, created = Group.objects.get_or_create(name=role)
            group.user_set.add(user)

            # Almacenar los datos adicionales del alumno
            alumno = Alumnos.objects.create(
                user=user,
                matricula=request.data['matricula'],
                curp=request.data['curp'].upper(),
                rfc=request.data['rfc'].upper(),
                fecha_nacimiento=request.data['fecha_nacimiento'],
                edad=request.data['edad'],
                telefono=request.data['telefono'],
                ocupacion=request.data['ocupacion']
            )
            alumno.save()

            return Response({"Alumno creado correctamente": alumno.id}, 201)

        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)
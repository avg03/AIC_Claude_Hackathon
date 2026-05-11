from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import User
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
# Create your views here.

@api_view(['POST']) 
def register_user(request):
    try:
        data=request.data
        user=User.objects.create_user(username=data['username'],password=data['password'],age=data['age'],weight=data['weight'],height=data['height'],primary_goal=data['primary_goal'])
        user.save()
        return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
#the login user 
@api_view(['POST'])
def login_user(request):
    try:
        data=request.data
        user=authenticate(username=data['username'],password=data['password'])
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


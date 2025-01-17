from django.shortcuts import render
from rest_framework import viewsets
from .models import Expense, Category
from .serializers.expense_serializer import ExpenseSerializer
from .serializers.category_serializer import CategorySerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .serializers.login_serializers import UserRegistrationSerializer, LoginSerializer
from .models import UserProfile
from .serializers.user_serializers import UserProfileSerializer

class RegisterAPIView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()  # Save the User instance
            # Create a UserProfile instance for the user
            UserProfile.objects.create(user=user, first_name=user.first_name, last_name=user.last_name)
            return Response(
                {"message": "User registered successfully", "user_id": user.id},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            username = validated_data['username']
            password = validated_data['password']
            user = authenticate(username=username, password=password)

            if user:
                # Fetch the associated UserProfile
                try:
                    profile = user.userprofile
                except UserProfile.DoesNotExist:
                    return Response(
                        {"message": "User profile not found. Please contact support."},
                        status=status.HTTP_404_NOT_FOUND
                    )

                return Response({
                    'user_id': user.id,
                    'username': user.username,
                    'first_name': profile.first_name,
                    'last_name': profile.last_name,
                    'message': 'Login successful'
                }, status=status.HTTP_200_OK)
            return Response(
                {"message": "Invalid username or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        categories = self.get_queryset()
        if not categories.exists():
            return Response(
                {"message": "No Data Found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        """
        This view returns a list of all expenses for the user specified by the `user_id` query parameter.
        """
        # Retrieve the user_id from the query parameters
        user_id = self.request.query_params.get('user_id')

        # If no user_id is provided, return all expenses (or you can raise an error)
        if user_id is None:
            return 'Please provide User Id'

        # Filter the expenses by the user_id
        return Expense.objects.filter(user_id=user_id)

class AnalyticsView(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user

        # Ensure user is authenticated
        if not user.is_authenticated:
            return Response(
                {"message": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Calculate total and category-wise expenses
        total_expense = Expense.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum'] or 0
        category_expenses = Expense.objects.filter(user=user).values('category__name').annotate(Sum('amount'))

        # Format response
        return Response({
            "total_expense": total_expense,
            "category_expenses": list(category_expenses) if category_expenses else "No expenses found"
        })

class ProfileView(APIView):
    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'message': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            profile = UserProfile.objects.get(user__id=user_id)
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({'message': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)



        
class ProfileUpdateView(APIView):
    def put(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        try:
            profile = UserProfile.objects.get(user_id=user_id)
            profile.first_name = request.data.get('first_name')
            profile.last_name = request.data.get('last_name')
            profile.username = request.data.get('username')
            profile.save()
            return Response({'message': 'Profile updated successfully'}, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({'message': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)


from django.contrib.auth.tokens import PasswordResetTokenGenerator
from datetime import datetime, timedelta
from rest_framework_simplejwt.tokens import RefreshToken

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            str(user.is_active) + str(user.pk) + str(timestamp)
        )

token_generator = AccountActivationTokenGenerator()

def generate_auth_token(user):
    # Define the token payload data
    token_payload = {
        "user_id": user.id,
        "username": user.username,
        "exp": datetime.timestamp(datetime.utcnow() + timedelta(seconds=5)),  # Set expiration time (1 hour)
    }

    # Create a RefreshToken instance with the custom payload
    token = RefreshToken.for_user(user)
    token.payload.update(token_payload)
    
    
    # Get the access token
    access_token = str(token.access_token)

    return access_token
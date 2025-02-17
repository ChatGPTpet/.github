import json
import jwt
import requests
from django.contrib.auth import authenticate
import environ

env = environ.Env(
    DEBUG=(bool, False),
)

def jwt_get_username_from_payload_handler(payload):
    username = payload.get('sub').replace('|', '.')
    authenticate(remote_user=username)
    return username
    
def jwt_decode_token(token):
    header = jwt.get_unverified_header(token)
    # jwks = requests.get('{}.well-known/jwks.json'.format(env("JWT_ISSUER"))).json()
    base_url = env("JWT_ISSUER").rstrip('/')
    jwks = requests.get(f'{base_url}/.well-known/jwks.json').json()
    public_key = None
    for jwk in jwks['keys']:
        if jwk['kid'] == header['kid']:
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))

    if public_key is None:
        raise Exception('Public key not found.')

    issuer = '{}'.format(env("JWT_ISSUER"))
    return jwt.decode(token, public_key, audience=env("JWT_AUDIENCE"), issuer=issuer, algorithms=['RS256'])
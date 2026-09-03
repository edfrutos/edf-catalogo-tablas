import pickle
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

BASE = Path(__file__).resolve().parent

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]

credentials_file = BASE / "credentials.json"
token_file = BASE / "token.pickle"

flow = InstalledAppFlow.from_client_secrets_file(
    str(credentials_file),
    scopes=SCOPES,
)

creds = flow.run_local_server(
    port=0,
    open_browser=True,
)

with open(token_file, "wb") as token:
    pickle.dump(creds, token)

print(f"OK: token.pickle creado en {token_file}")

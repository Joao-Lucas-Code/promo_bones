"""WSGI entrypoint para deploy no Render."""
from promo_bones.main import app

if __name__ == "__main__":
    app.run()

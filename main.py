"""Sanity-check the local environment before running the app.

Verifies required settings load from .env, then prints how to start
the backend and frontend. Run with: python main.py
"""

from backend.config import settings


def main():
    print("Hotel Booking Agent — environment check")
    print(f"  Azure OpenAI endpoint : {settings.AZURE_OPENAI_ENDPOINT}")
    print(f"  Azure OpenAI deployment: {settings.AZURE_OPENAI_DEPLOYMENT}")
    print(f"  Database URL          : {settings.DATABASE_URL}")
    print(f"  API URL               : {settings.API_URL}")
    print("\nConfig loaded successfully. Start the app with:")
    print("  uvicorn backend.api.main:app --reload")
    print("  streamlit run frontend/streamlit_app.py")


if __name__ == "__main__":
    main()

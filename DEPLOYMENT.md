# Streamlit Cloud deployment

1. Upload this project to a private GitHub repository.
2. In Streamlit Community Cloud, create an app from `app.py`.
3. Add these values under App settings > Secrets:

```toml
REVIEW_USERNAME = "shopee-review"
REVIEW_PASSWORD = "replace-with-a-strong-review-password"
```

4. Deploy and confirm that the login page and dashboard open.
5. Use the deployed HTTPS domain as the Shopee Live Redirect URL Domain.
6. Give Shopee only the dedicated review credentials, never the GitHub or Google credentials.

Do not commit `.env` or `.streamlit/secrets.toml`.

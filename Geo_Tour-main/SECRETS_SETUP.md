# Streamlit Secrets Configuration Guide

This application uses [Streamlit secrets management](https://docs.streamlit.io/develop/concepts/connections/secrets-management) to securely handle API keys and sensitive credentials.

## Required API Keys

The following API keys are required for the application to function:

1. **OPENAI_API_KEY** - Required for script generation and scene planning
   - Get your key from: https://platform.openai.com/api-keys
   - Format: `sk-...`

2. **REPLICATE_API_KEY** - Required for video generation
   - Get your key from: https://replicate.com/account/api-tokens
   - Format: `r8_...`

## Optional API Keys

The following API keys are optional and enable additional features:

3. **GEMINI_API_KEY** - Optional for matplotlib diagram generation
   - Get your key from: https://aistudio.google.com/app/apikey
   - Enables labeled diagram generation with animations

4. **ELEVENLABS_API_KEY** - Optional for text-to-speech
   - Get your key from: https://elevenlabs.io/

## Local Development Setup

For local development, you can use either `.env` file or Streamlit secrets:

### Option 1: Using .env file (Recommended for local)

1. Create a `.env` file in the `Geo_Tour-main` directory:
   ```bash
   cd Geo_Tour-main
   cp .env.example .env  # If you have an example file
   ```

2. Add your API keys to `.env`:
   ```bash
   OPENAI_API_KEY=sk-...
   REPLICATE_API_KEY=r8_...
   GEMINI_API_KEY=...
   ELEVENLABS_API_KEY=...
   ```

### Option 2: Using Streamlit secrets

1. Create the secrets directory and file:
   ```bash
   cd Geo_Tour-main
   mkdir -p .streamlit
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. Edit `.streamlit/secrets.toml` and add your API keys:
   ```toml
   OPENAI_API_KEY = "sk-..."
   REPLICATE_API_KEY = "r8_..."
   GEMINI_API_KEY = "..."
   ELEVENLABS_API_KEY = "..."
   ```

3. The secrets file is already in `.gitignore` so it won't be committed to version control.

## Streamlit Cloud Deployment

When deploying to Streamlit Cloud, you must use Streamlit secrets:

1. Deploy your app to Streamlit Cloud

2. Go to your app's dashboard at https://share.streamlit.io/

3. Click on your app, then click the "⚙️ Settings" button

4. Go to the "Secrets" section

5. Add your secrets in TOML format:
   ```toml
   OPENAI_API_KEY = "sk-..."
   REPLICATE_API_KEY = "r8_..."
   GEMINI_API_KEY = "..."
   ELEVENLABS_API_KEY = "..."
   ```

6. Click "Save"

7. Your app will automatically restart with the new secrets

## How It Works

The application uses a `get_secret()` function in `config.py` that:

1. First tries to read from Streamlit secrets (`st.secrets`)
2. Falls back to environment variables if Streamlit is not available
3. Falls back to `.env` file if `python-dotenv` is installed

This approach ensures:
- ✅ Secure secrets management in Streamlit Cloud
- ✅ Backward compatibility with existing `.env` files
- ✅ Works in both local and cloud environments
- ✅ No secrets committed to version control

## Verifying Your Setup

After configuring your secrets:

1. Run the Streamlit app:
   ```bash
   cd Geo_Tour-main
   streamlit run app.py
   ```

2. Check the "🔑 API Keys Status" section in the sidebar

3. You should see green checkmarks (✅) for configured keys

4. If you see warnings (⚠️), check your secrets configuration

## Troubleshooting

### "API key not found" error

- Make sure you've added the secrets to `.streamlit/secrets.toml` or `.env`
- Restart the Streamlit app after adding secrets
- Check that the secret keys are spelled correctly (case-sensitive)

### Secrets not loading in Streamlit Cloud

- Go to app settings and verify secrets are saved
- Make sure there are no syntax errors in your TOML format
- Check that secret values don't have extra quotes or spaces
- Redeploy the app if needed

### Local vs Cloud differences

- Local: Can use either `.env` or `.streamlit/secrets.toml`
- Cloud: Must use Streamlit Cloud secrets (in app settings)
- The app automatically detects which environment it's in

## Security Best Practices

1. ✅ **Never commit secrets to version control**
   - `.env` and `.streamlit/secrets.toml` are in `.gitignore`

2. ✅ **Use different API keys for development and production**
   - Consider using separate keys for local testing

3. ✅ **Rotate keys if compromised**
   - Generate new keys from provider dashboards
   - Update secrets in Streamlit Cloud immediately

4. ✅ **Limit API key permissions**
   - Use read-only or limited-scope keys when possible

## Additional Resources

- [Streamlit Secrets Management Documentation](https://docs.streamlit.io/develop/concepts/connections/secrets-management)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Replicate API Documentation](https://replicate.com/docs)
- [Google Gemini API Documentation](https://ai.google.dev/docs)

# Switching LLM Providers

The system now supports any OpenAI-compatible LLM provider. Switch between them instantly by updating `.env`.

## Quick Reference

### 1. Cerebras (Default - High Quality)
```ini
LLM_PROVIDER=cerebras
LLM_API_URL=https://api.cerebras.ai/v1
LLM_API_KEY=sk-...your-key...
LLM_MODEL=llama3.1-70b
```
- **Speed**: Fast
- **Quality**: Excellent
- **Cost**: Premium
- **Best for**: High-quality digests, production use
- **Get API key**: https://cloud.cerebras.ai/

### 2. Groq (Fast & Cost-Effective)
```ini
LLM_PROVIDER=groq
LLM_API_URL=https://api.groq.com/openai/v1
LLM_API_KEY=gsk_...your-key...
LLM_MODEL=mixtral-8x7b-32768
```
- **Speed**: ⚡ Fastest
- **Quality**: Very Good
- **Cost**: Free tier available
- **Best for**: Fast processing, budget-conscious, experimentation
- **Get API key**: https://console.groq.com/

### 3. Together AI (Flexible)
```ini
LLM_PROVIDER=together
LLM_API_URL=https://api.together.xyz/v1
LLM_API_KEY=...your-key...
LLM_MODEL=meta-llama/Llama-3-70b-chat-hf
```
- **Speed**: Fast
- **Quality**: Very Good
- **Cost**: Pay-as-you-go
- **Best for**: Custom models, research
- **Get API key**: https://www.together.ai/

### 4. OpenAI (Premium GPT Models)
```ini
LLM_PROVIDER=openai
LLM_API_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...your-key...
LLM_MODEL=gpt-4-turbo
```
- **Speed**: Standard
- **Quality**: Highest
- **Cost**: Expensive
- **Best for**: Maximum quality requirements
- **Get API key**: https://platform.openai.com/api-keys

### 5. Local/Self-Hosted (Private)
```ini
LLM_PROVIDER=local
LLM_API_URL=http://localhost:8000/v1
LLM_API_KEY=not-needed
LLM_MODEL=your-model-name
```
- **Speed**: Variable
- **Quality**: Depends on model
- **Cost**: Free (after setup)
- **Best for**: Privacy, no API costs, on-premise
- **Setup**: Use Ollama, vLLM, or text-generation-webui
- **Example Ollama setup**:
  ```bash
  ollama pull llama2:70b
  ollama serve  # Runs on http://localhost:11434
  # Then use http://localhost:11434/v1 as API URL
  ```

## How to Switch

### Option 1: Manual Edit
Edit `.env` and update these 4 variables:
```bash
nano .env
# Edit: LLM_PROVIDER, LLM_API_URL, LLM_API_KEY, LLM_MODEL
# Save and exit
python -m src.main --channels @your_channel
```

### Option 2: Command Line (Linux/Mac)
```bash
# Switch to Groq
sed -i '' 's/LLM_PROVIDER=.*/LLM_PROVIDER=groq/' .env
sed -i '' 's|LLM_API_URL=.*|LLM_API_URL=https://api.groq.com/openai/v1|' .env
sed -i '' 's/LLM_API_KEY=.*/LLM_API_KEY=gsk_your_key/' .env
sed -i '' 's/LLM_MODEL=.*/LLM_MODEL=mixtral-8x7b-32768/' .env

python -m src.main --channels @your_channel
```

### Option 3: Create Aliases
Add to your shell config (`~/.bash_profile`, `~/.zshrc`, etc.):
```bash
alias digest-cerebras='export LLM_PROVIDER=cerebras && python -m src.main'
alias digest-groq='export LLM_PROVIDER=groq && python -m src.main'
alias digest-local='export LLM_PROVIDER=local && python -m src.main'

# Then use:
digest-groq --channels @your_channel
```

## Comparison Table

| Feature | Cerebras | Groq | Together | OpenAI | Local |
|---------|----------|------|----------|--------|-------|
| **Speed** | Fast | ⚡⚡⚡ Fastest | Fast | Standard | Variable |
| **Quality** | Excellent | Very Good | Very Good | Best | Good-Excellent |
| **Cost** | Premium | Free tier | Cheap | Expensive | Free |
| **Setup Time** | 5 min | 5 min | 5 min | 5 min | 30 min |
| **Privacy** | Cloud | Cloud | Cloud | Cloud | Local ✓ |
| **Downtime Risk** | Low | Low | Low | Low | Depends |
| **Context Size** | 200k | 32k | Varies | 128k | Varies |
| **Best For** | Production | Budget | Experimentation | Premium | Privacy |

## Testing Provider Switch

After switching providers, test with a simple command:

```bash
# Quick test with small number of messages
python -m src.main --channels @your_channel --start-date 2025-09-01 --end-date 2025-09-02

# This will show you:
# - Configuration loaded
# - Messages fetched
# - LLM model and provider used
# - Digest generation status
# - Any errors (API key, rate limits, etc.)
```

## Troubleshooting

### "API key invalid" or "Unauthorized (401)"
- ✓ Check API key is correct and active in provider's dashboard
- ✓ Verify key hasn't expired
- ✓ For Groq: Make sure it's a fresh key (keys rotate)

### "Payment required" or "Out of quota"
- ✓ Check account balance/credits
- ✓ Verify subscription is active
- ✓ For Groq: Free tier has rate limits, wait before retry

### "Connection timeout"
- ✓ Check internet connection
- ✓ Verify URL is correct (typo in LLM_API_URL?)
- ✓ For local: ensure your local server is running

### "Invalid model"
- ✓ Check model name matches provider's available models
- ✓ Some models require specific API versions
- ✓ Use provider's API documentation to list available models

## Example Workflow: Try Groq Before Committing

```bash
# 1. Backup current config
cp .env .env.backup

# 2. Get Groq API key from console.groq.com
# (Takes 2 minutes)

# 3. Update .env with Groq settings
nano .env
# Change:
# LLM_PROVIDER=groq
# LLM_API_URL=https://api.groq.com/openai/v1
# LLM_API_KEY=gsk_xxx
# LLM_MODEL=mixtral-8x7b-32768

# 4. Test with small dataset
python -m src.main --channels @your_channel --start-date 2025-09-01 --end-date 2025-09-02

# 5a. If happy - keep it!
# 5b. If not - restore backup
#     cp .env.backup .env
```

## No Code Changes Needed! 🎉

The beauty of the new abstraction:
- **Zero** code changes to switch providers
- **Zero** dependency conflicts
- **Zero** risk of regressions
- Just update `.env` and run

Your existing scripts, crons, Docker containers all work unchanged.

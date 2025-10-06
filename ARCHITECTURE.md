# Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Telegram Digest PoC                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   User CLI  │────▶│  main.py     │────▶│ Configuration   │
│  Arguments  │     │  (Orchestr.) │     │   (config.py)   │
└─────────────┘     └──────────────┘     └─────────────────┘
                            │
                            ▼
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────────┐                   ┌──────────────────┐
│ TelegramFetcher  │                   │ DigestGenerator  │
│                  │                   │                  │
│ - Connect to TG  │                   │ - Format msgs    │
│ - Fetch messages │                   │ - Estimate size  │
│ - Filter by date │                   │ - Choose method  │
│ - Extract URLs   │                   └────────┬─────────┘
└────────┬─────────┘                            │
         │                                      ▼
         │                            ┌──────────────────┐
         │                            │ CerebrasClient   │
         │                            │                  │
         │                            │ - Generate       │
         │                            │ - Map-reduce     │
         │                            │ - Format prompt  │
         │                            └────────┬─────────┘
         │                                     │
         ▼                                     ▼
    ┌─────────────────────────────────────────────┐
    │           Generated Digest                   │
    │  (Structured text with categories & links)   │
    └─────────────┬───────────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ OutputHandler  │
         │                │
         │ - Print        │
         │ - Save to file │
         │ - Send to TG   │
         └────────────────┘
```

## Data Flow

```
1. INPUT
   │
   ├─ Channels: [@channel1, @channel2, ...]
   ├─ Date Range: [start_date, end_date]
   └─ Options: [output_file, telegram_target, ...]
   │
   ▼
2. TELEGRAM FETCHING
   │
   ├─ Connect with Telethon (MTProto)
   ├─ Iterate through channels
   ├─ Filter messages by date
   └─ Extract: text, links, metadata
   │
   ▼
3. MESSAGE FORMATTING
   │
   ├─ Format each message:
   │  │
   │  └─ === Channel Name — Date ===
   │     Message text
   │     Link: https://t.me/channel/123
   │     URLs: [url1, url2, ...]
   │
   └─ Combine all messages
   │
   ▼
4. SIZE ESTIMATION
   │
   ├─ Estimate tokens (chars / 4)
   │
   └─ Decision:
      ├─ < 50k tokens  → Single-pass
      └─ > 50k tokens  → Map-reduce
   │
   ▼
5A. SINGLE-PASS                    5B. MAP-REDUCE
    │                                  │
    └─ Send all to LLM                 ├─ Split into chunks
       with digest prompt              ├─ Process each chunk
                                       ├─ Generate partial summaries
                                       └─ Combine partials → Final digest
    │                                  │
    └──────────────┬───────────────────┘
                   ▼
6. LLM PROCESSING (Cerebras)
   │
   ├─ System Prompt:
   │  └─ "Analyze content, identify natural categories, create summaries, keep links..."
   │
   ├─ User Prompt:
   │  └─ Messages text
   │
   └─ Response:
      └─ Structured digest with AI-generated categories:
         ├─ [Emoji] [Category Name]: summary + links
         ├─ [Emoji] [Category Name]: summary + links
         └─ ... (3-7 categories based on content)
   │
   ▼
7. OUTPUT
   │
   ├─ Console: Print formatted digest
   ├─ File: Save to digest_TIMESTAMP.txt
   └─ Telegram: Send via Bot API (HTTP, HTML formatting)
```

## Component Interactions

```
┌───────────────────────────────────────────────────────┐
│                    config.py                          │
│  (Configuration, Environment Variables, Validation)   │
└───────────────────────────────────────────────────────┘
                          ▲
                          │ (used by all)
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   telegram   │  │   cerebras   │  │    output    │
│   _fetcher   │  │   _client    │  │   _handler   │
│              │  │              │  │              │
│ - Session    │  │ - API Client │  │ - File I/O   │
│ - Messages   │  │ - Prompts    │  │ - Bot API    │
│ - Channels   │  │ - Streaming  │  │ - HTML fmt   │
│ - Filtering  │  │ - Map-reduce │  │ - Splitting  │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                ┌──────────────────┐
                │ digest_generator │
                │                  │
                │ - Orchestration  │
                │ - Size decision  │
                │ - Formatting     │
                └──────────────────┘
                          ▲
                          │
                          │
                    ┌─────────┐
                    │ main.py │
                    │  (CLI)  │
                    └─────────┘
```

## Map-Reduce Flow (for large datasets)

```
┌────────────────────────────────────┐
│  Large Message Collection          │
│  (> 50,000 tokens)                 │
└─────────────┬──────────────────────┘
              │
              ▼
     ┌────────────────┐
     │  Split into    │
     │  Chunks        │
     └────────┬───────┘
              │
    ┌─────────┼─────────┬─────────┐
    ▼         ▼         ▼         ▼
  Chunk1   Chunk2   Chunk3   Chunk4
    │         │         │         │
    ▼         ▼         ▼         ▼
┌─────────────────────────────────────┐
│      MAP Phase                      │
│  (Process each chunk separately)    │
│                                     │
│  Cerebras API → Partial Summary 1   │
│  Cerebras API → Partial Summary 2   │
│  Cerebras API → Partial Summary 3   │
│  Cerebras API → Partial Summary 4   │
└─────────────┬───────────────────────┘
              │
              ▼
     ┌────────────────┐
     │  Combine all   │
     │  partial       │
     │  summaries     │
     └────────┬───────┘
              │
              ▼
┌─────────────────────────────────────┐
│      REDUCE Phase                   │
│  (Merge into final digest)          │
│                                     │
│  Cerebras API →                     │
│  - Identify & merge similar topics  │
│  - Generate appropriate categories  │
│  - Remove duplicates                │
│  - Consolidate links                │
│  - Create final structure           │
└─────────────┬───────────────────────┘
              │
              ▼
       ┌────────────┐
       │   Final    │
       │   Digest   │
       │ (Dynamic   │
       │ Categories)│
       └────────────┘
```

## Security & Configuration Flow

```
┌─────────────┐
│  .env file  │
│             │
│ API_ID      │
│ API_HASH    │
│ CEREBRAS_   │
│   API_KEY   │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  python-dotenv   │
│  (load vars)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Config class   │
│                  │
│  - Load          │
│  - Validate      │
│  - Provide       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Application     │
│  Components      │
└──────────────────┘
```

## Error Handling Strategy

```
┌─────────────────┐
│  User Input     │
└────────┬────────┘
         │
         ▼
    ┌────────────┐
    │ Validate   │─── Invalid ──→ Error Message
    └────┬───────┘                      │
         │ Valid                        │
         ▼                              │
    ┌────────────┐                      │
    │ TG Fetch   │─── Error ──→ Log + Retry/Skip
    └────┬───────┘                      │
         │ Success                      │
         ▼                              │
    ┌────────────┐                      │
    │ LLM Call   │─── Error ──→ Fallback/Partial
    └────┬───────┘                      │
         │ Success                      │
         ▼                              │
    ┌────────────┐                      │
    │ Output     │─── Error ──→ Save locally
    └────┬───────┘                      │
         │                              │
         ▼                              │
    ┌────────────┐                      │
    │  Success   │◀─────────────────────┘
    └────────────┘
```

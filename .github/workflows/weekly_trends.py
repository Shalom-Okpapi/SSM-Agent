name: Weekly Trends Report

on:
  schedule:
    - cron: "0 8 * * 1"   # Every Monday at 8 AM UTC (9 AM WAT)
  workflow_dispatch:

jobs:
  send-trends:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Send Weekly Trends
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          NVIDIA_API_KEY: ${{ secrets.NVIDIA_API_KEY }}
          NVIDIA_MODEL: ${{ secrets.NVIDIA_MODEL || 'meta/llama-3.1-8b-instruct' }}
        run: python weekly_trends.py

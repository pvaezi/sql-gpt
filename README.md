# SQL GPT

This tool provides an interactive experience for ask questions about your tabular data using AI to perform your SQL queries for you.
This repo software uses a multi-agent AI and SQL query engine to enable such experience.
You can simply load your data and ask questions for it.

This repository is designed to support various LLM services, as well as various SQL engines.

Currently, following AIs are supported:

1. OpenAI

Currently, following SQL engines are supported:

2. Duckdb

## Usage

To get started, install the python package with your desired SQL engine and LLM tools.
For instance, if you want to use OpenAI for query reasoning, and DuckDB for executing queries, install:

```bash
pip install "sql-gpt[openai,duckdb]"
```

Now you can run the prompt tool in your machine:

```bash
export OPENAI_API_KEY=...
python -m sql_gpt --llm openai --llm-kwargs '{"model": "gpt-4o-mini"}' --engine duckdb
```

Now you should see prompting tool available.
You can load one or multiple tables in your AI context, as shown in the example bellow:

```
>>> User prompt (/q to quit, /load to load data):
/load example_data/apple_sales_2024.csv example_data/apple_sales_2024_schema.txt
```

After data is loaded, you can start typing and asking questions from your data:

```
what are the top three states where apple sold most iphones?
```

You can exit program by typing `/q` at any time.

## Multi-Agent Design

![SQL GPT](graph.png "SQL GPT Multi-Agent Design")

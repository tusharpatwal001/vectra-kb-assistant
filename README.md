# Vectra KB Assistant

A Retrieval-Augmented Generation (RAG) knowledge-base assistant that answers questions using relevant knowledge-base articles. It uses vector embeddings and PostgreSQL with the `pgvector` extension to retrieve semantically similar content and generate answers grounded in available documentation.

The assistant supports cited answers when relevant articles are found and fallback responses when the knowledge base does not contain sufficient information.

## Features

* **Semantic search:** Retrieve relevant knowledge-base content using vector similarity.
* **Grounded answers:** Generate responses based on retrieved articles.
* **Source citations:** Include article citations in answers when applicable.
* **Abstention and fallback:** Avoid making unsupported claims when relevant information is unavailable.
* **PostgreSQL + pgvector:** Store and search vector embeddings.
* **Python-based implementation:** Modular assistant logic under `src/`.

## Tech Stack

* Python
* LangChain
* LangChain OpenAI integrations
* PostgreSQL
* pgvector
* Psycopg
* YAML
* Docker

## Project Structure

```text
vectra-kb-assistant/
├── kb_articles/       # Knowledge-base articles
├── src/               # Assistant and retrieval logic
├── app.py             # Application entry point
├── requirements.txt   # Python dependencies
└── README.md
```

## Prerequisites

Install the following before getting started:

* Python 3.10 or newer
* Docker Desktop or Docker Engine
* Git
* An OpenAI API key, if using OpenAI embeddings or chat models

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/tusharpatwal001/vectra-kb-assistant.git
cd vectra-kb-assistant
```

### 2. Pull the PostgreSQL + pgvector Docker image

Pull the PostgreSQL image with pgvector preinstalled:

```bash
docker pull pgvector/pgvector:pg16
```

The image provides PostgreSQL with the pgvector extension available for vector storage and similarity search.

Image reference: [pgvector on Docker](https://hub.docker.com/r/pgvector/pgvector)

### 3. Start the PostgreSQL container

Run the following command:

```bash
docker run -d \
  --name vectra-postgres \
  -e POSTGRES_USER=vectra \
  -e POSTGRES_PASSWORD=vectra_dev_password \
  -e POSTGRES_DB=vectra_kb \
  -p 5432:5432 \
  -v vectra_pgdata:/var/lib/postgresql/data \
  pgvector/pgvector:pg16
```

This command:

* Creates a PostgreSQL database named `vectra_kb`.
* Creates a database user named `vectra`.
* Exposes PostgreSQL on port `5432`.
* Uses a Docker volume to persist database data.

Check the container status:

```bash
docker ps
```

View database logs if needed:

```bash
docker logs vectra-postgres
```

### 4. Enable the pgvector extension

Enable the vector extension in the database:

```bash
docker exec -it vectra-postgres \
  psql -U vectra -d vectra_kb \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Verify that it is installed:

```bash
docker exec -it vectra-postgres \
  psql -U vectra -d vectra_kb \
  -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

You should see `vector` in the output.

### 5. Create a Python virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 6. Install Python dependencies

Install the packages listed in `requirements.txt`:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The project dependencies include LangChain, LangChain OpenAI, LangChain PostgreSQL, Psycopg, PyYAML, and python-dotenv.

### 7. Configure environment variables

Create a `.env` file in the project root if your application configuration uses environment variables.

Example configuration:

```env
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql+psycopg://vectra:vectra_dev_password@localhost:5432/vectra_kb
```

**Important:** These are example variable names and a sample connection string. Confirm the variable names and connection-string format expected by the implementation in `src/` before running the application. Never commit your real API key or production database credentials.

### 8. Configure the knowledge base

Place your knowledge-base documents in the `kb_articles/` directory.

Ensure the document format and file structure match what the ingestion and retrieval code expects.

Before asking questions, verify that the application's setup process has loaded the articles and generated their embeddings. If indexing is performed automatically, follow the existing initialization logic; otherwise, run the appropriate ingestion or indexing procedure implemented in `src/`.

### 9. Run the assistant

The repository includes `app.py` as the entry point for running sample questions.

Start the application with:

```bash
python app.py
```

The script runs example questions covering account lockouts, VPN access, ticket resolution targets, office parking, and mobile email support.

Your output should contain answers based on retrieved knowledge-base content, along with citations or fallback responses where applicable.

## Example Questions

Try questions such as:

* My account got locked. How long until it unlocks by itself?
* What VPN server address should I use when working from home?
* What is the resolution target for a P2 ticket?
* How do I get a parking pass for the Gurugram office?
* Why is my company email not showing up in my iPhone's built-in Mail app?

When the knowledge base contains sufficient relevant information, the assistant should return a grounded answer with applicable citations. When it cannot find sufficient information, it should use the configured fallback behavior.

## Troubleshooting

### PostgreSQL container is not running

Check the container:

```bash
docker ps -a
docker logs vectra-postgres
```

Start it if it is stopped:

```bash
docker start vectra-postgres
```

### Port 5432 is already in use

Change the host-side port mapping to `5433:5432` when creating the container. Update the database connection string to use port `5433`.

### The vector extension is missing

Run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Execute this statement in the database used by the application.

### Database connection fails

Verify that:

* The PostgreSQL container is running.
* The database name, username, and password match the container configuration.
* The host and port in the connection string are correct.
* The application is configured to use the same database.

### Answers are missing citations or return a fallback

Check that:

* Knowledge-base articles exist in `kb_articles/`.
* The articles have been indexed.
* The embedding model and vector dimensions match the database schema.
* The retrieval relevance threshold is appropriate for your content.
* The database contains the expected article records and embeddings.

### Python dependency errors

Activate the virtual environment and reinstall the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Stopping the Database

Stop the PostgreSQL container:

```bash
docker stop vectra-postgres
```

Start it again later:

```bash
docker start vectra-postgres
```

To remove the container:

```bash
docker rm -f vectra-postgres
```

The `vectra_pgdata` volume is retained when the container is removed. To permanently delete the stored database data as well, remove the volume separately:

```bash
docker volume rm vectra_pgdata
```

**Warning:** Removing the volume permanently deletes the database data stored in it.

## Security Notes

* Keep API keys and passwords out of source control.
* Use strong credentials outside local development.
* Avoid exposing PostgreSQL publicly without appropriate network restrictions and authentication.
* Back up important database data regularly.

## Contributing

Contributions, bug reports, and improvements are welcome. Open an issue or submit a pull request through the repository.

## License

No license information is currently specified here. Check the repository for a `LICENSE` file before reusing or distributing this project.

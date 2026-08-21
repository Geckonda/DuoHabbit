# Duohabit App

## How to develop - general

1. Grab the repo.
2. On the host machine, run `python backend/duohabit/scripts/generate_env.py` to generate the .env and .devcontainer/.env files. Or use "python3" command instead "python", if python installed on your machine, but not working.
3. In VSCode or Cursor, install devcontainer VSExtension and open the repo in container(devcontainer). Make sure you have docker and docker-compose available.
4. Run `task backend_install` and `task frontend_install` to install the dependencies.
5. Run `task backend_up` to start the backend.
6. Run `task frontend_up` to start the frontend.
7. You may want to expose the ports persistently so they don't change on manual restarts, though these commands support hot realoading.
8. The env generation script supports incremental updates - it will only add missing fields and abort if there are conflicts.
   If you need to change existing secrets, update the files manually. If you regenerate secrets after the postgres volume
   has been created, you MUST delete the volume with `docker compose -f .devcontainer/docker-compose.yml down -v`
   before restarting, otherwise postgres will have a different password than your .env file.

## How to develop - backend

1. Use `task backend_quality` to autoformat and run linters. Keep pylint fully happy and mypy reasonably happy.
2. Honor the architecture: repositories for data, services for business logic, routers for dependencies and hooking
into the app.
3. Do not forget to maintain the event log and check limits with limits.py utilities.
4. Add telemetry only after you know you need it, not before.
5. Between requests and outside redis/db, keep the app stateless.
6. Keep the SQL fast: if you need to query in a loop, write a better query and add to an appropriate repository.
Remember that services should commit, not repositories.
7. To drop the database for **LOCAL** iterations, run `uv run python -m duohabit.scripts.danger_dropdb --yes-i-am-sure` from `backend`.
8. To run tests, run `task backend_test`. Current testing rules: for every major router, a happy-path test and an error conversion test. For every service, test happy path and notable error paths (not found, not unique, authorization) for every method. Use the `@pytest.mark.asyncio(loop_scope="session")` decorator to ensure the tests run in a single event loop. Failing this will crash them with a somewhat cryptic error! Do not test what FastAPI and Pydantic will ensure, we trust them to be well-tested, test our code instead.

### Environment variable flow

1. Logical environment variables originate in fillme.env
2. An example of fillme.env is example.env
3. .env and .devcontainer/.env are generated from fillme.env by the generate_env.sh script
4. .env is used at deployment time
5. .devcontainer/.env is used in the devcontainer. It will be read by docker compose. The variables will be available in the docker-compose.yml file via ${VARIABLE_NAME}. These should be passed into the environments of the containers via their environment directives. Each variable will probably be used twice: once in the relevant service's environment directive to set up the service, and once in the devcontainer's environment directive to pass the variable into the app so that it can use the configured service.
6. The variables are then read in the app via config.py as OS environment variables.

## How to develop - frontend

🫠

## How to deploy

1. Grab the repo.
2. On the host machine, run `/backend/duohabit/scripts/generate_env.py` to generate the .env and .devcontainer/.env files.
3. The rest is WIP for now, woops.
800. On startup, the app will create an admin user, credentials are `admin@duohabit.com` and `admin`.
Change their password before going public.

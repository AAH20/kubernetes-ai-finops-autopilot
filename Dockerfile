FROM python:3.12-slim AS build
WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip wheel . --no-deps --wheel-dir /wheels

FROM python:3.12-slim
RUN useradd --create-home --uid 10001 app
COPY --from=build /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels
USER 10001
WORKDIR /work
ENTRYPOINT ["ai-finops"]

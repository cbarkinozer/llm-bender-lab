FROM python:3.11.15-slim@sha256:90744cff8f32887f075c47d747a173ff333e9e98801667af93c357fa9f5e28ff
RUN pip install --no-cache-dir pytest==8.4.2 iniconfig==2.3.0 packaging==26.3 pluggy==1.6.0 pygments==2.21.0
ENV PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
WORKDIR /workspace
USER 65534:65534

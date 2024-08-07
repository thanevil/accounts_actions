FROM python:3.10
WORKDIR ./ghost_accounts
COPY ghost_accounts_actions.py /ghost_accounts
RUN pip install requests
CMD python3 ghost_accounts_actions.py


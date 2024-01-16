import time
from pathlib import Path

import github
from github import Github, PullRequest
from github.Repository import Repository
from prometheus_client import start_http_server, Gauge
from github_prometheus_exporter.settings import settings
from github_prometheus_exporter.logger import get_logger


logger = get_logger('github exporter')

GITHUB_SCRAPE_INTERVAL = 60

open_pull_requests_gauge = Gauge(f"open_pull_requests", f"Open pull requests", ['repo_name'])


def get_authenticated_api() -> Github:
    integration = github.GithubIntegration(settings.application_id, settings.private_key)
    access_token = integration.get_access_token(settings.installation_id).token
    return github.Github(access_token)


def get_all_repositories(g: Github) -> list[Repository]:
    return list(g.get_organization(settings.organization_id).get_repos())


def report_open_pull_requests(repo: Repository) -> list[PullRequest]:
    return list(repo.get_pulls(state="open"))


def update_repo_metrics(repo: Repository):
    open_pull_requests = report_open_pull_requests(repo)
    open_pull_requests_gauge.labels(repo_name=repo.name).set(len(open_pull_requests))


def update_metrics():
    while True:
        logger.info("Starting to scrape github")
        g = get_authenticated_api()
        repos = get_all_repositories(g)
        for repo in repos:
            logger.info(f"Scraping {repo=}")
            update_repo_metrics(repo)
        time.sleep(GITHUB_SCRAPE_INTERVAL)


def main() -> None:
    logger.info("Exporter started")
    logger.info("Starting prometheus http server")
    start_http_server(12345)
    logger.info("Started prometheus http server")
    update_metrics()


if __name__ == "__main__":
    main()

import time

import github
from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository
from prometheus_client import Gauge, start_http_server

from github_prometheus_exporter.logger import get_logger
from github_prometheus_exporter.settings import settings

logger = get_logger("github exporter")

open_pull_requests_gauge = Gauge("open_pull_requests", "Open pull requests", ["repo_name"])


def get_authenticated_api() -> Github:
    integration = github.GithubIntegration(settings.application_id, settings.private_key)
    access_token = integration.get_access_token(settings.installation_id).token
    return github.Github(access_token)


def get_all_repositories(g: Github) -> list[Repository]:
    return list(g.get_organization(settings.organization_id).get_repos())


def report_open_pull_requests(repo: Repository) -> list[PullRequest]:
    return list(repo.get_pulls(state="open"))


def update_repo_metrics(repo: Repository) -> None:
    open_pull_requests = report_open_pull_requests(repo)
    open_pull_requests_gauge.labels(repo_name=repo.name).set(len(open_pull_requests))


def update_metrics() -> None:
    while True:
        logger.info("Starting to scrape github")
        g = get_authenticated_api()
        repos = get_all_repositories(g)
        for repo in repos:
            logger.info(f"Scraping {repo=}")
            update_repo_metrics(repo)
        time.sleep(settings.github_scrape_interval)


def main() -> None:
    logger.info("Exporter started")
    logger.info("Starting prometheus http server")
    start_http_server(settings.port)
    logger.info("Started prometheus http server")
    update_metrics()


if __name__ == "__main__":
    main()
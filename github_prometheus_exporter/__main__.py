import time
from datetime import datetime, timedelta

import github
import pytz
from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.WorkflowRun import WorkflowRun
from prometheus_client import Counter, Gauge, Histogram, start_http_server

from github_prometheus_exporter.logger import get_logger
from github_prometheus_exporter.settings import settings

logger = get_logger("github exporter")
github_open_pr_histogram = Histogram(
    "github_pr_duration",
    "Duration of an opened pr until merge",
    ["repo_name"],
    buckets=[hours * 60 * 60 for hours in range(72)],
)
github_actions_histogram = Histogram(
    "success_github_actions_duration",
    "Duration of an action run",
    ["repo_name", "workflow_name"],
    buckets=[1, 5, 10, 30, 60, 120, 180, 240, 300, 360, 420, 480, 600, 900, 1200, 1800],
)
failed_github_actions_counter = Counter(
    "failed_github_actions",
    "Number of failed actions",
    ["repo_name", "workflow_name"],
)
open_pull_requests_gauge = Gauge("github_open_pull_requests", "Open pull requests", ["repo_name"])

Saturday = 5
Friday = 4


def get_authenticated_api() -> Github:
    integration = github.GithubIntegration(settings.application_id, settings.private_key)
    access_token = integration.get_access_token(settings.installation_id).token
    return github.Github(access_token)


def get_all_repositories(g: Github) -> list[Repository]:
    return list(g.get_organization(settings.organization_id).get_repos())


def get_open_pull_requests(repo: Repository, from_time: datetime) -> list[PullRequest]:
    return [
        pull_request
        for pull_request in repo.get_pulls(state="open", sort="created", direction="desc")
        if pull_request.created_at.astimezone(pytz.utc) >= from_time
    ]


def get_merged_pull_requests(repo: Repository, from_time: datetime) -> list[PullRequest]:
    try:
        return [
            pull_request
            for pull_request in repo.get_pulls(state="closed", sort="created", direction="desc")[:100]
            if pull_request.merged_at and pull_request.merged_at.astimezone(pytz.utc) >= from_time
        ]
    except IndexError:
        return []


def get_workflow_runs(repo: Repository, from_time: datetime, status: str) -> list[WorkflowRun]:
    try:
        return [
            workflow
            for workflow in repo.get_workflow_runs(status=status)[:500]
            if workflow.created_at.astimezone(pytz.utc) >= from_time
        ]
    except IndexError:
        return []


def report_workflow_runs(from_time: datetime, repo: Repository) -> None:
    report_success_workflows(from_time, repo)
    report_failed_workflows(from_time, repo)


def report_success_workflows(from_time: datetime, repo: Repository) -> None:
    success_workflow = get_workflow_runs(repo, from_time, "success")
    for workflow in success_workflow:
        github_actions_histogram.labels(repo_name=repo.name, workflow_name=workflow.name).observe(
            workflow.timing().run_duration_ms / 1000
        )


def report_failed_workflows(from_time: datetime, repo: Repository) -> None:
    failed_workflow = get_workflow_runs(repo, from_time, "failure")
    for workflow in failed_workflow:
        failed_github_actions_counter.labels(repo_name=repo.name, workflow_name=workflow.name).inc(1)


def update_repo_metrics(repo: Repository, from_time: datetime) -> None:
    report_opened_pull_requests(from_time, repo)
    report_merge_time(from_time, repo)
    report_workflow_runs(from_time, repo)


def report_merge_time(from_time: datetime, repo: Repository) -> None:
    merged_pull_requests = get_merged_pull_requests(repo, from_time)

    merged_pull_requests_without_deploy = [
        pull_request for pull_request in merged_pull_requests if "deploy" not in pull_request.title.lower()
    ]

    for pull_request in merged_pull_requests_without_deploy:
        (github_open_pr_histogram.labels(repo_name=repo.name).observe(get_pr_duration_without_weekend(pull_request)))


def get_pr_duration_without_weekend(pull_request: PullRequest) -> float:
    duration = (pull_request.merged_at - pull_request.created_at).total_seconds()  # type: ignore
    dates = [
        pull_request.created_at + timedelta(days=days)
        for days in range((pull_request.merged_at - pull_request.created_at).days)  # type: ignore
    ]
    if Friday in [date.weekday() for date in dates] and Saturday in [date.weekday() for date in dates]:
        duration -= 2 * 24 * 60 * 60
    return duration


def report_opened_pull_requests(from_time: datetime, repo: Repository) -> None:
    open_pull_requests = get_open_pull_requests(repo, from_time)
    open_pull_requests_gauge.labels(repo_name=repo.name).set(len(open_pull_requests))


def update_metrics() -> None:
    last_fetch_time = datetime.now(tz=pytz.UTC) - timedelta(days=1)
    while True:
        logger.info(f"Starting to scrape github since {last_fetch_time}")
        g = get_authenticated_api()
        repos = get_all_repositories(g)
        for repo in repos:
            logger.info(f"Scraping {repo=} since {last_fetch_time}")
            update_repo_metrics(repo, last_fetch_time)
        last_fetch_time = datetime.now(tz=pytz.UTC)
        time.sleep(settings.github_scrape_interval)


def main() -> None:
    logger.info("Exporter started")
    logger.info("Starting prometheus http server")
    start_http_server(settings.port)
    logger.info("Started prometheus http server")
    update_metrics()


if __name__ == "__main__":
    main()

from pathlib import Path

import github
from github import Github
from github.Repository import Repository

PRIVATE_KEY_PATH = "./aim-promhippie-exporter.2024-01-16.private-key.pem"
APPLICATION_ID = 798085
INSTALLATION_ID = 46187215
ORGANIZATION_ID = "hakasecurity"


def get_authenticated_api() -> Github:
    private_key = Path(PRIVATE_KEY_PATH).read_text()
    integration = github.GithubIntegration(APPLICATION_ID, private_key)
    access_token = integration.get_access_token(INSTALLATION_ID).token
    return github.Github(access_token)


def get_all_repositories(g: Github) -> list[Repository]:
    return list(g.get_organization(ORGANIZATION_ID).get_repos())


def main() -> None:
    g = get_authenticated_api()

    g.get_repo("hakasecurity/haka")


if __name__ == "__main__":
    main()

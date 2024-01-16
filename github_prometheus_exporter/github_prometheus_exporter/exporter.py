import github
from github import Github
from github.Repository import Repository

PRIVATE_KEY_PATH = './aim-promhippie-exporter.2024-01-16.private-key.pem'
APPLICATION_ID = 798085
INSTALLATION_ID = 46187215
ORGANIZATION_ID = "hakasecurity"


def get_authenticated_api() -> Github:
    with open(PRIVATE_KEY_PATH) as private_key_file:
        private_key = private_key_file.read()

    integration = github.GithubIntegration(APPLICATION_ID, private_key)
    access_token = integration.get_access_token(INSTALLATION_ID).token
    return github.Github(access_token)


def get_all_repositories(g: Github) -> list[Repository]:
    return list(g.get_organization(ORGANIZATION_ID).get_repos())


def main():
    g = get_authenticated_api()

    haka = g.get_repo('hakasecurity/haka')
    print(get_all_repositories(g))


if __name__ == '__main__':
    main()

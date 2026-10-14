from argsense import cli


@cli
def runx(
    appid: str,
    version: str = '',
    use_exist: bool = True,
    *,
    dry_run: bool = False,
) -> None:
    """
    check app exists, if not, download and install it. then run the application.
    this is a test case for showing a long parameter description.

    params:
        appid: the app id (a normalized app name).
        version: the app version to operate on.
            if not given, the last installed version will be used.
        use_exist (-u):
            1. if `version` is not given, will try to use the last installed -
            version.
            2. if `version` is given, but not installed, and if depsland finds
            a newer version already installed, will use the newer one.
                why we do this: due to the design limitation, the cloud drive
                stores only one "latest" version on the oss side; older
                versions are discarded as soon as a new version is published.
                this means user can never retrieve a specific older version at
                that time. we have to force user to use the newer one.

    prerequisite:
        make sure your network available.
    """
    print(
        'appid={}, version={}, use_exist={}, dry_run={}'.format(
            appid, version, use_exist, dry_run
        )
    )


if __name__ == '__main__':
    # python test/long_desc_show_case.py -h
    # python test/long_desc_show_case.py runx hello-world
    # python test/long_desc_show_case.py runx hello-world -u
    cli.run()

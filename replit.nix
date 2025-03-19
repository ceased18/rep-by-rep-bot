{pkgs}: {
  deps = [
    pkgs.python39
    pkgs.python39Packages.pip
    pkgs.python39Packages.discord.py
    pkgs.python39Packages.python-dotenv
    pkgs.python39Packages.requests
    pkgs.python39Packages.reportlab
    pkgs.python39Packages.pytz
  ];
}

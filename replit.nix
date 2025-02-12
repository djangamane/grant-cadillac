{pkgs}: {
  deps = [
    pkgs.python312Packages.gunicorn
    pkgs.zip
  ];
}

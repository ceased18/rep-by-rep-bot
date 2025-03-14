{pkgs}: {
  deps = [
    pkgs.libsodium
    pkgs.glibcLocales
    pkgs.freetype
    pkgs.postgresql
    pkgs.openssl
  ];
}

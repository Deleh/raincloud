{
  description = "Stream media files over SSH";
  nixConfig.bash-prompt = "\[\\e[1mmincloud-dev\\e[0m:\\w\]$ ";
  inputs = {
    nixpkgs.url = github:nixos/nixpkgs/nixos-unstable;
    flake-utils.url = github:numtide/flake-utils;
  };

  outputs = { self, nixpkgs, flake-utils }:

    flake-utils.lib.eachDefaultSystem
      (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
          {
                      # Development shell
          devShell = pkgs.mkShell {
            buildInputs = with pkgs; [
              python3
              python3Packages.flask
              python3Packages.toml
            ];
          };
        }
      );
}

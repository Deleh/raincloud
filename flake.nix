{
  description = "Self-hosted file sharing cloud for you and your friends";
  inputs = {
    nixpkgs.url = github:nixos/nixpkgs/nixos-unstable;
    flake-utils.url = github:numtide/flake-utils;
  };

  outputs = { self, nixpkgs, flake-utils }: {

    nixosModule = { config, ... }:
      with nixpkgs.lib;
      let
        system = config.nixpkgs.localSystem.system;

        python = nixpkgs.legacyPackages.${system}.python3Packages.python;
        flask = nixpkgs.legacyPackages.${system}.python3Packages.flask;
        gunicorn = nixpkgs.legacyPackages.${system}.python3Packages.gunicorn;
        raincloud = self.packages.${system}.raincloud;
        toml = nixpkgs.legacyPackages.${system}.python3Packages.toml;

        cfg = config.services.raincloud;

        raincloud_config = nixpkgs.legacyPackages.${system}.writeText "raincloud_config.py" ''
          CLOUD_NAME = "${cfg.cloudName}"
          SECRET_KEY = "${cfg.secretKey}"
          BASE_PATH = "${cfg.basePath}"
        '';
      in
        {
          options.services.raincloud = {

            enable = mkEnableOption "Enable raincloud WSGI server";

            address = mkOption {
              type = types.str;
              default = "127.0.0.1";
              example = "0.0.0.0";
              description = "Bind address of the server";
            };

            port = mkOption {
              type = types.str;
              default = "8000";
              example = "4000";
              description = "Port on which the server listens";
            };

            user = mkOption {
              type = types.str;
              default = "raincloud";
              description = "User under which the server runs";
            };

            group = mkOption {
              type = types.str;
              default = "raincloud";
              description = "Group under which the server runs";
            };

            cloudName = mkOption {
              type = types.str;
              default = "raincloud";
              description = "Name of the raincloud";
            };

            basePath = mkOption {
              type = types.str;
              description = "Base path of the raincloud";
            };

            secretKey = mkOption {
              type = types.str;
              default = "i_am_a_key";
              description = "Flask secret key";
            };
          };

          config = mkIf cfg.enable {

            systemd.services.raincloud = {
              description = "Enable raincloud WSGI server";
              after = [ "network.target" ];
              wantedBy = [ "multi-user.target" ];
              restartIfChanged = true;

              environment =
                let
                  penv = python.buildEnv.override {
                    extraLibs = [ flask raincloud toml ];
                  };
                in
                  {
                    PYTHONPATH = "${penv}/${python.sitePackages}/";
                  };

              serviceConfig = {
                Type = "simple";
                User = cfg.user;
                Group = cfg.group;
                Restart = "always";
                RestartSec = "5s";
                PermissionsStartOnly = true;

                ExecStart = ''
                  ${gunicorn}/bin/gunicorn "raincloud:app('${raincloud_config}')" \
                    --bind=${cfg.address}:${cfg.port}
                '';
              };
            };

            users.users = mkIf (cfg.user == "raincloud") {
              raincloud = {
                group = cfg.group;
                isSystemUser = true;
              };
            };

            users.groups = mkIf (cfg.group == "raincloud") {
              raincloud = { };
            };

          };

        };

  } // flake-utils.lib.eachDefaultSystem
    (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
        {

          # Package
          packages.raincloud =
            pkgs.python3Packages.buildPythonPackage rec {
              name = "raincloud";
              src = self;
              propagatedBuildInputs = with pkgs; [
                python3Packages.flask
                python3Packages.toml
              ];
            };
          defaultPackage = self.packages.${system}.raincloud;

          # Development shell
          devShell = pkgs.mkShell {
            buildInputs = with pkgs; [
              python3
              python3Packages.flask
              python3Packages.gunicorn
            python3Packages.toml
            ];
          };
        }
    );
}

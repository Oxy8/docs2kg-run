{
  description = "Python 3.12";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, ... }: 

      let
        system = "x86_64-linux";
        pkgs = import nixpkgs {
          inherit system;
          config = { allowUnfree = true; };
        };
        
        
      in
      {
		  
        devShell.x86_64-linux = pkgs.mkShell {
          packages = [
			pkgs.bashInteractive # needed for vscode integrated terminal to work properly
			pkgs.vscode-fhs
			pkgs.antigravity-fhs
			pkgs.python312
          ];
	
        };
      };
}

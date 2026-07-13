from fertility_popeve.utils.config import load_config


def main():
    cfg = load_config()

    print("Project   :", cfg["project"]["name"])
    print("Version   :", cfg["project"]["version"])
    print("Reference :", cfg["paths"]["reference"])
    print("Assembly  :", cfg["vep"]["assembly"])


if __name__ == "__main__":
    main()

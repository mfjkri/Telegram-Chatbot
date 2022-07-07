import sys
sys.path.append("")

import shutil

import main


if __name__ == "__main__":
    shutil.rmtree("logs")
    main.FRESH_START = True
    main.setup()

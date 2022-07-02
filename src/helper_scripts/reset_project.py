import sys
sys.path.append("")

import shutil

import main

shutil.rmtree("logs")

if __name__ == "__main__":
    main.FRESH_START = True
    main.setup()

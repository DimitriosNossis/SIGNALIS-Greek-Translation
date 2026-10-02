"""Install the SIGNALIS Greek translation.

    python patch.py              patch the game (finds the Steam install automatically)
    python patch.py --restore    put the original game files back
    python patch.py --game "D:\\Games\\SIGNALIS"
"""
import sys

from signalis_greek.patcher import main

if __name__ == "__main__":
    sys.exit(main())

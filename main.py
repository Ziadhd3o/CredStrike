from pyfiglet import Figlet
from time import sleep
import Modules.CredGen
import os

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

f = Figlet(font='ansi_shadow')
while True:
    clear_screen()
    print('\n')
    print(f.renderText('CredStrike'))
    print ("============================================================================")
    print ("||                                                                        ||")
    print ("||    [+] 1. Generate Smart Wordlist                                      ||")
    print ("||    [+] 2. Configure Audit Settings                                     ||")
    print ("||    [+] 3. Start Password Audit                                         ||")
    print ("||    [+] 4. View Audit History                                           ||")
    print ("||    [+] 0. Exit                                                         ||")
    print ("||                                                                        ||")
    print ("============================================================================")
    choice = int(input("[?] Select an option: "))
    match choice:
        case 1: # Member 1
            print("[+] running CredGen")
            sleep(1)
            clear_screen()
            Modules.CredGen.main()
        case 2: # Member 3
            clear_screen()
            print("[+] running CredSafety")
            Modules.CredSafety.main()
        case 3: # Member 2
            clear_screen()
            print("[+] running CredAttack")
            Modules.CredAttack.main()
        case 4: # Member 4
            clear_screen()
            print("[+] running CredHistory")
            Modules.CredHistory.main()
        case 0:
            break

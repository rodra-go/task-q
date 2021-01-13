import pwd, os
from pathlib import Path

print(pwd.getpwuid( os.getuid() ).pw_name)
print(str(Path.home()))

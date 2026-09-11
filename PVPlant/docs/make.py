import subprocess
# from git import Repo
from time import strftime, localtime
import datetime
from datetime import datetime

# oRepo = Repo("..\\")
# gComTag = oRepo.head.commit.hexsha[:7]
# gDirty = "*" if oRepo.is_dirty() else ""
# gComTime = strftime("%a, %d %b %Y, %H:%M:%S", localtime(oRepo.head.commit.committed_date))
subprocess.run(".\\make.bat clean")
f = open('build\\copyright', 'wt')
# f.write(f'{datetime.now().year}, Jonathan Marks, Commit Tag: ' + gComTag + gDirty + ', ' + gComTime)
f.write(f'{datetime.now().year}, Jonathan Marks')  # , Commit Tag: ' + gComTag + gDirty + ', ' + gComTime)
f.close()
subprocess.run(".\\make.bat html")

' ===============================================================================
' StreamYT Pro - Pembuat Shortcut yang Bisa di-PIN ke Taskbar & Start Menu
' ===============================================================================

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
vbsTarget = currentDir & "\Jalankan_Tanpa_CMD.vbs"
icoPath = currentDir & "\app_icon.ico"

' 1. Buat Shortcut di Folder Proyek
shortcutPath1 = currentDir & "\StreamYT Pro.lnk"
Set sc1 = WshShell.CreateShortcut(shortcutPath1)
sc1.TargetPath = "wscript.exe"
sc1.Arguments = """" & vbsTarget & """"
sc1.WorkingDirectory = currentDir
sc1.IconLocation = icoPath & ", 0"
sc1.Description = "StreamYT Pro - YouTube Live Scheduler"
sc1.Save

' 2. Buat Shortcut di Desktop
desktopDir = WshShell.SpecialFolders("Desktop")
shortcutPath2 = desktopDir & "\StreamYT Pro.lnk"
Set sc2 = WshShell.CreateShortcut(shortcutPath2)
sc2.TargetPath = "wscript.exe"
sc2.Arguments = """" & vbsTarget & """"
sc2.WorkingDirectory = currentDir
sc2.IconLocation = icoPath & ", 0"
sc2.Description = "StreamYT Pro - YouTube Live Scheduler"
sc2.Save

WScript.Echo "Shortcut 'StreamYT Pro' berhasil dibuat di Desktop dan di folder ini! Sekarang Anda sudah bisa klik kanan > 'Pin to taskbar' atau 'Pin to Start'."

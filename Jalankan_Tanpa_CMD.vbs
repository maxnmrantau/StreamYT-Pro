' ===============================================================================
' StreamYT Pro - One-Click Silent Background Launcher
' Menjalankan server YouTube streaming 100% di latar belakang (tanpa jendela CMD)
' ===============================================================================

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Pastikan direktori kerja berada di folder script
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir

' Jalankan server Python secara senyap (0 = SW_HIDE, jendela CMD tidak akan muncul)
WshShell.Run "cmd /c python app.py", 0, False

' Berikan jeda 1.5 detik agar server web siap, lalu buka browser
WScript.Sleep 1500
WshShell.Run "http://localhost:8000"

Set WshShell = Nothing
Set fso = Nothing

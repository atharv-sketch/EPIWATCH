Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objShell = CreateObject("WScript.Shell")

baseDir = "C:\Users\silverfang\epiwatch"
objShell.CurrentDirectory = baseDir

WScript.Echo "=== Creating directories ==="

Dim dirs
dirs = Array("backend", "frontend", "data", "notebooks", ".github\workflows")

For Each d In dirs
  fullPath = baseDir & "\" & d
  If Not objFSO.FolderExists(fullPath) Then
    objFSO.CreateFolder(fullPath)
    WScript.Echo "Created: " & d
  Else
    WScript.Echo "Exists: " & d
  End If
Next

WScript.Echo ""
WScript.Echo "=== Creating files ==="

Dim files
files = Array("backend\__init__.py", "backend\data_pipeline.py", "backend\model.py", "backend\api.py", "backend\requirements.txt", "data\.gitkeep", "notebooks\.gitkeep")

For Each f In files
  fullPath = baseDir & "\" & f
  dirPath = objFSO.GetParentFolderName(fullPath)
  
  If Not objFSO.FolderExists(dirPath) Then
    objFSO.CreateFolder(dirPath)
  End If
  
  If Not objFSO.FileExists(fullPath) Then
    Set objFile = objFSO.CreateTextFile(fullPath, True)
    objFile.Close()
    WScript.Echo "Created: " & f
  Else
    WScript.Echo "Exists: " & f
  End If
Next

WScript.Echo ""
WScript.Echo "=== Setup Complete ==="

script "ComfyGames"
######################################################################################
## STACK SCRIPT: "ComfyGames"  (LIB_COMFY/Player, 18 Nov 2026, Opus)
## Comfy Games: the player for the games the ComfyUI nodes build. A copy of the Vibecode3D
## Library (LIB_PUBLIC/launcher/vibe_launcher.livecodescript) that reads no install: it
## finds its games beside itself.
##
## Started with no arguments   the list: every Vibecode3D_Play_*.livecodescript in games/,
##                             by genre (ComfyBricks1 -> Bricks), by name or newest first.
## Started with a game file    that game in its own window (one game per program: the engine
##   ( -game <file>  or         keeps its state in globals). Play starts a second copy of this
##     just <file> )            program this way, so closing the list leaves games running.
##
## Where things are (all found from the program's own folder, never from one PC's paths):
##   games/      the first folder named games (or Games) found walking up from the program:
##               LIB_COMFY/Player/ComfyGames.exe finds LIB_COMFY/games/
##   the engine  Player/Engine/ if it is there (vibe_engine_xt3d, game_player, GameNotes),
##               else from the projects folder above LIB_COMFY, where the engine is made
## Game errors go to %LOCALAPPDATA%\ComfyGames\logs\game_errors.txt.
## The window is made by CG.BuildUI the first time the stack opens, so the stack is just this script.
######################################################################################

constant kW = 960
constant kH = 600
constant kListW = 300

local sRoot, sGames, sOrder, sFilter, sSort, sSel, sTestRoot

-------------------------------------------------------------------- start

on openStack
   -- only for this stack (game windows have their own scripts)
   if the short name of the owner of the target is not the short name of me then pass openStack
   CG.Start
end openStack

on closeStackRequest
   set the destroyStack of me to true
   pass closeStackRequest
end closeStackRequest

command CG.Start
   local tFile, tWhy
   put CG.GameArg() into tFile
   if the environment is "standalone application" then CG.Log "started:" && $# && "arguments: [" & $1 & "] [" & $2 & "] game: [" & tFile & "]"
   if tFile is not empty then
      hide me
      put CG.Play(tFile, true) into tWhy
      if tWhy is not empty then
         CG.Log "could not start" && tFile & ":" && tWhy
         if the environment is "standalone application" then
            answer "Comfy Games could not start this game:" & return & tWhy
            quit
         end if
      end if
      -- this copy only plays the game: once its window is open, the list stack goes
      if the environment is "standalone application" then send "CG.CloseSelf" to me in 3 seconds
      exit CG.Start
   end if
   CG.BuildUI
   CG.Refresh
   send "CG.Place" to me in 100 milliseconds
end CG.Start

-- centre the window once it is on the screen (placed before it opens, it landed up and to the
-- left on a 125% display: 18 Nov). The log keeps what the engine saw.
command CG.Place
   local tBefore
   put the rect of me into tBefore
   set the loc of me to the screenLoc
   if the top of me < 30 then set the top of me to 30
   if the left of me < 0 then set the left of me to 0
   CG.Log "place: screenRect" && the screenRect && "screenLoc" && the screenLoc && "before" && tBefore && "after" && the rect of me
end CG.Place

-- the game file from the command line: -game <file>, or a .livecodescript file
function CG.GameArg
   local tA, tB, tErr
   try
      put $1 into tA
      put $2 into tB
   catch tErr
      return empty
   end try
   if tA is "-game" then return tB
   if tA ends with ".livecodescript" and there is a file tA then return tA
   return empty
end CG.GameArg

-- the folder the program (or, in the IDE, the stack file) is in
function CG.Home
   local tPath
   if the environment is "standalone application" then
      put specialFolderPath("engine") into tPath
   else
      put the effective filename of me into tPath
      set the itemDelimiter to "/"
      replace "\" with "/" in tPath
      delete item -1 of tPath
   end if
   replace "\" with "/" in tPath
   return tPath
end CG.Home

-- LIB_COMFY: the first folder holding games/ (or Games/), from the program's folder upward
function CG.Root
   local tPath
   if sTestRoot is not empty then return sTestRoot
   if sRoot is not empty then return sRoot
   put CG.Home() into tPath
   set the itemDelimiter to "/"
   repeat while the number of items of tPath > 1
      if there is a folder (tPath & "/games") or there is a folder (tPath & "/Games") then
         put tPath into sRoot
         return sRoot
      end if
      delete item -1 of tPath
   end repeat
   return empty
end CG.Root

function CG.GamesFolder
   if CG.Root() is empty then return empty
   if there is a folder (CG.Root() & "/games") then return CG.Root() & "/games"
   return CG.Root() & "/Games"
end CG.GamesFolder

-------------------------------------------------------------------- reading the games

function CG.ReadText pPath
   local tText
   if there is not a file pPath then return empty
   put textDecode(URL ("binfile:" & pPath), "UTF-8") into tText
   replace numToChar(13) & numToChar(10) with return in tText
   replace numToChar(13) with return in tText
   return tText
end CG.ReadText

-- ComfyBricks1 -> Bricks, ComfySquad443265200 -> Squad; anything else -> Other
function CG.Genre pName
   local tG
   if matchText(pName, "^Comfy([A-Za-z]+?)[0-9]*$", tG) then return tG
   return "Other"
end CG.Genre

-- every game in games/ into sGames[name]: file, genre, modified (seconds)
command CG.Scan
   local tDir, tOld, tLine, tFile, tName
   put empty into sGames
   put CG.GamesFolder() into tDir
   if tDir is empty or there is not a folder tDir then exit CG.Scan
   put the defaultFolder into tOld
   set the defaultFolder to tDir
   set the itemDelimiter to comma
   repeat for each line tLine in the detailed files
      put urlDecode(item 1 of tLine) into tFile
      if not (tFile begins with "Vibecode3D_Play_" and tFile ends with ".livecodescript") then next repeat
      put char 17 to -16 of tFile into tName
      put tDir & "/" & tFile into sGames[tName]["file"]
      put CG.Genre(tName) into sGames[tName]["genre"]
      put item 5 of tLine into sGames[tName]["modified"]
      put item 2 of tLine into sGames[tName]["size"]
   end repeat
   set the defaultFolder to tOld
end CG.Scan

-- the genres found, sorted
function CG.Genres
   local tName, tSeen, tOut
   repeat for each key tName in sGames
      if tSeen[sGames[tName]["genre"]] is true then next repeat
      put true into tSeen[sGames[tName]["genre"]]
      put sGames[tName]["genre"] & return after tOut
   end repeat
   delete last char of tOut
   sort lines of tOut
   return tOut
end CG.Genres

-- the names shown for the filter (All games or one genre), by name or newest first
function CG.Ordered pFilter, pSort
   local tName, tOut
   repeat for each key tName in sGames
      if pFilter is not "All games" and pFilter is not empty and sGames[tName]["genre"] is not pFilter then next repeat
      put tName & tab & sGames[tName]["modified"] & return after tOut
   end repeat
   delete last char of tOut
   set the itemDelimiter to tab
   if pSort is "Newest first" then
      sort lines of tOut descending numeric by item 2 of each
   else
      sort lines of tOut by item 1 of each
   end if
   put empty into sOrder
   repeat for each line tName in tOut
      put item 1 of tName & return after sOrder
   end repeat
   delete last char of sOrder
   return sOrder
end CG.Ordered

-- what a game's script header says (as LIB_DEV's GL.Info): about, keys, rules
function CG.Info pName
   local tScript, tInfo, tLine, tText, tMode
   put CG.ReadText(sGames[pName]["file"]) into tScript
   repeat for each line tLine in line 1 to 30 of tScript
      if not (tLine begins with "##") then
         if tLine is not empty then exit repeat
         next repeat
      end if
      if char 3 to 5 of tLine is "###" or tLine is "##" then next repeat
      put char 4 to -1 of tLine into tText
      if word 1 of tText is "CARD" and word 2 of tText is "SCRIPT:" then next repeat
      if word 1 of tText is "CONTROLS" then
         put "keys" into tMode
         delete word 1 of tText
      else if word 1 of tText is "RULES" then
         put "rules" into tMode
         delete word 1 of tText
      end if
      if tMode is empty then put "about" into tMode
      put word 1 to -1 of tText & return after tInfo[tMode]
   end repeat
   return tInfo
end CG.Info

-- a file of the engine: Player/Engine/ first (a copy that travels with the program), then the
-- projects folder above LIB_COMFY, where the engine, the game player and GameNotes are made
function CG.EngineFile pName
   local tPath, tProjects
   if CG.Root() is empty then return empty
   put CG.Root() & "/Player/Engine/" & pName into tPath
   if there is a file tPath then return tPath
   put CG.Root() into tProjects
   set the itemDelimiter to "/"
   delete item -1 of tProjects
   switch pName
      case "vibe_engine_xt3d.livecodescript"
         put tProjects & "/xt3D_Raylib_Livecode_Bridge/testbench/" & pName into tPath
         break
      case "game_player.livecodescript"
         put tProjects & "/LIB_DEV/livecode/" & pName into tPath
         break
      case "GameNotes.livecodescript"
         put tProjects & "/LIB_GAMES/tools/" & pName into tPath
         break
      default
         return empty
   end switch
   if there is a file tPath then return tPath
   return empty
end CG.EngineFile

-- what is wrong with a game (empty: nothing)
function CG.Check pName
   local tOut, tScript
   put CG.ReadText(sGames[pName]["file"]) into tScript
   if tScript is empty then
      put "the file is empty or unreadable" & return after tOut
   else if not matchText(tScript, "(?m)^on Game\.OnStart") then
      put "no Game.OnStart handler: not a Vibecode3D game card script" & return after tOut
   end if
   delete last char of tOut
   return tOut
end CG.Check

-------------------------------------------------------------------- the window

command CG.BuildUI
   local tObj
   set the title of me to "Comfy Games"
   set the resizable of me to false
   set the backgroundColor of me to "18,20,28"
   set the foregroundColor of me to "220,226,240"
   set the textFont of me to "Arial"
   set the textSize of me to 13
   set the width of me to kW
   set the height of me to kH
   set the loc of me to the screenLoc
   if the top of me < 30 then set the top of me to 30
   if there is not a field "Header" of me then
      create field "Header" in card 1 of me
      set the lockText of it to true
      set the opaque of it to false
      set the showBorder of it to false
      set the textSize of it to 20
      set the textStyle of it to "bold"
      set the rect of it to 16, 10, 400, 44
      put "COMFY  GAMES" into it
   end if
   -- the template colours first (owner rule: colour before create; menus take the button colours)
   set the backgroundColor of the templateButton to "40,44,58"
   set the foregroundColor of the templateButton to "220,226,240"
   if there is not a button "Filter" of me then
      create button "Filter" in card 1 of me
      set the style of it to "menu"
      set the menuMode of it to "option"
      set the rect of it to 16, 52, 160, 76
   end if
   if there is not a button "Sort" of me then
      create button "Sort" in card 1 of me
      set the style of it to "menu"
      set the menuMode of it to "option"
      set the text of it to "By name" & return & "Newest first"
      set the label of it to "By name"
      set the rect of it to 168, 52, kListW, 76
   end if
   if there is not a field "Games" of me then
      create field "Games" in card 1 of me
      set the listBehavior of it to true
      set the dontWrap of it to true
      set the lockText of it to true
      set the vScrollbar of it to true
      set the backgroundColor of it to "28,31,42"
      set the hiliteColor of it to "60,110,200"
      set the borderWidth of it to 0
      set the textSize of it to 14
      set the rect of it to 16, 84, kListW, kH - 40
   end if
   if there is not a field "Title" of me then
      create field "Title" in card 1 of me
      set the lockText of it to true
      set the opaque of it to false
      set the showBorder of it to false
      set the textSize of it to 26
      set the textStyle of it to "bold"
      set the rect of it to kListW + 24, 48, kW - 16, 88
   end if
   repeat for each item tObj in "Play,Folder,Verify,Refresh"
      if there is not a button tObj of me then
         create button tObj in card 1 of me
         set the style of it to "standard"
      end if
   end repeat
   set the label of button "Play" of me to "PLAY"
   set the textStyle of button "Play" of me to "bold"
   set the backgroundColor of button "Play" of me to "70,160,90"
   set the rect of button "Play" of me to kListW + 24, 96, kListW + 144, 128
   set the label of button "Folder" of me to "Show Folder"
   set the rect of button "Folder" of me to kListW + 156, 96, kListW + 276, 128
   set the label of button "Verify" of me to "Verify Games"
   set the rect of button "Verify" of me to kListW + 288, 96, kListW + 408, 128
   set the label of button "Refresh" of me to "Refresh"
   set the rect of button "Refresh" of me to kListW + 420, 96, kListW + 540, 128
   if there is not a field "Details" of me then
      create field "Details" in card 1 of me
      set the lockText of it to true
      set the vScrollbar of it to true
      set the backgroundColor of it to "28,31,42"
      set the borderWidth of it to 0
      set the rect of it to kListW + 24, 140, kW - 16, kH - 40
   end if
   if there is not a field "Status" of me then
      create field "Status" in card 1 of me
      set the lockText of it to true
      set the opaque of it to false
      set the showBorder of it to false
      set the textSize of it to 11
      set the rect of it to 16, kH - 32, kW - 16, kH - 8
   end if
end CG.BuildUI

command CG.Refresh
   local tList, tName, tSel
   CG.Scan
   if sFilter is empty then put "All games" into sFilter
   if sSort is empty then put "By name" into sSort
   -- the genre menu is made from the games found (a new kit shows up by itself)
   put "All games" & return & CG.Genres() into tList
   set the text of button "Filter" of me to tList
   if sFilter is not among the lines of tList then put "All games" into sFilter
   set the label of button "Filter" of me to sFilter
   put empty into tList
   repeat for each line tName in CG.Ordered(sFilter, sSort)
      put tName & return after tList
   end repeat
   delete last char of tList
   put tList into field "Games" of me
   if sOrder is empty then
      put empty into field "Title" of me
      if CG.Root() is empty then
         put "No games folder found above" && CG.WinPath(CG.Home()) & "." & return & return & "Put this program in LIB_COMFY/Player, beside LIB_COMFY/games." into field "Details" of me
      else
         put "No games yet in" && CG.WinPath(CG.GamesFolder()) & "." & return & return & "Build one in ComfyUI (Build Game node), then press Refresh." into field "Details" of me
      end if
      CG.Say "0 games"
      exit CG.Refresh
   end if
   put lineOffset(sSel, sOrder) into tSel
   if sSel is empty or tSel is 0 then put 1 into tSel
   CG.Select tSel
   CG.Say the number of lines of sOrder && "games  |  " & the number of lines of CG.Genres() && "genres  |  " & CG.WinPath(CG.GamesFolder())
end CG.Refresh

command CG.Select pLine
   local tName, tInfo, tText
   put line pLine of sOrder into tName
   if tName is empty then exit CG.Select
   put tName into sSel
   set the hilitedLine of field "Games" of me to pLine
   put tName into field "Title" of me
   put CG.Info(tName) into tInfo
   if tInfo["about"] is not empty then put tInfo["about"] & return after tText
   if tInfo["keys"] is not empty then put "CONTROLS" & return & tInfo["keys"] & return after tText
   if tInfo["rules"] is not empty then put "RULES" & return & tInfo["rules"] & return after tText
   put "----" & return after tText
   put "Genre" && sGames[tName]["genre"] & return after tText
   if sGames[tName]["modified"] is a number then
      put "Built" && CG.Date(sGames[tName]["modified"]) & return after tText
   end if
   put CG.WinPath(sGames[tName]["file"]) after tText
   put tText into field "Details" of me
   set the enabled of button "Play" of me to true
end CG.Select

function CG.Date pSeconds
   local tD
   put pSeconds into tD
   convert tD to short date and short time
   return tD
end CG.Date

function CG.WinPath pPath
   if the platform is "Win32" then replace "/" with "\" in pPath
   return pPath
end CG.WinPath

command CG.Say pText
   if there is a field "Status" of me then put pText into field "Status" of me
end CG.Say

on mouseUp
   local tName
   put the short name of the target into tName
   switch tName
      case "Games"
         if the hilitedLine of field "Games" of me is a number then CG.Select the hilitedLine of field "Games" of me
         break
      case "Play"
         CG.PlaySelected
         break
      case "Folder"
         CG.ShowFolder
         break
      case "Verify"
         CG.VerifyAll
         break
      case "Refresh"
         CG.Refresh
         break
   end switch
end mouseUp

on mouseDoubleUp
   if the short name of the target is "Games" then CG.PlaySelected
end mouseDoubleUp

on arrowKey pDir
   local tL
   if the selectedField is not empty then pass arrowKey
   put the hilitedLine of field "Games" of me into tL
   if tL is not a number then put 0 into tL
   if pDir is "down" and tL < the number of lines of sOrder then CG.Select tL + 1
   if pDir is "up" and tL > 1 then CG.Select tL - 1
   if pDir is not "down" and pDir is not "up" then pass arrowKey
end arrowKey

on returnKey
   CG.PlaySelected
end returnKey

on menuPick pItem
   switch the short name of the target
      case "Filter"
         put pItem into sFilter
         CG.Refresh
         break
      case "Sort"
         put pItem into sSort
         CG.Refresh
         break
      default
         pass menuPick
   end switch
end menuPick

-------------------------------------------------------------------- buttons

-- Play: a second copy of this program plays the game (one game per program)
command CG.PlaySelected
   local tWhy
   if sSel is empty then exit CG.PlaySelected
   if the environment is "standalone application" then
      put CG.LaunchCopy(sGames[sSel]["file"]) into tWhy
   else
      put CG.Play(sGames[sSel]["file"], false) into tWhy
   end if
   if tWhy is empty then
      CG.Say "Started" && sSel
   else
      CG.Say "Could not start" && sSel & ":" && tWhy
   end if
end CG.PlaySelected

-- the copy is started with Windows' start command (start "" "<exe>" -game "<file>"), which
-- returns at once, so this list is free to answer the copy's relaunch message
-- (the Vibecode3D Library learnt this on 16 Nov)
function CG.LaunchCopy pFile
   local tExe, tErr, tCmd, tOut
   put the effective filename of me into tExe
   if tExe is empty then return "this program's own file is unknown"
   replace "\" with "/" in pFile
   if the platform is not "Win32" then
      try
         launch CG.WinPath(pFile) with CG.WinPath(tExe)
      catch tErr
         return line 1 of tErr
      end try
      return empty
   end if
   put "start " & quote & quote & space & quote & CG.WinPath(tExe) & quote & " -game " & quote & CG.WinPath(pFile) & quote into tCmd
   CG.Log "play:" && tCmd
   set the hideConsoleWindows to true
   try
      put shell(tCmd) into tOut
   catch tErr
      return line 1 of tErr
   end try
   if the result is not empty and the result is not 0 then return "start said:" && the result && tOut
   return empty
end CG.LaunchCopy

-- a game copy, 3 seconds after its start: the list stack closes. When no game window is
-- open, the copy did nothing: it says so in the log and quits instead of lingering
command CG.CloseSelf
   local tStack, tOpen
   put false into tOpen
   repeat for each line tStack in the openStacks
      if tStack begins with "Play " and the visible of stack tStack then put true into tOpen
   end repeat
   if not tOpen then
      CG.Log "no game window 3 seconds after the start: this copy quits"
      set the destroyStack of me to true
      quit
   end if
   set the destroyStack of me to true
   close me
end CG.CloseSelf

-- a second copy of this program was started: let it run (it is a game, or another list)
on relaunch
   pass relaunch
end relaunch

command CG.ShowFolder
   local tErr
   if CG.GamesFolder() is empty then exit CG.ShowFolder
   try
      launch document CG.WinPath(CG.GamesFolder())
   catch tErr
      CG.Say "Could not open the folder:" && line 1 of tErr
   end try
end CG.ShowFolder

command CG.VerifyAll
   local tName, tBad, tN, tOut, tWhy, tF
   CG.Scan
   put 0 into tN
   put 0 into tBad
   repeat for each item tF in "vibe_engine_xt3d.livecodescript,game_player.livecodescript"
      if CG.EngineFile(tF) is empty then
         add 1 to tBad
         put "The engine: no" && tF && "in Player/Engine or the projects folder" & return after tOut
      end if
   end repeat
   repeat for each key tName in sGames
      add 1 to tN
      put CG.Check(tName) into tWhy
      if tWhy is empty then next repeat
      add 1 to tBad
      replace return with "; " in tWhy
      put tName & ":" && tWhy & return after tOut
   end repeat
   sort lines of tOut
   put "Verify Games" into field "Title" of me
   if tBad is 0 then
      put tN && "games checked: all readable, and the engine is there." into field "Details" of me
   else
      put tN && "games checked," && tBad && "problems:" & return & return & tOut into field "Details" of me
   end if
   CG.Say "Verified" && tN && "games," && tBad && "problems"
end CG.VerifyAll

-------------------------------------------------------------------- playing

-- a game file in its own window (as LIB_DEV's GL.Open). pQuitOnClose: closing the window
-- ends the program. Returns empty, or why it could not.
function CG.Play pFile, pQuitOnClose
   local tScript, tEngine, tPlayer, tNotes, tName, tStack, tErr, tLevels, tAt
   global gV3DSkin
   replace "\" with "/" in pFile
   put CG.ReadText(pFile) into tScript
   if tScript is empty then return "no game script:" && pFile
   put CG.EngineFile("vibe_engine_xt3d.livecodescript") into tEngine
   if tEngine is empty then return "no engine (vibe_engine_xt3d.livecodescript) in Player/Engine or the projects folder"
   put CG.ReadText(CG.EngineFile("game_player.livecodescript")) into tPlayer
   if tPlayer is empty then return "no game player (game_player.livecodescript) in Player/Engine or the projects folder"
   try
      if not ("VibeEngineXt3d" is among the lines of the stacksInUse) then start using stack tEngine
   catch tErr
      return "the engine did not load:" && line 1 of tErr
   end try
   put CG.EngineFile("GameNotes.livecodescript") into tNotes
   if tNotes is not empty and not ("GameNotes" is among the lines of the frontScripts) then
      try
         start using stack tNotes
         insert script of stack "GameNotes" into front
      catch tErr
      end try
   end if
   put empty into gV3DSkin
   -- Vibecode3D_Play_<Name>.livecodescript: the card is "Play.<Name>"
   set the itemDelimiter to "/"
   put item -1 of pFile into tName
   if tName begins with "Vibecode3D_Play_" then delete char 1 to 16 of tName
   set the itemDelimiter to "."
   put item 1 of tName into tName
   put "Play" && tName into tStack
   if there is a stack tStack then close stack tStack
   lock messages
   create invisible stack tStack
   unlock messages
   set the defaultStack to tStack
   set the script of stack tStack to tPlayer
   if the result is not empty then
      put the result into tErr
      delete stack tStack
      return "the game player does not compile:" && tErr
   end if
   set the name of card 1 of stack tStack to "Play." & tName
   set the script of card 1 of stack tStack to tScript
   if the result is not empty then
      put the result into tErr
      delete stack tStack
      return tName && "does not compile:" && tErr
   end if
   -- the level menu: <Prefix>.StartLevel, 5 levels unless the header says otherwise
   put 0 into tLevels
   repeat for each line tAt in tScript
      if word 1 of tAt is "on" and word 2 of tAt ends with ".StartLevel" then
         set the uPrefix of stack tStack to char 1 to -12 of word 2 of tAt
         put 5 into tLevels
         exit repeat
      end if
   end repeat
   if tLevels > 0 and matchText(line 1 to 30 of tScript, "(?i)\b([0-9]+) levels", tAt) then
      if tAt is an integer and tAt > 0 and tAt < 100 then put tAt into tLevels
   end if
   set the uGame of stack tStack to tName
   set the uScriptFile of stack tStack to pFile
   set the uLevels of stack tStack to tLevels
   set the uQuitOnClose of stack tStack to (pQuitOnClose is true)
   set the uErrorFile of stack tStack to CG.ErrorFile()
   set the backgroundColor of stack tStack to "0,0,0"
   set the resizable of stack tStack to false
   set the destroyStack of stack tStack to true
   set the title of stack tStack to tName && "|  Comfy Games  |  Escape pauses, ... top right: Reset, Levels, Quit"
   set the rect of stack tStack to CG.WindowRect()
   try
      show stack tStack
      go stack tStack
   catch tErr
      return "the window did not open:" && line 1 of tErr
   end try
   send "Player.Start" to stack tStack in 50 milliseconds
   return empty
end CG.Play

function CG.WindowRect
   local tL, tT
   put max(0, (item 3 of the screenRect - 900) div 2) into tL
   put max(30, (item 4 of the screenRect - 600) div 2) into tT
   return tL, tT, tL + 900, tT + 600
end CG.WindowRect

-- %LOCALAPPDATA%\ComfyGames\logs\ (this machine only, safe to lose), else the temporary folder
function CG.LogFolder
   local tDir, tErr
   put $LOCALAPPDATA into tDir
   if tDir is empty then
      put specialFolderPath("temporary") into tDir
   else
      replace "\" with "/" in tDir
      put "/ComfyGames" after tDir
      try
         if there is not a folder tDir then create folder tDir
         put "/logs" after tDir
         if there is not a folder tDir then create folder tDir
      catch tErr
         put specialFolderPath("temporary") into tDir
      end try
   end if
   return tDir
end CG.LogFolder

function CG.ErrorFile
   return CG.LogFolder() & "/game_errors.txt"
end CG.ErrorFile

command CG.Log pText
   local tFile, tText, tErr
   try
      put CG.LogFolder() & "/player.txt" into tFile
      put CG.ReadText(tFile) into tText
      put the short date && the long time & tab & pText & return after tText
      put textEncode(tText, "UTF-8") into URL ("binfile:" & tFile)
   catch tErr
   end try
end CG.Log

-------------------------------------------------------------------- test hooks

command CG.TestRoot pPath
   put pPath into sTestRoot
end CG.TestRoot

function CG.Count
   return the number of lines of sOrder
end CG.Count

function CG.Field pName
   return field pName of me
end CG.Field

function CG.SelName
   return sSel
end CG.SelName

function CG.FileOf pName
   return sGames[pName]["file"]
end CG.FileOf

function CG.SetView pFilter, pSort
   put pFilter into sFilter
   put pSort into sSort
   CG.Refresh
   return sOrder
end CG.SetView

script "ComfyGames"
######################################################################################
## STACK SCRIPT: "ComfyGames"  (LIB_COMFY/Player; 18 Nov 2026 player, 19-20 Nov 2026 app, Opus)
## Engine 1 (pure xTalk Vibecode3D) host: plays the game scripts the ComfyUI nodes build.
## Comfy Games: pick a genre, pick a game, PLAY. Rate games with stars, sort by stars or date,
## make a new game of a genre with one button (no ComfyUI needed), or open the genre's starter
## workflow in ComfyUI when it is running. Kept apart from the hand-made Vibecode3D Library
## (owner, 18 Nov). Its play code is the Library's (LIB_PUBLIC/launcher/vibe_launcher).
##
## Started with no arguments   the window: genres (left), games of the genre (middle), the game
##                             (right): stars, PLAY, Make a new one, Open in ComfyUI.
## Started with a game file    that game in its own window (one game per program: the engine
##   ( -game <file>  or         keeps its state in globals). PLAY starts a second copy of this
##     just <file> )            program this way, so closing the list leaves games running.
##
## Where things are (all found from the program's own folder, never from one PC's paths):
##   LIB_COMFY   the first folder above the program holding games/ (or Games/)
##   genres      LIB_COMFY/genres.tsv (genre, maker, about, starter workflow); a genre found
##               only in game files is listed too. A game's genre: its "-- comfy: genre=..."
##               header line (Build Game writes it), else its file name (ComfyBricks1 -> Bricks)
##   new games   LIB_COMFY/tools/make_game.py builds one (any Python 3); they go into games/,
##               or, when games/ is read-only (an installed copy), Data/Games/ComfyGames/games
##   ratings     Data/Games/ComfyGames/ratings.tsv in the player's Data folder (LIB_DATA rules)
##   the engine  Player/Engine/ if it is there, else the projects folder above LIB_COMFY
## Logs and game errors: %LOCALAPPDATA%\ComfyGames\logs\.
## The window is made by CG.BuildUI the first time the stack opens, so the stack is just this script.
######################################################################################

constant kW = 960
constant kH = 600
constant kComfyURL = "http://127.0.0.1:8188"
-- the window title's role tag (stack title rule): empty it for the public release
constant kTitleTag = "FOR OWNER | "

local sRoot, sGames, sOrder, sGenre, sSort, sSel, sTestRoot, sTestData
local sGenreList, sGenreRows, sHead, sRatings, sRatingsRead, sPython, sDataFolder, sTestBuild

-------------------------------------------------------------------- start

on openStack
   -- only for this stack (game windows have their own scripts)
   if the short name of the owner of the target is not the short name of me then pass openStack
   CG.Start
end openStack

-- back from ComfyUI (or anywhere): read games/ again, so new builds show up at once
on resumeStack
   if the short name of the owner of the target is not the short name of me then pass resumeStack
   if there is a field "Games" of me and the visible of me then CG.Refresh
end resumeStack

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

-- owner rule: stacks open with their top left at 200,32 (kept on the screen when it is small)
command CG.Place
   local tL, tT
   put 200 into tL
   put 32 into tT
   if item 3 of the screenRect > 0 then
      put max(0, min(tL, item 3 of the screenRect - kW)) into tL
      put max(0, min(tT, item 4 of the screenRect - kH - 40)) into tT
   end if
   set the topLeft of me to tL, tT
   CG.Log "place: screenRect" && the screenRect && "rect" && the rect of me
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

-------------------------------------------------------------------- the player's Data folder

-- Data/Games/ComfyGames: through LIB_DATA when it is there (the Data folder may have moved),
-- else Documents/Data, LIB_DATA's default. Made if missing.
function CG.DataFolder
   local tLib, tDir, tErr
   if sTestData is not empty then
      put sTestData & "/Games/ComfyGames" into tDir
      CG.MakeFolders tDir
      return tDir
   end if
   if sDataFolder is not empty then return sDataFolder
   put CG.EngineFile("lib_data.livecodescript") into tLib
   if tLib is not empty then
      try
         if not ("LIB_DATA" is among the lines of the stacksInUse) then start using stack tLib
         put Data.Folder("Games", "ComfyGames") into tDir
      catch tErr
         put empty into tDir
      end try
   end if
   if tDir is empty then
      put specialFolderPath("documents") & "/Data/Games/ComfyGames" into tDir
      replace "\" with "/" in tDir
      CG.MakeFolders tDir
   end if
   put tDir into sDataFolder
   return tDir
end CG.DataFolder

command CG.MakeFolders pPath
   local tSoFar, tPart, tErr
   set the itemDelimiter to "/"
   repeat for each item tPart in pPath
      if tSoFar is empty and tPart is empty then
         put "/" into tSoFar
         next repeat
      end if
      if tSoFar is empty or tSoFar is "/" then
         put tSoFar & tPart into tSoFar
      else
         put tSoFar & "/" & tPart into tSoFar
      end if
      if tSoFar ends with ":" then next repeat
      try
         if there is not a folder tSoFar then create folder tSoFar
      catch tErr
      end try
   end repeat
end CG.MakeFolders

-- where Make a new one writes: games/ when it can be written to (this PC's LIB_COMFY), else the
-- player's Data folder (an installed, read-only copy)
function CG.BuildFolder
   local tDir, tProbe
   if sTestBuild is not empty then return sTestBuild
   put CG.GamesFolder() into tDir
   if tDir is not empty then
      put tDir & "/.comfygames_write_test" into tProbe
      put "x" into URL ("binfile:" & tProbe)
      if the result is empty and there is a file tProbe then
         delete file tProbe
         return tDir
      end if
   end if
   put CG.DataFolder() & "/games" into tDir
   CG.MakeFolders tDir
   return tDir
end CG.BuildFolder

-- the folders games are read from: games/, then the player's own builds when they are elsewhere
function CG.GameFolders
   local tOut, tOwn
   put CG.GamesFolder() into tOut
   put CG.DataFolder() & "/games" into tOwn
   if tOwn is not tOut and there is a folder tOwn then put return & tOwn after tOut
   if sTestBuild is not empty and not (sTestBuild is among the lines of tOut) then put return & sTestBuild after tOut
   return tOut
end CG.GameFolders

-------------------------------------------------------------------- genres

-- genres.tsv: genre <tab> maker <tab> about <tab> workflow, in the order they are offered
command CG.ReadGenres
   local tLine, tG
   put empty into sGenreRows
   put empty into sGenreList
   set the itemDelimiter to tab
   repeat for each line tLine in CG.ReadText(CG.Root() & "/genres.tsv")
      if tLine is empty or char 1 of tLine is "#" then next repeat
      put item 1 of tLine into tG
      if tG is empty or sGenreRows[tG]["maker"] is not empty then next repeat
      put item 2 of tLine into sGenreRows[tG]["maker"]
      put item 3 of tLine into sGenreRows[tG]["about"]
      put item 4 of tLine into sGenreRows[tG]["workflow"]
      put tG & return after sGenreList
   end repeat
   delete last char of sGenreList
end CG.ReadGenres

-- ComfyBricks1 -> Bricks, ComfySquad443265200 -> Squad; anything else -> Other
function CG.Genre pName
   local tG
   if matchText(pName, "^Comfy([A-Za-z]+?)[0-9]*$", tG) then return tG
   return "Other"
end CG.Genre

-- the genres in the menu: genres.tsv's order, then any other genre the games have, Other last
function CG.Genres
   local tName, tSeen, tOut, tExtra, tG
   repeat for each line tG in sGenreList
      put true into tSeen[tG]
      put tG & return after tOut
   end repeat
   repeat for each key tName in sGames
      put sGames[tName]["genre"] into tG
      if tSeen[tG] is true then next repeat
      put true into tSeen[tG]
      if tG is not "Other" then put tG & return after tExtra
   end repeat
   sort lines of tExtra
   put tExtra after tOut
   if tSeen["Other"] is true and not ("Other" is among the lines of sGenreList) then put "Other" & return after tOut
   delete last char of tOut
   return tOut
end CG.Genres

function CG.GenreCount pGenre
   local tName, tN
   put 0 into tN
   repeat for each key tName in sGames
      if pGenre is "All games" or sGames[tName]["genre"] is pGenre then add 1 to tN
   end repeat
   return tN
end CG.GenreCount

-------------------------------------------------------------------- reading the games

function CG.ReadText pPath
   local tText
   if there is not a file pPath then return empty
   put textDecode(URL ("binfile:" & pPath), "UTF-8") into tText
   replace numToChar(13) & numToChar(10) with return in tText
   replace numToChar(13) with return in tText
   return tText
end CG.ReadText

-- the "-- comfy: genre=<g> seed=<n> built=<iso>" line under a game's header (Build Game and
-- tools/make_game.py write it): genre <tab> seed <tab> built, read once per file version
function CG.Head pFile, pModified
   local tText, tLine, tOut, tWord
   if sHead[pFile]["modified"] is pModified and pModified is not empty then return sHead[pFile]["line"]
   put CG.ReadText(pFile) into tText
   repeat for each line tLine in line 1 to 200 of tText
      if not (tLine begins with "-- comfy:") then next repeat
      put tab & tab into tOut
      set the itemDelimiter to tab
      repeat for each word tWord in char 10 to -1 of tLine
         if tWord begins with "genre=" then put char 7 to -1 of tWord into item 1 of tOut
         if tWord begins with "seed=" then put char 6 to -1 of tWord into item 2 of tOut
         if tWord begins with "built=" then put char 7 to -1 of tWord into item 3 of tOut
      end repeat
      exit repeat
   end repeat
   put pModified into sHead[pFile]["modified"]
   put tOut into sHead[pFile]["line"]
   return tOut
end CG.Head

-- 2026-11-19T23:11:56 -> seconds (this PC's clock); empty when it is not that shape
function CG.IsoSeconds pIso
   local tY, tMo, tD, tH, tMi, tS, tItems
   if not matchText(pIso, "^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})", tY, tMo, tD, tH, tMi, tS) then return empty
   put tY, tMo + 0, tD + 0, tH + 0, tMi + 0, tS + 0, 1 into tItems
   convert tItems from dateItems to seconds
   return tItems
end CG.IsoSeconds

-- every game into sGames[name]: file, genre, seed, built (seconds), modified, size
command CG.Scan
   local tDir, tOld, tLine, tFile, tName, tHead, tBuilt
   put empty into sGames
   put the defaultFolder into tOld
   repeat for each line tDir in CG.GameFolders()
      if tDir is empty or there is not a folder tDir then next repeat
      set the defaultFolder to tDir
      set the itemDelimiter to comma
      repeat for each line tLine in the detailed files
         set the itemDelimiter to comma
         put urlDecode(item 1 of tLine) into tFile
         if not (tFile begins with "Vibecode3D_Play_" and tFile ends with ".livecodescript") then next repeat
         put char 17 to -16 of tFile into tName
         -- a name in both folders: the first one (games/) is kept
         if sGames[tName]["file"] is not empty then next repeat
         put tDir & "/" & tFile into sGames[tName]["file"]
         put item 5 of tLine into sGames[tName]["modified"]
         put item 2 of tLine into sGames[tName]["size"]
         put CG.Head(tDir & "/" & tFile, item 5 of tLine) into tHead
         set the itemDelimiter to tab
         if item 1 of tHead is not empty then
            put item 1 of tHead into sGames[tName]["genre"]
         else
            put CG.Genre(tName) into sGames[tName]["genre"]
         end if
         put item 2 of tHead into sGames[tName]["seed"]
         put CG.IsoSeconds(item 3 of tHead) into tBuilt
         if tBuilt is empty then put sGames[tName]["modified"] into tBuilt
         put tBuilt into sGames[tName]["built"]
      end repeat
   end repeat
   set the defaultFolder to tOld
end CG.Scan

-- the names shown for a genre ("All games" for every one), sorted:
--   Stars   most stars first, newest first among the same stars (the default)
--   Newest  date built, newest first
--   Name    A-Z
function CG.Ordered pGenre, pSort
   local tName, tOut, tStars
   CG.LoadRatings
   repeat for each key tName in sGames
      if pGenre is not "All games" and pGenre is not empty and sGames[tName]["genre"] is not pGenre then next repeat
      put sRatings[tName] into tStars
      if tStars is not an integer then put 0 into tStars
      put tName & tab & sGames[tName]["built"] & tab & tStars & return after tOut
   end repeat
   delete last char of tOut
   set the itemDelimiter to tab
   sort lines of tOut by item 1 of each
   if pSort is "Newest" or pSort is "Stars" then sort lines of tOut descending numeric by item 2 of each
   -- sort is stable: the same stars stay newest first
   if pSort is "Stars" then sort lines of tOut descending numeric by item 3 of each
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
      else if word 1 of tText is "REMIX" then
         exit repeat
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
      case "lib_data.livecodescript"
         put tProjects & "/LIB_DATA/livecode/" & pName into tPath
         break
      case "lib_audio.livecodescript"
         put tProjects & "/LIB_AUDIO/livecode/" & pName into tPath
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

-------------------------------------------------------------------- star ratings

-- ratings.tsv: game <tab> stars (1-5) <tab> when; a game with no line has 0 stars
command CG.LoadRatings
   local tLine
   if sRatingsRead is true then exit CG.LoadRatings
   put empty into sRatings
   set the itemDelimiter to tab
   repeat for each line tLine in CG.ReadText(CG.RatingsFile())
      if tLine is empty or char 1 of tLine is "#" then next repeat
      if item 2 of tLine is an integer and item 2 of tLine > 0 then put min(5, item 2 of tLine) into sRatings[item 1 of tLine]
   end repeat
   put true into sRatingsRead
end CG.LoadRatings

function CG.RatingsFile
   return CG.DataFolder() & "/ratings.tsv"
end CG.RatingsFile

function CG.Rating pName
   CG.LoadRatings
   if sRatings[pName] is an integer then return sRatings[pName]
   return 0
end CG.Rating

-- set a game's stars (0 takes them away) and write the file at once
command CG.SetRating pName, pStars
   local tText, tName, tKeys, tWhen
   if pName is empty or pStars is not an integer then exit CG.SetRating
   CG.LoadRatings
   put max(0, min(5, pStars)) into pStars
   if pStars is 0 then
      delete variable sRatings[pName]
   else
      put pStars into sRatings[pName]
   end if
   put the keys of sRatings into tKeys
   sort lines of tKeys
   put "# Comfy Games star ratings: game <tab> stars (1-5) <tab> when. Kept by the Comfy Games app." & return into tText
   put the seconds into tWhen
   convert tWhen to dateItems
   put format("%04d-%02d-%02d", item 1 of tWhen, item 2 of tWhen, item 3 of tWhen) into tWhen
   repeat for each line tName in tKeys
      put tName & tab & sRatings[tName] & tab & tWhen & return after tText
   end repeat
   put textEncode(tText, "UTF-8") into URL ("binfile:" & CG.RatingsFile())
   if the result is not empty then CG.Say "Could not save the stars:" && the result
end CG.SetRating

-- U+2726 / U+2727 (LIB_UNICODE registry: a rating star given / not given)
function CG.Stars pN
   local tOut, i
   repeat with i = 1 to 5
      if i <= pN then
         put numToCodepoint(10022) after tOut
      else
         put numToCodepoint(10023) after tOut
      end if
   end repeat
   return tOut
end CG.Stars

-------------------------------------------------------------------- the window

-- owner rule: colour the template before every create (a menu's list takes the button colours)
command CG.Template pKind
   switch pKind
      case "button"
         reset the templateButton
         set the backgroundColor of the templateButton to "40,44,58"
         set the foregroundColor of the templateButton to "220,226,240"
         set the textColor of the templateButton to "220,226,240"
         set the borderColor of the templateButton to "70,76,96"
         set the hiliteColor of the templateButton to "60,110,200"
         break
      case "field"
         reset the templateField
         set the backgroundColor of the templateField to "28,31,42"
         set the foregroundColor of the templateField to "220,226,240"
         set the textColor of the templateField to "220,226,240"
         set the borderColor of the templateField to "70,76,96"
         set the hiliteColor of the templateField to "60,110,200"
         break
   end switch
end CG.Template

command CG.NewField pName, pRect, pList
   if there is not a field pName of me then
      CG.Template "field"
      create field pName in card 1 of me
   end if
   set the lockText of field pName of me to true
   set the dontWrap of field pName of me to (pList is true)
   set the listBehavior of field pName of me to (pList is true)
   set the vScrollbar of field pName of me to (pList is true)
   set the borderWidth of field pName of me to 0
   set the rect of field pName of me to pRect
end CG.NewField

command CG.NewButton pName, pLabel, pRect
   if there is not a button pName of me then
      CG.Template "button"
      create button pName in card 1 of me
      set the style of it to "standard"
   end if
   set the label of button pName of me to pLabel
   set the rect of button pName of me to pRect
end CG.NewButton

command CG.NewText pName, pRect, pSize, pStyle
   if there is not a field pName of me then
      CG.Template "field"
      create field pName in card 1 of me
      set the lockText of it to true
      set the opaque of it to false
      set the showBorder of it to false
      set the dontWrap of it to true
   end if
   set the textSize of field pName of me to pSize
   set the textStyle of field pName of me to pStyle
   set the rect of field pName of me to pRect
end CG.NewText

command CG.BuildUI
   local i, tX
   set the title of me to kTitleTag & "Comfy Games"
   set the resizable of me to false
   set the backgroundColor of me to "18,20,28"
   set the foregroundColor of me to "220,226,240"
   set the textFont of me to "Arial"
   set the textSize of me to 13
   set the width of me to kW
   set the height of me to kH
   -- an older window (18 Nov player) had menus here: the new layout replaces them
   if there is a button "Filter" of me then delete button "Filter" of me
   if there is a button "Sort" of me then delete button "Sort" of me
   CG.NewText "Header", "16,8,300,44", 22, "bold"
   put "COMFY  GAMES" into field "Header" of me
   CG.NewText "Hint", "300,16,944,40", 13, "plain"
   set the textColor of field "Hint" of me to "150,160,185"
   put "Pick a genre, pick a game, PLAY.   Make a new one any time: it is ready in a second." into field "Hint" of me
   -- left: genres
   CG.NewText "GenresLabel", "16,48,176,70", 12, "bold"
   put "GENRE" into field "GenresLabel" of me
   CG.NewField "Genres", "16,72,176," & kH - 40, true
   set the textSize of field "Genres" of me to 16
   -- middle: games and how they are sorted
   CG.NewText "GamesLabel", "184,48,250,70", 12, "bold"
   put "GAMES" into field "GamesLabel" of me
   CG.NewButton "SortStars", "Best rated", "250,48,322,70"
   CG.NewButton "SortNewest", "Newest", "326,48,388,70"
   CG.NewButton "SortName", "A-Z", "392,48,456,70"
   CG.NewField "Games", "184,72,456," & kH - 40, true
   set the textSize of field "Games" of me to 14
   if the platform is "Win32" then set the textFont of field "Games" of me to "Segoe UI Symbol"
   -- right: the game
   CG.NewText "Title", "468,48,944,84", 24, "bold"
   put 468 into tX
   repeat with i = 1 to 5
      CG.NewButton "Star" & i, numToCodepoint(10023), tX & ",90," & tX + 34 & ",120"
      set the textSize of button ("Star" & i) of me to 20
      set the showBorder of button ("Star" & i) of me to false
      set the opaque of button ("Star" & i) of me to false
      set the textColor of button ("Star" & i) of me to "255,205,80"
      if the platform is "Win32" then set the textFont of button ("Star" & i) of me to "Segoe UI Symbol"
      add 36 to tX
   end repeat
   CG.NewText "StarWords", "656,94,944,118", 12, "plain"
   set the textColor of field "StarWords" of me to "150,160,185"
   CG.NewButton "Play", "PLAY", "468,128,588,162"
   set the textStyle of button "Play" of me to "bold"
   set the textSize of button "Play" of me to 16
   set the backgroundColor of button "Play" of me to "70,160,90"
   CG.NewButton "Make", "Make a new one", "596,128,780,162"
   set the backgroundColor of button "Make" of me to "60,90,150"
   CG.NewButton "Comfy", "Open in ComfyUI", "788,128,944,162"
   CG.NewField "Details", "468,172,944," & kH - 76, false
   set the vScrollbar of field "Details" of me to true
   set the dontWrap of field "Details" of me to false
   CG.NewButton "Folder", "Show Folder", "468," & kH - 68 & ",588," & kH - 44
   CG.NewButton "Verify", "Verify Games", "596," & kH - 68 & ",716," & kH - 44
   CG.NewButton "Refresh", "Refresh", "724," & kH - 68 & ",844," & kH - 44
   CG.NewText "Status", "16," & kH - 32 & "," & kW - 16 & "," & kH - 8, 11, "plain"
   if the platform is not "Win32" then put "If this Comfy Games program is on Linux: Make a new one runs python3." into field "Status" of me
end CG.BuildUI

command CG.Refresh
   local tList, tName, tSel, tG, tLine
   put false into sRatingsRead
   CG.ReadGenres
   CG.Scan
   if sGenre is empty then put "All games" into sGenre
   if sSort is empty then put "Stars" into sSort
   if sGenre is not "All games" and not (sGenre is among the lines of CG.Genres()) then put "All games" into sGenre
   -- genres with their counts; the line number is the genre's place in "All games" & CG.Genres()
   put "All games" & tab & CG.GenreCount("All games") & return into tList
   repeat for each line tG in CG.Genres()
      put tG & tab & CG.GenreCount(tG) & return after tList
   end repeat
   delete last char of tList
   set the tabStops of field "Genres" of me to 120
   put tList into field "Genres" of me
   put 0 into tLine
   repeat for each line tG in ("All games" & return & CG.Genres())
      add 1 to tLine
      if tG is sGenre then set the hilitedLine of field "Genres" of me to tLine
   end repeat
   -- the sort buttons: the one in use is lit
   set the backgroundColor of button "SortStars" of me to CG.Lit(sSort is "Stars")
   set the backgroundColor of button "SortNewest" of me to CG.Lit(sSort is "Newest")
   set the backgroundColor of button "SortName" of me to CG.Lit(sSort is "Name")
   if sGenre is "All games" then
      set the label of button "Make" of me to "Make a new one"
      set the enabled of button "Comfy" of me to false
   else
      set the label of button "Make" of me to "Make a new" && sGenre
      set the enabled of button "Comfy" of me to (sGenreRows[sGenre]["workflow"] is not empty)
   end if
   put empty into tList
   repeat for each line tName in CG.Ordered(sGenre, sSort)
      put CG.Stars(CG.Rating(tName)) & "   " & tName & return after tList
   end repeat
   delete last char of tList
   put tList into field "Games" of me
   if sOrder is empty then
      CG.ShowNothing
      exit CG.Refresh
   end if
   set the wholeMatches to true
   put lineOffset(sSel, sOrder) into tSel
   if sSel is empty or tSel is 0 or line tSel of sOrder is not sSel then put 1 into tSel
   CG.Select tSel
   CG.Say the number of lines of sOrder && "games  |  " & CG.WinPath(CG.GamesFolder()) & "  |  stars in" && CG.WinPath(CG.RatingsFile())
end CG.Refresh

function CG.Lit pOn
   if pOn then return "60,110,200"
   return "40,44,58"
end CG.Lit

-- no game to show: say why and what to do
command CG.ShowNothing
   local tText
   put empty into sSel
   put empty into field "Title" of me
   put empty into field "StarWords" of me
   CG.ShowStars 0
   set the enabled of button "Play" of me to false
   if CG.Root() is empty then
      put "No games folder found above" && CG.WinPath(CG.Home()) & "." & return & return & "Put this program in LIB_COMFY/Player, beside LIB_COMFY/games." into tText
   else if sGenre is "All games" then
      put "No games yet." & return & return & "Press Make a new one: a game is made in a second, no ComfyUI needed." into tText
   else
      put "No" && sGenre && "games yet." & return & return & sGenreRows[sGenre]["about"] & return & return & "Press Make a new" && sGenre & ": one is made in a second, no ComfyUI needed." into tText
   end if
   put tText into field "Details" of me
   CG.Say "0 games"
end CG.ShowNothing

command CG.ShowStars pN
   local i
   repeat with i = 1 to 5
      if i <= pN then
         set the label of button ("Star" & i) of me to numToCodepoint(10022)
      else
         set the label of button ("Star" & i) of me to numToCodepoint(10023)
      end if
   end repeat
   if sSel is empty then exit CG.ShowStars
   if pN is 0 then
      put "not rated: click a star (or press 1-5)" into field "StarWords" of me
   else
      put pN && "of 5 (click it again to take it away)" into field "StarWords" of me
   end if
end CG.ShowStars

command CG.Select pLine
   local tName, tInfo, tText, tG
   put line pLine of sOrder into tName
   if tName is empty then exit CG.Select
   put tName into sSel
   set the hilitedLine of field "Games" of me to pLine
   put tName into field "Title" of me
   CG.ShowStars CG.Rating(tName)
   put CG.Info(tName) into tInfo
   if tInfo["about"] is not empty then put tInfo["about"] & return after tText
   if tInfo["keys"] is not empty then put "CONTROLS" & return & tInfo["keys"] & return after tText
   if tInfo["rules"] is not empty then put "RULES" & return & tInfo["rules"] & return after tText
   put "----" & return after tText
   put sGames[tName]["genre"] into tG
   put "Genre" && tG after tText
   if sGenreRows[tG]["about"] is not empty then put ":" && sGenreRows[tG]["about"] after tText
   put return after tText
   if sGames[tName]["seed"] is not empty then put "Seed" && sGames[tName]["seed"] & return after tText
   if sGames[tName]["built"] is a number then put "Built" && CG.Date(sGames[tName]["built"]) & return after tText
   put CG.WinPath(sGames[tName]["file"]) after tText
   put tText into field "Details" of me
   set the enabled of button "Play" of me to true
end CG.Select

-- a genre picked in the left list (line 1 is All games)
command CG.PickGenre pLine
   local tG
   put line pLine of ("All games" & return & CG.Genres()) into tG
   if tG is empty then exit CG.PickGenre
   put tG into sGenre
   CG.Refresh
end CG.PickGenre

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
   if tName begins with "Star" and char 5 of tName is an integer then
      CG.ClickStar char 5 of tName
      exit mouseUp
   end if
   switch tName
      case "Genres"
         if the hilitedLine of field "Genres" of me is a number then CG.PickGenre the hilitedLine of field "Genres" of me
         break
      case "Games"
         if the hilitedLine of field "Games" of me is a number then CG.Select the hilitedLine of field "Games" of me
         break
      case "SortStars"
         put "Stars" into sSort
         CG.Refresh
         break
      case "SortNewest"
         put "Newest" into sSort
         CG.Refresh
         break
      case "SortName"
         put "Name" into sSort
         CG.Refresh
         break
      case "Play"
         CG.PlaySelected
         break
      case "Make"
         CG.MakeClicked
         break
      case "Comfy"
         CG.ComfyClicked
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

-- a star clicked: that many stars; the same star again takes them away
command CG.ClickStar pN
   if sSel is empty then exit CG.ClickStar
   if CG.Rating(sSel) is pN then put 0 into pN
   CG.SetRating sSel, pN
   CG.Refresh
   CG.Say sSel && "has" && pN && "stars"
end CG.ClickStar

on arrowKey pDir
   local tL
   if the selectedField is not empty then pass arrowKey
   put the hilitedLine of field "Games" of me into tL
   if tL is not a number then put 0 into tL
   if pDir is "down" and tL < the number of lines of sOrder then CG.Select tL + 1
   if pDir is "up" and tL > 1 then CG.Select tL - 1
   if pDir is not "down" and pDir is not "up" then pass arrowKey
end arrowKey

-- 0 to 5: the stars of the game picked
on keyDown pKey
   if the number of chars of pKey is 1 and pKey is among the chars of "012345" and sSel is not empty then
      CG.SetRating sSel, pKey
      CG.Refresh
      exit keyDown
   end if
   pass keyDown
end keyDown

on returnKey
   CG.PlaySelected
end returnKey

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

-- the command that starts a copy of the program on one game (Windows' start returns at once,
-- so this list is free to answer the copy's relaunch message: the Library learnt this 16 Nov)
function CG.PlayCommand pExe, pFile, pPlatform
   if pPlatform is "Win32" then
      replace "/" with "\" in pExe
      replace "/" with "\" in pFile
      return "start " & quote & quote & space & quote & pExe & quote & " -game " & quote & pFile & quote
   end if
   return quote & pExe & quote & " -game " & quote & pFile & quote & " &"
end CG.PlayCommand

function CG.LaunchCopy pFile
   local tExe, tErr, tCmd, tOut
   put the effective filename of me into tExe
   if tExe is empty then return "this program's own file is unknown"
   replace "\" with "/" in pFile
   put CG.PlayCommand(tExe, pFile, the platform) into tCmd
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

-------------------------------------------------------------------- make a new one

-- a Python 3 to run tools/make_game.py with (it needs nothing but Python itself):
--   Player/python/python.exe   one shipped with the app (the installer's plan)
--   Comfy Desktop's own        %LOCALAPPDATA%\Comfy-Desktop\ComfyUI-Installs\*\standalone-env\python.exe
--   py -3                      the Windows Python launcher
--   python3                    off Windows
-- empty when there is none
function CG.Python
   local tTry, tBase, tDir, tOld, tOut
   if sPython is not empty then return sPython
   if the platform is not "Win32" then
      put "python3" into sPython
      return sPython
   end if
   put CG.Root() & "/Player/python/python.exe" into tTry
   if there is a file tTry then
      put quote & CG.WinPath(tTry) & quote into sPython
      return sPython
   end if
   put $LOCALAPPDATA into tBase
   replace "\" with "/" in tBase
   put tBase & "/Comfy-Desktop/ComfyUI-Installs" into tBase
   if there is a folder tBase then
      put the defaultFolder into tOld
      set the defaultFolder to tBase
      repeat for each line tDir in the folders
         if tDir is ".." or tDir is "." then next repeat
         put tBase & "/" & tDir & "/standalone-env/python.exe" into tTry
         if there is a file tTry then
            put quote & CG.WinPath(tTry) & quote into sPython
            exit repeat
         end if
      end repeat
      set the defaultFolder to tOld
      if sPython is not empty then return sPython
   end if
   set the hideConsoleWindows to true
   put shell("where py") into tOut
   if the result is 0 or the result is empty then
      if line 1 of tOut ends with "py.exe" then
         put "py -3" into sPython
         return sPython
      end if
   end if
   return empty
end CG.Python

-- the command line that makes one new game of a genre into pFolder
function CG.MakeCommand pGenre, pFolder
   local tPy, tCmd
   put CG.Python() into tPy
   if tPy is empty then return empty
   put tPy && "-I" && quote & CG.WinPath(CG.Root() & "/tools/make_game.py") & quote && quote & pGenre & quote \
         && "--out" && quote & CG.WinPath(pFolder) & quote into tCmd
   -- cmd.exe /C drops the first and last quote of a line holding more than two: wrap it once more
   if the platform is "Win32" then put quote & tCmd & quote into tCmd
   return tCmd
end CG.MakeCommand

-- make one new game (pGenre empty or All games: a genre picked at random); it is picked in the
-- list at once. Returns empty, or why not.
function CG.MakeNew pGenre
   local tCmd, tOut, tLine, tFile, tName
   if pGenre is empty or pGenre is "All games" then put any line of sGenreList into pGenre
   if pGenre is empty then return "no genres.tsv in" && CG.WinPath(CG.Root())
   if there is not a file (CG.Root() & "/tools/make_game.py") then return "the maker (tools/make_game.py) is missing"
   put CG.MakeCommand(pGenre, CG.BuildFolder()) into tCmd
   if tCmd is empty then return "Make a new one needs Python 3 (ComfyUI's own Python will do): none was found"
   CG.Log "make:" && tCmd
   set the hideConsoleWindows to true
   put shell(tCmd) into tOut
   replace numToChar(13) with empty in tOut
   repeat for each line tLine in tOut
      if tLine begins with "OK " then put char 4 to -1 of tLine into tFile
   end repeat
   if tFile is empty then
      CG.Log "make failed:" && tOut
      repeat for each line tLine in tOut
         if tLine begins with "ERROR" then return char 7 to -1 of tLine
      end repeat
      return "the maker said:" && line -1 of tOut
   end if
   replace "\" with "/" in tFile
   set the itemDelimiter to "/"
   put item -1 of tFile into tName
   put char 17 to -16 of tName into tName
   put tName into sSel
   return empty
end CG.MakeNew

command CG.MakeClicked
   local tWhy, tGenre
   put sGenre into tGenre
   set the cursor to watch
   CG.Say "Making a new" && tGenre && "game..."
   put CG.MakeNew(tGenre) into tWhy
   if tWhy is not empty then
      CG.Say "Could not make one:" && tWhy
      exit CG.MakeClicked
   end if
   -- show it in the list, newest first, so it is in sight
   put "Newest" into sSort
   CG.Refresh
   CG.Say "New:" && sSel && " |  press PLAY, or rate it after a go"
end CG.MakeClicked

-------------------------------------------------------------------- Open in ComfyUI

function CG.Curl
   local tC
   if the platform is "Win32" then
      put $SystemRoot into tC
      if tC is empty then put "C:\Windows" into tC
      return quote & tC & "\System32\curl.exe" & quote
   end if
   return "curl"
end CG.Curl

-- the genre's starter workflow file (LIB_COMFY/workflows/<name>.json)
function CG.WorkflowFile pGenre
   if sGenreRows[pGenre]["workflow"] is empty then return empty
   return CG.Root() & "/workflows/" & sGenreRows[pGenre]["workflow"] & ".json"
end CG.WorkflowFile

-- the commands: is ComfyUI up, and put the workflow into its Workflows panel (its userdata
-- store: user/default/workflows/ComfyGames_<genre>.json)
function CG.ComfyCommand pWhat, pGenre
   local tCmd
   if pWhat is "ping" then
      put CG.Curl() && "-s -m 2" && kComfyURL & "/system_stats" into tCmd
   else
      put CG.Curl() && "-s -m 10 -X POST -H" && quote & "Content-Type: application/json" & quote \
            && "--data-binary" && quote & "@" & CG.WinPath(CG.WorkflowFile(pGenre)) & quote \
            && quote & kComfyURL & "/api/userdata/workflows%2FComfyGames_" & pGenre & ".json?overwrite=true" & quote into tCmd
   end if
   if the platform is "Win32" then put quote & tCmd & quote into tCmd
   return tCmd
end CG.ComfyCommand

function CG.ComfyRunning
   local tOut
   set the hideConsoleWindows to true
   put shell(CG.ComfyCommand("ping")) into tOut
   return (tOut contains "comfyui_version" or tOut contains "system")
end CG.ComfyRunning

command CG.ComfyClicked
   local tOut, tErr
   if sGenre is "All games" or CG.WorkflowFile(sGenre) is empty then
      CG.Say "Pick a genre first: each has its own starter workflow"
      exit CG.ComfyClicked
   end if
   if there is not a file CG.WorkflowFile(sGenre) then
      CG.Say "No starter workflow file:" && CG.WinPath(CG.WorkflowFile(sGenre))
      exit CG.ComfyClicked
   end if
   set the cursor to watch
   if not CG.ComfyRunning() then
      put "ComfyUI is not running." & return & return & \
            "Start ComfyUI (Comfy Desktop), then press Open in ComfyUI again." & return & \
            "You don't need it to play: Make a new" && sGenre && "makes one without ComfyUI." & return & return & \
            "The starter workflow is also a file you can drag into ComfyUI:" & return & \
            CG.WinPath(CG.WorkflowFile(sGenre)) into field "Details" of me
      CG.Say "ComfyUI is not running at" && kComfyURL
      exit CG.ComfyClicked
   end if
   put shell(CG.ComfyCommand("upload", sGenre)) into tOut
   CG.Log "comfy upload" && sGenre & ":" && tOut
   try
      launch url kComfyURL
   catch tErr
   end try
   put "In ComfyUI: open the Workflows panel (press W) and pick ComfyGames_" & sGenre & "." & return & return & \
         "Change the nodes, press Queue (Run): each run builds a new" && sGenre && "game." & return & \
         "Come back here and it is in the list (Newest)." into field "Details" of me
   CG.Say "Sent the" && sGenre && "starter workflow to ComfyUI"
end CG.ComfyClicked

-------------------------------------------------------------------- verify

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
      put tN && "games checked: all readable, and the engine is there." & return into tWhy
   else
      put tN && "games checked," && tBad && "problems:" & return & return & tOut into tWhy
   end if
   put return & "Make a new one runs:" && CG.Python() & return after tWhy
   if CG.Python() is empty then put "  (no Python 3 found: Make a new one can't work)" & return after tWhy
   put "New games go to:" && CG.WinPath(CG.BuildFolder()) & return after tWhy
   put "Stars are kept in:" && CG.WinPath(CG.RatingsFile()) after tWhy
   put tWhy into field "Details" of me
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
   CG.Audio tName, pFile
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

-- the hidden AUDIO stack (LIB_AUDIO), as LIB_DEV's GL.Audio: the game's sounds fill one per
-- tick, the engine's Sound.Play goes through it, and ... > Sounds... chooses them. A Comfy game
-- uses its own words, else its family's (ComfyPhoton.txt), else its remix source's (PhotonBall.txt).
-- No LIB_AUDIO (Player/Engine or the projects folder): the engine's own sound kit, as before.
command CG.Audio pName, pFile
   global bNoAudio
   local tLib, tErr
   if bNoAudio is true then exit CG.Audio
   put CG.EngineFile("lib_audio.livecodescript") into tLib
   if tLib is empty then exit CG.Audio
   try
      if not ("lib_audio" is among the lines of the stacksInUse) then start using stack tLib
      if not Audio.IsOpen() then
         Audio.Open
         -- installed: the kit beside the program goes into the player's Sounds folder once
         if there is a folder (CG.Root() & "/Player/Sounds") then Audio.Seed CG.Root() & "/Player/Sounds", CG.Root() & "/Player/Music"
      end if
      Audio.Refresh CG.GameFolders()   -- new builds since the last game get their cards
      Audio.Select pName, pFile
   catch tErr
      CG.Log "AUDIO did not start:" && line 1 of tErr
   end try
end CG.Audio

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
   put empty into sHead
end CG.TestRoot

-- a throwaway Data folder (its Games/ComfyGames is used); empty: the real one again
command CG.TestData pPath
   put pPath into sTestData
   put empty into sDataFolder
   put false into sRatingsRead
end CG.TestData

-- new games go here (empty: the usual place)
command CG.TestBuildFolder pPath
   put pPath into sTestBuild
end CG.TestBuildFolder

function CG.Count
   return the number of lines of sOrder
end CG.Count

function CG.Order
   return sOrder
end CG.Order

function CG.Field pName
   return field pName of me
end CG.Field

function CG.SelName
   return sSel
end CG.SelName

function CG.FileOf pName
   return sGames[pName]["file"]
end CG.FileOf

function CG.GameData pName, pKey
   return sGames[pName][pKey]
end CG.GameData

function CG.GenreRow pGenre, pKey
   return sGenreRows[pGenre][pKey]
end CG.GenreRow

function CG.SetView pGenre, pSort
   put pGenre into sGenre
   put pSort into sSort
   CG.Refresh
   return sOrder
end CG.SetView
